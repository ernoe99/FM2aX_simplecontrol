import math


class EM_heating_cycle:
    def __init__(self, Tdiff=10):
        """
        Initialisiert das EM_heating_cycle Objekt mit seinen internen Zuständen und Parametern.
        """
        self.P_hk_ist = 0.0  # Aktuelle thermische Leistung im Heizkreis
        self.Pump_signal = 0.0  # Aktuelles Pumpensignal
        self.Pump_signal_min = 20.0  # Minimales Pumpensignal
        self.Pump_signal_max = 100.0  # Maximales Pumpensignal
        self.Tdifference_to_ctk = Tdiff  # K unter Tsoll Start der Pumpe

        # NEUE PD-Regler-Parameter
        self.kp = 0.5  # Proportional-Gain
        self.kd = 0.1  # Derivative-Gain
        self.previous_error = None  # Speichert den Fehler aus dem vorherigen Zyklus

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
        # Überprüfung, ob die Pumpe laufen sollte
        if Tvl_tk > Tvl_soll - self.Tdifference_to_ctk and self.Pump_signal == 0:
            self.Pump_signal = self.Pump_signal_min
        elif Tvl_tk > Tvl_soll + self.Tdifference_to_ctk:
            self.Pump_signal = self.Pump_signal_max

        cp_hk = 4182.0  # Spezifische Wärmekapazität von Wasser (J/kg*K)
        rho_hk = 997.0  # Dichte von Wasser (kg/m³)
        self.P_hk_ist = Vol_hk * cp_hk * rho_hk * (Tvl_hk - Trl_hk) * 1.0E-6  # in kW

        # PD-Regler Logik
        error = Tvl_soll - Tvl_hk

        if self.previous_error is None:
            self.previous_error = error

        derivative = error - self.previous_error

        # PD-Regelungs-Ausgabe
        pd_output = self.kp * error + self.kd * derivative

        self.Pump_signal -= pd_output
        self.Pump_signal = max(self.Pump_signal_min, min(self.Pump_signal, self.Pump_signal_max))  # Begrenzung

        self.previous_error = error

        return self.Pump_signal, self.P_hk_ist


if __name__ == "__main__":
    hk1 = EM_heating_cycle()

    # Beispiel-Testfälle
    print("Initialisierung:", hk1.Pump_signal)

    # Simuliere einen starken Abfall der Vorlauftemperatur
    print("Fall 1: Tvl_hk zu niedrig")
    x = hk1.run(Tvl_soll=45, Tvl_tk=46, Vol_hk=3.2, Trl_tk=28, Tvl_hk=40.0, Trl_hk=28)
    print("Pumpensignal:", x[0])

    print("Fall 2: Tvl_hk nähert sich dem Sollwert")
    x = hk1.run(Tvl_soll=45, Tvl_tk=46, Vol_hk=3.2, Trl_tk=28, Tvl_hk=43.0, Trl_hk=28)
    print("Pumpensignal:", x[0])

    print("Fall 3: Tvl_hk am Sollwert")
    x = hk1.run(Tvl_soll=45, Tvl_tk=46, Vol_hk=3.2, Trl_tk=28, Tvl_hk=45.0, Trl_hk=28)
    print("Pumpensignal:", x[0])