class EM_common_tk:
    def __init__(self, plus_dT_tk):
        """
        Initializes the EM_common_tk object with its internal state and parameters.
        """
        self.plus_dT_tk = plus_dT_tk   # Erhöhung der Trennkreis Temperatur
        self.P_tk_ist = 0.0  # Aktuelle thermische Leistung
        self.Tvl_tk_soll = 0.0  # Sollwert der Trennkreis-Vorlauftemperatur
        self.Pump_signal_tk = 0.0  # Steuersignal für die Pumpe
        self.S = 0.0  # Regelabweichung
        self.Pump_signal_req_change = 0.0  # Rückgabewert des Pumpensignals
        self.K_pump_tk = 50.0  # Proportionalitätskonstante für P_Regler_Vol_tk
        self.K_water_vent_tk = 100.0  # Proportionalitätskonstante für P_Regler_Ventil
        self.Pump_signal_min = 20.0  # Minimales Pumpensignal
        self.Pump_signal_max = 100.0  # Maximales Pumpensignal
        self.vent_open = 100.0  # Stellung des Ventils

        self.cp_tk = 3600.0  # Spezifische Wärmekapazität von Wasser/Gylkol (J/kg*K)
        self.rho_tk = 997.0  # Dichte von Wasser/Gylkol (kg/m³)

    def start_up(self):
        self.Pump_signal_tk = self.Pump_signal_min

    def stop(self):
        self.Pump_signal_tk = 0.0

    def run(self, Tvl_soll, Tvl_tk, Trl_tk, Tvl_hk, Trl_hk,  Vol_tk):
        """
        Executes the control logic based on the provided input signals.

        :param Tvl_soll: Target supply temperature
        :param Tvl_tk: Separator circuit supply temperature measured
        :param Trl_hk: Heating circuit return temperature measured
        :param Tvl_hk: Heating circuit supply temperature measured
        :param Vol_tk: Separator circuit flow measured
        :param Trl_tk: Separator circuit return temperature measured
        """

        self.cp_tk = 3600.0  # Spezifische Wärmekapazität von Wasser/Gylkol (J/kg*K)
        self.rho_tk = 997.0  # Dichte von Wasser/Gylkol (kg/m³)
        self.P_tk_ist = Vol_tk * self.cp_tk * self.rho_tk / 1000.0 * (Tvl_tk - Trl_tk) / 1000.0  # in kW

        # P_Regler_Vol_tk
        self.Tvl_tk_soll = Tvl_soll + self.plus_dT_tk   # Soll Vorlauf Trennkreis bei Tvl_soll hk
        self.S = self.K_pump_tk * (self.Tvl_tk_soll - Tvl_tk) / (Tvl_tk - Trl_tk)
        self.Pump_signal_tk = min(max(self.Pump_signal_min, self.Pump_signal_tk - self.S), self.Pump_signal_max)
        self.Pump_signal_req_change = self.S

        # P_Regler_Ventil
        if self.Pump_signal_tk == self.Pump_signal_min:
            self.S = self.K_water_vent_tk * (self.Tvl_tk_soll - Tvl_tk) / (Tvl_tk - Trl_tk)
            self.vent_open = max(0.0, min(self.vent_open - self.S, 100.0))
            eq_change = True
        else:
            eq_change = False

        self.Pump_signal_req_change = self.Pump_signal_tk

        return self.Pump_signal_req_change, eq_change, self.vent_open, self.P_tk_ist


if __name__ == "__main__":

    tk1 = EM_common_tk(plus_dT_tk=1.0)

    tk1.start_up()

    x = tk1.run(45, 48, 3.2, 28, 3.2, 1.0)
    print(x)

    x = tk1.run(45, 45.5, 3.2, 28, 48.0, 1.05)
    print(x)
    x = tk1.run(45, 46, 3.2, 28, 44.0, 1.0)
    print(x)

    x = tk1.run(45, 43, 3.2, 28, 41.0, 1.0)
    print(x)
    x = tk1.run(45, 41, 3.2, 28, 41.0, 1.0)
    print(x)

    tk1.stop()

