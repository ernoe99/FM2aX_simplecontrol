class EM_heating_cycle:
    def __init__(self, Tdiff=10):
        """
        Initialisiert das EM_heating_cycle Objekt mit seinen internen Zuständen und Parametern.
        """
        self.P_hk_ist = 0.0  # Aktuelle thermische Leistung im Heizkreis
        self.S = 0.0  # Regelabweichung
        self.Pump_signal_req_change = 0.0  # Angefordertes Pumpensignal
        self.K_pump_hk = 50.0  # Proportionalitätskonstante für den P-Regler
        self.Pump_signal = 0.0  # Aktuelles Pumpensignal
        self.Pump_signal_min = 20.0  # Minimales Pumpensignal
        self.Pump_signal_max = 100.0  # Maximales Pumpensignal
        self.Tdifference_to_ctk = Tdiff  # K unter Tsoll Start der Pumpe

    def run(self, Tvl_soll, Tvl_tk, Vol_hk, Trl_tk, Tvl_hk, Trl_hk):
        """
        Führt die Regellogik basierend auf den bereitgestellten Eingangssignalen aus.

        :param Tvl_soll: Sollwert der Vorlauftemperatur
        :param Tvl_tk: Vorlauftemperatur Trennkreis
        :param Vol_hk: Volumenstrom Heizkreis
        :param Trl_tk: Rücklauftemperatur Trennkreis
        :param Tvl_hk: Vorlauftemperatur Heizkreis
        :param Trl_hk: Rücklauftemperatur Heizkreis
        """
        # Check if pump should run

        if Tvl_tk > Tvl_soll - self.Tdifference_to_ctk and self.Pump_signal == 0:
            self.Pump_signal = self.Pump_signal_min
        elif Tvl_tk > Tvl_soll + self.Tdifference_to_ctk:
            self.Pump_signal = self.Pump_signal_max

        cp_hk = 4182.0  # Spezifische Wärmekapazität von Wasser (J/kg*K)
        rho_hk = 997.0  # Dichte von Wasser (kg/m³)
        self.P_hk_ist = Vol_hk * cp_hk * rho_hk * (Tvl_hk - Trl_hk) * 1.0E-6  # in kW

        # P Regler Vol_hk
        self.S = self.K_pump_hk * (Tvl_soll - Tvl_hk) / (Tvl_hk - Trl_hk)

        print(self.S)

        self.Pump_signal = max(self.Pump_signal_min, self.Pump_signal - self.S)
        # self.Pump_signal_req_change = self.Pump_signal

        return self.Pump_signal, self.P_hk_ist


if __name__ == "__main__":
    hk1 = EM_heating_cycle()

    x = hk1.run(45, 46, 3.2, 28, 42.0, 28)
    print(x)

    x = hk1.run(45, 46, 3.2, 28, 48.0, 28)
    print(x)
    x = hk1.run(45, 46, 3.2, 28, 44.0, 28)
    print(x)

    x = hk1.run(45, 46, 3.2, 28, 45.0, 28)
    print(x)

