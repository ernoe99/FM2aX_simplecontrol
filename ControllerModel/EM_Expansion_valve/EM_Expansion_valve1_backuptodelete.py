class EM_expansion_valve:
    def __init__(self, mode="user"):
        """
        Initialisiert das EM_expansion_valve Objekt mit Standardparametern für die Regelung.

        :param mode: Betriebsmodus ('user' oder 'wp').
        """
        if mode == "user":
            self.mode = 0
        else:
            self.mode = 1

        self.pump_down_active = False

        # Parameter für die Überhitzungsregelung (Discharge Superheat)
        self.Superheat_soll = 10.0
        self.DTC_Superheat = 20.0
        self.DTC_Superheat_low = 8.0
        self.DTC_Superheat_critical_low = 3.0
        self.DTC_Superheat_high = 40.0
        self.DTC_wait_time = 0.0
        self.DTC_wait_time_high_DTC = 300.0
        self.DTC_wait_time_low_DTC = 60.0
        self.DTC_Superheat_critical_low_step = 5.0
        self.waiting = False
        self.exv_change = 0.0

        # EXV-Einstellungen
        self.exv_opening = 50.0

    def start_up(self):
        """Setzt die EXV-Öffnung auf den Startwert und deaktiviert den Pump-Down-Modus."""
        self.exv_opening = 50.0
        self.pump_down_active = False
        return self.exv_opening, self.pump_down_active

    def pump_down(self):
        """Aktiviert den Pump-Down-Modus und schließt das Ventil vollständig."""
        self.exv_opening = 0.0
        self.pump_down_active = True
        return self.exv_opening, self.pump_down_active

    def set_exv_absolut(self, mode, tdc_soll, tdc_ist, exv_open_soll=50.0):
        """
        Regelt das elektronische Expansionsventil (EXV) basierend auf der
        Verdichter-Austrittstemperatur (TDC) oder einem direkten Sollwert.

        :param mode: 0 für direkte Sollwertsetzung, 1 für TDC-basierte Regelung.
        :param tdc_soll: Sollwert der Verdichter-Austrittstemperatur.
        :param tdc_ist: Istwert der Verdichter-Austrittstemperatur.
        :param exv_open_soll: Sollwert für die Ventilöffnung (nur bei mode=0 relevant).
        :return: Der neue Wert für die EXV-Öffnung.
        """
        # Modus 0: Direkte Sollwertübernahme, keine Wartezeit
        if mode == 0:
            self.exv_opening = exv_open_soll
            self.waiting = False
            self.DTC_wait_time = 0.0
            return self.exv_opening

        # Sofortige Sicherheitsprüfung: Kritisch hohe Verdichter-Austrittstemperatur
        if tdc_ist > 130.0:
            print("Compressor discharge Temperature above 130°C - taking actions")
            self.exv_opening = min(self.exv_opening + 5, 100)
            self.waiting = False
            self.DTC_wait_time = 0.0
            return self.exv_opening

        dtc = tdc_ist - tdc_soll + self.Superheat_soll

        # Sofortige Sicherheitsprüfung: Kritisch niedrige Überhitzung
        if dtc < self.DTC_Superheat_critical_low:
            print("Critical low superheat detected - closing valve")
            self.exv_opening = max(0.0, self.exv_opening - self.DTC_Superheat_critical_low_step)
            self.waiting = False
            self.DTC_wait_time = 0.0
            return self.exv_opening

        # Wartezeit abfragen und herunterzählen
        if self.waiting:
            self.DTC_wait_time -= 1
            if self.DTC_wait_time <= 0:
                self.waiting = False
            # Im Wartezustand keine weitere Regelung durchführen
            return self.exv_opening

        # TDC-basierte Regelung (mode != 0)
        if self.DTC_Superheat <= dtc < self.DTC_Superheat_high:
            # Normaler Bereich: keine Änderung und keine Wartezeit
            pass
        elif dtc >= self.DTC_Superheat_high:
            print("High superheat detected - opening valve and starting wait period")
            self.exv_opening = min(self.exv_opening + 1, 100)
            self.DTC_wait_time = self.DTC_wait_time_high_DTC
            self.waiting = True
        elif dtc < self.DTC_Superheat_low:
            print("Low superheat detected - closing valve and starting wait period")
            self.exv_opening = max(0.0, self.exv_opening - 1)
            self.DTC_wait_time = self.DTC_wait_time_low_DTC
            self.waiting = True

        return self.exv_opening


if __name__ == "__main__":
    exv1 = EM_expansion_valve(mode="hp")

    print("--- Test Start-Up ---")
    exv1.start_up()
    print(f"Start-up Opening: {exv1.exv_opening}")

    print("\n--- Test Mode 0 (Direct Control) ---")
    x = exv1.set_exv_absolut(mode=0, tdc_soll=88, tdc_ist=55, exv_open_soll=75)
    print(f"Direct set opening: {x}")

    print("\n--- Test Mode 1 (TDC-based Control) ---")

    # Zustand: Normaler Bereich (keine Änderung)
    print("Testfall 1: Normalbereich (keine Änderung)")
    initial_opening = exv1.exv_opening
    x = exv1.set_exv_absolut(mode=1, tdc_soll=88, tdc_ist=100)
    print(f"Initial: {initial_opening}, Current: {x}, expected: no change")

    # Zustand: Überhitzung zu hoch (Ventil öffnen, Wartezeit starten)
    print("\nTestfall 2: Überhitzung zu hoch (Ventil öffnen)")
    initial_opening = exv1.exv_opening
    x = exv1.set_exv_absolut(mode=1, tdc_soll=88, tdc_ist=130)
    print(f"Initial: {initial_opening}, Current: {x}, expected: +1, waiting: {exv1.waiting}")

    print("\nTestfall 3: Wartezeit (Test mit TDC im Normalbereich)")
    # Simuliere mehrere Zyklen in der Wartezeit
    for i in range(5):
        x = exv1.set_exv_absolut(mode=1, tdc_soll=88, tdc_ist=105)  # "Normaler" Wert
        print(f"Wait cycle {i + 1}: Opening: {x}, wait_time: {exv1.DTC_wait_time}")

    # Zustand: Kritisch niedrige Überhitzung während der Wartezeit (Bedingung überschreibt Wartezeit)
    print("\nTestfall 4: Kritisch niedrige Überhitzung während Wartezeit")
    x = exv1.set_exv_absolut(mode=1, tdc_soll=88, tdc_ist=89)  # dtc < 3
    print(f"Opening: {x}, wait_time: {exv1.DTC_wait_time}, waiting: {exv1.waiting}")

    # Zustand: Überhitzung zu niedrig (Ventil schließen, Wartezeit starten)
    print("\nTestfall 5: Überhitzung zu niedrig (Ventil schließen)")
    x = exv1.set_exv_absolut(mode=1, tdc_soll=88, tdc_ist=92)
    print(f"Opening: {x}, wait_time: {exv1.DTC_wait_time}, waiting: {exv1.waiting}")

    print("\n--- Test Pump-Down ---")
    x = exv1.pump_down()
    print(f"Pump-down active: {x[1]}, Opening: {x[0]}")
