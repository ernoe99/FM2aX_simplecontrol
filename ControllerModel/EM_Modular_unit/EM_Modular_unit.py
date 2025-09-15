# --- Import der benötigten Klassen ---
from EM_Dynamics import EM_Dynamics
from EM_common_tk import EM_common_tk
from EM_heating_cycle import EM_heating_cycle
from EM_Cascade import EM_Cascade


# --- Platzhalter für HP- und Kompressor-Logik (unverändert) ---
# In einer realen Anwendung würden Sie hier Ihre tatsächlichen Klassen importieren
class MockCompressor:
    def predict(self, T_ambient, humidity):
        return [
            (50, 10.0), (60, 12.5), (70, 15.0), (80, 17.5),
            (90, 20.0), (100, 22.0), (110, 24.5), (120, 27.0)
        ]


class MockHP:
    """Simuliert eine einzelne HP-Einheit mit Laufzeit und Kompressor-Instanz."""

    def __init__(self, hp_type, runtime=0.0):
        self.hp_type = hp_type
        self.compressor = MockCompressor()
        self.runtime_hp = runtime
        self.is_running = False
        self.current_speed = 0.0

    def get_power_estimates(self, T_ambient, humidity):
        return self.compressor.predict(T_ambient, humidity)

    def set_speed(self, speed):
        self.current_speed = speed
        print(f"HP vom Typ '{self.hp_type}' auf Drehzahl {self.current_speed} eingestellt.")


class Hydraulics_SIM:
    def __init__(self):
        print("Komponente: Hydraulik-Simulation initialisiert.")

    def run(self, common_tk, heating_cycle):
        pass


# --- Aktualisierte modular_unit Klasse ---
class modular_unit:
    def __init__(self, hp_types: list):
        """
        Initialisiert die modulare Einheit und alle ihre Komponenten.

        :param hp_types: Eine Liste der HP-Typen in der Kaskade.
        """
        print("--- Modulare Einheit wird initialisiert ---")

        # 1. Die Kaskadensteuerung initialisieren
        self.cascade = EM_Cascade(hp_types)

        # 2. Eine Liste von HP-Instanzen erstellen
        self.hp_units = [MockHP(hp_type) for hp_type in hp_types]

        # 3. Andere Systemkomponenten initialisieren
        self.dynamics = EM_Dynamics(Ktime=5.0)
        self.common_tk = EM_common_tk(plus_dT_tk=1.0)
        self.internal_tk = EM_heating_cycle(Tdiff=10)
        self.hydraulics_sim = Hydraulics_SIM()

        print("--- Alle Komponenten der modularen Einheit initialisiert ---")

    def run_full_cycle(self, ctrl_data, is_data, sens2_data, current_time):
        """
        Führt einen vollständigen Regelzyklus für das modulare System aus,
        indem die Cascade die Steuerung übernimmt.

        :param ctrl_data: Steuerungsdaten (P_soll, Tvl_soll, etc.).
        :param is_data: Umfeldsensordaten.
        :param sens2_data: Hydrauliksensoren.
        :param current_time: Aktueller Zeitstempel für Laufzeitberechnungen.
        :return: Stellgrößen für HPs, Pumpen und Ventile.
        """
        print("\n--- Regelzyklus der modularen Einheit gestartet ---")

        # 1. Dynamische Leistungsberechnung
        dynamic_output = self.dynamics.run(
            T_rl_ist=sens2_data["Trl_hk"],
            T_ambient=is_data["Tair"],
            humidity=is_data["Rfair"],
            P_soll=ctrl_data["P_soll"]
        )

        # 2. Auswahl der HPs durch die Cascade-Logik
        # Die gewünschte Leistung ist der dynamische Ausgang der Dynamik-Klasse
        desired_power = dynamic_output.get("P_app_dynamic")

        selected_hps_and_speeds, _, _ = self.cascade.run(
            desired_power=desired_power,
            is_data=is_data,
            current_time=current_time
        )

        # 3. Anwenden der Geschwindigkeitsbefehle auf die ausgewählten HPs
        hp_control_values = {}
        for hp_index, speed in selected_hps_and_speeds:
            self.hp_units[hp_index].set_speed(speed)
            hp_control_values[f"HP_{hp_index}"] = speed

        # 4. Regelung der Pumpen und Ventile (Trenn- und Heizkreis)
        pump_signal_tk, _, vent_open, _ = self.common_tk.run(
            Tvl_soll=ctrl_data["Tvl_soll"],
            Tvl_tk=sens2_data["Tvl_tk"],
            Trl_tk=sens2_data["Trl_tk"],
            Tvl_hk=sens2_data["Tvl_hk"],
            Trl_hk=sens2_data["Trl_hk"],
            Vol_tk=sens2_data["Vol_tk"]
        )

        pump_signal_hk, _ = self.internal_tk.run(
            Tvl_soll=ctrl_data["Tvl_soll"],
            Tvl_tk=sens2_data["Tvl_tk"],
            Vol_hk=sens2_data["Vol_hk"],
            Trl_tk=sens2_data["Trl_tk"],
            Tvl_hk=sens2_data["Tvl_hk"],
            Trl_hk=sens2_data["Trl_hk"]
        )

        # 5. Datenfluss zur Hydraulik-Simulation
        self.hydraulics_sim.run(self.common_tk, self.internal_tk)

        print("--- Regelzyklus der modularen Einheit beendet ---")

        return hp_control_values, pump_signal_tk, vent_open, pump_signal_hk


if __name__ == "__main__":
    # Beispiel-Daten für einen Simulationszyklus
    ctrl = {"P_soll": 22.0, "Tvl_soll": 45.0, "dT_soll": 1.5}
    is_sens = {"Tair": 10.0, "Rfair": 60.0}
    sens2 = {"Vol_tk": 1.0, "Tvl_tk": 46.5, "Trl_tk": 30.0, "Tvl_hk": 45.0, "Trl_hk": 35.0, "Vol_hk": 3.2}

    # Initialisierung der modularen Einheit mit 2 HPs
    my_modular_unit = modular_unit(hp_types=["VZN175", "VZN175"])

    # Ausführen des Simulationszyklus
    hp_control, pump_tk_sig, vent_tk_open, pump_hk_sig = my_modular_unit.run_full_cycle(
        ctrl, is_sens, sens2, current_time=10
    )

    print("\n--- Ergebnisse des Zyklus ---")
    print(f"HP-Steuerwerte: {hp_control}")
    print(f"Trennkreis-Pumpensignal: {pump_tk_sig}")
    print(f"Trennkreis-Ventilstellung: {vent_tk_open}")
    print(f"Heizkreis-Pumpensignal: {pump_hk_sig}")