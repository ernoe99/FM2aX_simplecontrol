import numpy as np
import collections


class Hydraulik_System:
    def __init__(self, D_mm, P_kW, cp_tk_kj_kgK, q_dot_out_W_m, n_x, L_total_m=1000):
        """
        Initialisiert ein Hydraulik-System mit den gegebenen Parametern.

        Args:
            D_mm (float): Innendurchmesser des Rohres in Millimetern (mm).
            P_kW (float): Leistung in Kilowatt (kW).
            cp_tk_kj_kgK (float): Spezifische Wärmekapazität des Trennkreises in kJ/(kg·K).
            q_dot_out_W_m (float): Abwärme des Systems in W/m.
            n_x (int): Anzahl der Segmente für die Berechnung.
            L_total_m (float, optional): Gesamtlänge des Rohres in Metern. Standard ist 1000 m.
        """
        self.D = D_mm / 1000.0
        self.P = P_kW * 1000.0
        self.cp_tk = cp_tk_kj_kgK * 1000.0
        self.q_dot_out = q_dot_out_W_m
        self.n_x = n_x
        self.L_total = L_total_m
        self.temperatures = np.array([])

        self.rho = 998.2
        self.cp_water = 4182.0

        self.A = np.pi * (self.D / 2) ** 2
        self.V_segment = (self.A * self.L_total) / self.n_x
        self.V_total = self.A * self.L_total
        print("Total Water Volume: ", self.V_total)

        self.T_rl_history = collections.deque()
        self.smoothing_seconds = 10.0

    def berechne_zeitschritt(self, T_vl, T_rl_start, dt_step, P_WP_kW = 0, Volumenstrom_m3s=None, Qdot_Heizkreis_W=0):
        """
        Berechnet einen instationären Zeitschritt für die Hydraulik mit internen
        Sub-Schritten und einer Wärmesenke.

        Args:
            T_vl (float): Temperatur Eintritt in Celsius.
            T_rl_start (float): Temperatur Austritt (Startwert) in Celsius.
            dt_step (float): Gesamter Zeitschritt in Sekunden (z.B. 1.0).
            P_WP_kW (float): Aktuelle WP Heizleistung in kW - wenn 0, dann self.P (Achtung in W)
            Volumenstrom_m3s (float, optional): Volumenstrom in m³/s. Standard ist None.
            Qdot_Heizkreis_W (float, optional): Abgeführte Leistung in Watt. Standard ist 0.
        """
        if self.temperatures.size == 0:  # Initialisierung
            self.temperatures = np.full(self.n_x, T_rl_start)
            self.T_rl_smoothed = T_rl_start

        # Anzahl der internen Sub-Schritte
        num_sub_steps = 10
        sub_dt = dt_step / num_sub_steps

        # Index der Wärmesenke in der Mitte des Rohrs
        heat_sink_index = self.n_x // 2

        # Modus für WP Leistung
        if P_WP_kW != 0:
            self.P = P_WP_kW * 1000.0     # Leistung der WP aus dem Aufruf

        # Schleife für die internen Sub-Schritte
        for _ in range(num_sub_steps):

            # Berechnung des Volumenstroms, falls nicht übergeben
            if Volumenstrom_m3s is None or Volumenstrom_m3s <= 0:
                delta_T_calc = T_vl - self.temperatures[0]
                if delta_T_calc == 0:
                    Q = 0
                else:
                    Q = self.P / (self.rho * self.cp_water * delta_T_calc)
            else:  # Berechnung von T_vl auf Basis von self.P
                Q = Volumenstrom_m3s
                T_vl = self.P / (self.rho * self.cp_water * Q) + self.T_rl_smoothed  #  Achtung Tvl shadowed

            new_temperatures = np.zeros(self.n_x)

            # Berechnung des instationären Zustands für jedes Segment
            for i in range(self.n_x):
                T_in = T_vl if i == 0 else self.temperatures[i - 1]

                # Wärmesenke nur am definierten Segment berücksichtigen
                q_dot_sink = Qdot_Heizkreis_W if i == heat_sink_index else 0

                if Q > 0:
                    mass_flow = Q * self.rho
                    delta_Q_segment = (T_in - self.temperatures[i]) * (mass_flow * self.cp_water) - self.q_dot_out * (
                                self.L_total / self.n_x) - q_dot_sink
                    T_new = self.temperatures[i] + (delta_Q_segment * sub_dt) / (self.rho * self.V_segment * self.cp_tk)
                else:
                    T_new = self.temperatures[i] - (
                                self.q_dot_out * (self.L_total / self.n_x) + q_dot_sink) * sub_dt / (
                                        self.rho * self.V_segment * self.cp_tk)

                new_temperatures[i] = T_new

            self.temperatures = new_temperatures

        T_rl_aktuell = self.temperatures[-1]

        self.T_rl_history.append(T_rl_aktuell)
        max_history_size = int(self.smoothing_seconds / dt_step)
        while len(self.T_rl_history) > max_history_size:
            self.T_rl_history.popleft()

        self.T_rl_smoothed = np.mean(list(self.T_rl_history))

        return self.T_rl_smoothed, self.temperatures


# --- Beispielnutzung des überarbeiteten Codes ---
if __name__ == "__main__":
    D_mm = 125
    P_kW = 50
    cp_tk_kj_kgK = 4.18
    q_dot_out_W_m = 0.5
    n_x = 100
    L_total_m = 60

    mein_system = Hydraulik_System(D_mm, P_kW, cp_tk_kj_kgK, q_dot_out_W_m, n_x, L_total_m)

    T_vl = 60.0
    T_rl = 40.0
    dt_step = 1.0
    Qdot_Heizkreis = 10000 # 5000  # 5 kW Wärmeleistung wird entnommen
    Volumenstrom = 0.001  # 0.5 L/s

    print(f"Start-Austrittstemperatur: {T_rl:.2f}°C")

    for i in range(1000):
        # Übergabe des Volumenstroms und der Heizkreisleistung
        T_rl_neu, temperaturen = mein_system.berechne_zeitschritt(T_vl, T_rl, dt_step, P_WP_kW=P_kW,  Volumenstrom_m3s=Volumenstrom,
                                                                  Qdot_Heizkreis_W=Qdot_Heizkreis)
        print(f"Schritt {i + 1}: Aktuelle geglättete Austrittstemperatur: {T_rl_neu:.2f}°C")
        T_rl = T_rl_neu  # Update T_rl for the next step

    print("\nEndgültige Temperaturverteilung in den Segmenten:")
    print(np.round(temperaturen, 2))