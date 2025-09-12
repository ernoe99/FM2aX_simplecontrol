class EM_expansion_valve:
    def __init__(self, mode="user"):
        """
        Initialisiert das EM_expansion_valve Objekt mit Standardparametern für die Regelung.

        :param mode: Betriebsmodus ('user' oder 'wp').
        """

        if mode == "user":
            self.mode = 0 # "user"  EXV settings will be directly apllied
        else:
            self.mode = 1
        self.pump_down_active = False

        # Parameter für die Überhitzungsregelung (Discharge Superheat)
        self.Superheat_soll = 10.0  # 10 Grad, weil die Superheat bei Danfoss 10 Grad ist
        self.DTC_Superheat = 20.0  # Ziel-Überhitzung (Verdichter-Austritt)
        self.DTC_Superheat_low = 8.0  # Untere Grenze für normale Überhitzung
        self.DTC_Superheat_critical_low = 3.0  # Kritische Schwelle für starke Reaktion
        self.DTC_Superheat_high = 40.0  # Obere Grenze für starke Reaktion
        self.DTC_wait_time = 0.0  # Wartezeit vor der nächsten Anpassung
        self.DTC_wait_time_high_DTC = 300.0  # Wartezeit bei hoher Überhitzung
        self.DTC_wait_time_low_DTC = 60.0  # Wartezeit bei niedriger Überhitzung
        self.DTC_Superheat_critical_low_step = 5.0  # Schrittgröße zum Schließen des Ventils bei kritischer Überhitzung
        self.wait_high_DTC = False
        self.wait_low_DTC = False

        # EXV-Einstellungen
        self.exv_opening = 50.0  # Startwert für die Ventilöffnung in Prozent

    def start_up(self):
        self.exv_opening = 50.0
        self.pump_down_active = False
        return self.exv_opening, self.pump_down_active

    def pump_down(self):
        self.exv_opening = 0.0  # pump_down activated
        self.pump_down_active = True
        return self.exv_opening, self.pump_down_active

    def set_exv_absolut(self, mode, tdc_soll, tdc_ist, exv_open_soll=50.0):
        """
        Regelt das elektronische Expansionsventil (EXV) basierend auf der
        Verdichter-Austrittstemperatur (TDC).

        :param mode: 0 für direkte Sollwertsetzung, 1 für TDC-basierte Regelung.
        :param tdc_soll: Sollwert der Verdichter-Austrittstemperatur.
        :param tdc_ist: Istwert der Verdichter-Austrittstemperatur.
        :param exv_open_soll: Sollwert für die Ventilöffnung (nur bei mode=0 relevant).
        :return: Der neue Wert für die EXV-Öffnung.
        """
        # Sicherheitsabfrage: Kritisch hohe Verdichter-Austrittstemperatur
        if tdc_ist > 130.0:
            print("Compressor discharge Temperature above 130°C - taking actions")
            pump_flow = 1.0
            compressor_speed_emergency_reduction = -10.0
            self.exv_opening = min(self.exv_opening + 5, 100)
            return self.exv_opening

        dtc = tdc_ist - tdc_soll + self.Superheat_soll  # Differenz zum Sollwert

        # Kritisch niedrige Überhitzung: Ventil schließen, um Flüssigkeitsschlag zu vermeiden
        if dtc < self.DTC_Superheat_critical_low:
            self.exv_opening = max(0.0, self.exv_opening - self.DTC_Superheat_critical_low_step)
            return self.exv_opening

        # Modus 0: Direkte Sollwertübernahme
        if mode == 0:
            self.exv_opening = exv_open_soll
        else:
            if self.DTC_wait_time > 0.0:
                self.DTC_wait_time += 1.0   # update der Wartezeit
            # Regelung basierend auf TDC und Überhitzungsbereichen
            if self.DTC_Superheat <= dtc < self.DTC_Superheat_high:
                # Normaler Bereich: keine Änderung
                pass
            elif dtc >= self.DTC_Superheat_high:
                if self.wait_high_DTC or self.DTC_wait_time >= self.DTC_wait_time_high_DTC:
                    self.wait_high_DTC = False
                    self.DTC_wait_time = 0.0
                # Überhitzung zu hoch: Ventil öffnen, Wartezeit setzen
                self.exv_opening = min(self.exv_opening + 1, 100)  # Annahme: Öffnung um 1%
                self.DTC_wait_time = self.DTC_wait_time_high_DTC
                self.wait_high_DTC = True
            elif dtc < self.DTC_Superheat_low:
                # Überhitzung zu niedrig: Ventil schließen, Wartezeit setzen
                self.exv_opening = max(0, self.exv_opening - 1)
                self.DTC_wait_time = self.DTC_wait_time_low_DTC

        return self.exv_opening


if __name__ == "__main__":

    exv1 = EM_expansion_valve(mode="hp")

    exv1.start_up()
    print("Opening: ", exv1.exv_opening)

    x = exv1.set_exv_absolut(0, 48.0, 3.2, 52)
    print(x)
    x = exv1.set_exv_absolut(0, 48.0, 52.0 , 52)
    print(x)

    x = exv1.set_exv_absolut(1, 88, 55, 52)
    print(x)
    x = exv1.set_exv_absolut(1, 88, 88, 52)
    print(x)
    x = exv1.set_exv_absolut(1, 88, 98, 52)
    print(x)
    x = exv1.set_exv_absolut(1, 88, 103.2, 52)
    print(x)

    x = exv1.pump_down()
    print(x)
