import math


class Internal_tk:
    def __init__(self, plus_dT_tk):
        """
        Initializes the EM_common_tk object with its internal state and parameters.
        """
        self.plus_dT_tk = plus_dT_tk  # Erhöhung der Trennkreis Temperatur
        self.P_tk_ist = 0.0  # Aktuelle thermische Leistung
        self.Tvl_tk_soll = 0.0  # Sollwert der Trennkreis-Vorlauftemperatur
        self.Pump_signal_tk = 0.0  # Steuersignal für die Pumpe
        self.vent_open = 100.0  # Stellung des Ventils

        self.Pump_signal_min = 20.0  # Minimales Pumpensignal
        self.Pump_signal_max = 100.0  # Maximales Pumpensignal

        self.cp_tk = 3600.0  # Spezifische Wärmekapazität von Wasser/Gylkol (J/kg*K)
        self.rho_tk = 997.0  # Dichte von Wasser/Gylkol (kg/m³)

        # NEUE PD-Regler-Parameter
        self.kp_pump = 2.0  # Proportional-Gain für die Pumpe
        self.kd_pump = 0.5  # Derivative-Gain für die Pumpe
        self.previous_error_pump = None

        self.kp_vent = 1.5  # Proportional-Gain für das Ventil
        self.kd_vent = 0.3  # Derivative-Gain für das Ventil
        self.previous_error_vent = None

    def start_up(self):
        self.Pump_signal_tk = self.Pump_signal_min
        self.previous_error_pump = None
        self.previous_error_vent = None

    def stop(self):
        self.Pump_signal_tk = 0.0
        self.previous_error_pump = None
        self.previous_error_vent = None

    def run(self, Tvl_soll, Tvl_tk, Trl_tk, Tvl_hk, Trl_hk, Vol_tk):
        """
        Executes the control logic based on the provided input signals.

        :param Tvl_soll: Target supply temperature
        :param Tvl_tk: Separator circuit supply temperature measured
        :param Trl_hk: Heating circuit return temperature measured
        :param Tvl_hk: Heating circuit supply temperature measured
        :param Vol_tk: Separator circuit flow measured
        :param Trl_tk: Separator circuit return temperature measured
        """
        # Berechnung der Leistung des Trennkreises
        self.P_tk_ist = Vol_tk * self.cp_tk * self.rho_tk / 1000.0 * (Tvl_tk - Trl_tk) / 1000.0  # in kW

        # Sollwert für den Trennkreis festlegen
        self.Tvl_tk_soll = Tvl_soll + self.plus_dT_tk

        # PD-Regler-Logik für die Pumpe
        pump_error = self.Tvl_tk_soll - Tvl_tk
        if self.previous_error_pump is None:
            self.previous_error_pump = pump_error
        pump_derivative = pump_error - self.previous_error_pump
        pd_output_pump = self.kp_pump * pump_error + self.kd_pump * pump_derivative

        # Anpassung des Pumpensignals
        self.Pump_signal_tk = self.Pump_signal_tk + pd_output_pump
        self.Pump_signal_tk = max(self.Pump_signal_min, min(self.Pump_signal_tk, self.Pump_signal_max))
        self.previous_error_pump = pump_error

        eq_change = False

        # PD-Regler-Logik für das Ventil, nur wenn die Pumpe am Minimum läuft
        if self.Pump_signal_tk <= self.Pump_signal_min:
            vent_error = self.Tvl_tk_soll - Tvl_tk
            if self.previous_error_vent is None:
                self.previous_error_vent = vent_error
            vent_derivative = vent_error - self.previous_error_vent
            pd_output_vent = self.kp_vent * vent_error + self.kd_vent * vent_derivative

            # Anpassung der Ventilöffnung
            self.vent_open = self.vent_open - pd_output_vent
            self.vent_open = max(0.0, min(self.vent_open, 100.0))
            self.previous_error_vent = vent_error
            eq_change = True

        return self.Pump_signal_tk, eq_change, self.vent_open, self.P_tk_ist


if __name__ == "__main__":
    tk1 = Internal_tk(plus_dT_tk=1.0)
    tk1.start_up()

    # Testfall 1: Tvl_tk ist zu niedrig, Pumpe soll hochfahren
    print("--- Testfall 1: Tvl_tk zu niedrig ---")
    pump_signal, eq_change, vent_open, p_ist = tk1.run(Tvl_soll=45, Tvl_tk=44, Trl_tk=28, Tvl_hk=43, Trl_hk=28,
                                                       Vol_tk=1.0)
    print(f"Pumpen-Signal: {pump_signal:.2f}, Ventil-Öffnung: {vent_open:.2f}")

    # Testfall 2: Tvl_tk nähert sich dem Sollwert
    print("--- Testfall 2: Tvl_tk nähert sich Sollwert ---")
    pump_signal, eq_change, vent_open, p_ist = tk1.run(Tvl_soll=45, Tvl_tk=45.5, Trl_tk=28, Tvl_hk=43, Trl_hk=28,
                                                       Vol_tk=1.0)
    print(f"Pumpen-Signal: {pump_signal:.2f}, Ventil-Öffnung: {vent_open:.2f}")

    # Testfall 3: Tvl_tk am Sollwert
    print("--- Testfall 3: Tvl_tk am Sollwert ---")
    pump_signal, eq_change, vent_open, p_ist = tk1.run(Tvl_soll=45, Tvl_tk=46, Trl_tk=28, Tvl_hk=44, Trl_hk=28,
                                                       Vol_tk=1.0)
    print(f"Pumpen-Signal: {pump_signal:.2f}, Ventil-Öffnung: {vent_open:.2f}")

    # Testfall 4: Tvl_tk am Sollwert mit minimaler Pumpenleistung, Ventil soll regeln
    print("--- Testfall 4: Ventil-Regelung aktiv ---")
    tk1.Pump_signal_tk = tk1.Pump_signal_min  # Simulation: Pumpe ist bereits am Minimum
    pump_signal, eq_change, vent_open, p_ist = tk1.run(Tvl_soll=45, Tvl_tk=45.8, Trl_tk=28, Tvl_hk=43, Trl_hk=28,
                                                       Vol_tk=1.0)
    print(f"Pumpen-Signal: {pump_signal:.2f}, Ventil-Öffnung: {vent_open:.2f}")

    tk1.stop()
    print("--- Stopp-Routine ausgeführt ---")