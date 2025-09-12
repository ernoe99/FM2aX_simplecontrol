import pandas as pd
from datetime import datetime
import time


# --- EM_expansion_valve Klasse mit Status-Logik und PD-Regler ---
class Expansion_valve:
    def __init__(self, mode="user"):
        """
        Initialisiert das EM_expansion_valve Objekt mit Standardparametern und Statusvariablen.

        :param mode: Betriebsmodus ('user', 'wp' oder 'pd').
        """
        if mode == "user":
            self.mode = 0  # Direkte Ventilsteuerung
        elif mode == "wp":
            self.mode = 1  # WP-spezifische TDC-Regelung
        elif mode == "pd":
            self.mode = 2  # PD-Regler
        else:
            self.mode = 1

        self.pump_down_active = False

        # Parameter für die Überhitzungsregelung (Discharge Superheat)
        self.Superheat_soll = 10.0
        self.DTC_Superheat = 10.0
        self.DTC_Superheat_low = 8.0
        self.DTC_Superheat_critical_low = 3.0
        self.DTC_Superheat_high = 40.0
        self.DTC_wait_time = 0.0
        self.DTC_wait_time_high_DTC = 300.0
        self.DTC_wait_time_low_DTC = 60.0
        self.DTC_Superheat_critical_low_step = 5.0
        self.waiting = False

        # NEUE PD-Regler-Parameter
        self.kp = -0.05  # Proportional-Gain
        self.kd = -0.1  # Derivative-Gain
        self.previous_error = None  # Speichert den Fehler aus dem vorherigen Zyklus

        # NEUE STATUS-VARIABLEN
        self.status = "Initial"
        self.last_status = "Initial"

        # EXV-Einstellungen
        self.exv_opening = 50.0

    def start_up(self):
        """Setzt die EXV-Öffnung auf den Startwert und deaktiviert den Pump-Down-Modus."""
        self.exv_opening = 50.0
        self.pump_down_active = False
        self.status = "Normal"
        self.last_status = "Initial"
        self.DTC_wait_time = 0.0
        self.waiting = False
        self.previous_error = None
        return self.exv_opening, self.pump_down_active

    def pump_down(self):
        """Aktiviert den Pump-Down-Modus und schließt das Ventil vollständig."""
        self.exv_opening = 0.0
        self.pump_down_active = True
        self.status = "Pump Down"
        self.last_status = "Normal"
        self.DTC_wait_time = 0.0
        self.waiting = False
        self.previous_error = None
        return self.exv_opening, self.pump_down_active

    def set_exv_absolut(self, mode, tdc_soll, tdc_ist, exv_open_soll=50.0):
        self.last_status = self.status
        new_status = self.status

        # Priorität 1: Direkte Sollwertübernahme (Modus 0)
        if mode == 0:
            self.exv_opening = exv_open_soll
            new_status = "Direct Control"

        # Modus 2: PD-Regelung  TODO: Testen mit Versuchsdaten
        elif mode == 2:
            dtc = tdc_ist - tdc_soll + self.Superheat_soll
            error = dtc - self.DTC_Superheat

            if self.previous_error is None:
                self.previous_error = error

            derivative = error - self.previous_error

            # PD-Regelungs-Ausgabe
            pd_output = self.kp * error + self.kd * derivative

            self.exv_opening -= pd_output
            self.exv_opening = max(0.0, min(self.exv_opening, 100.0))  # Begrenzung auf 0-100%

            self.previous_error = error
            new_status = "PD Control"
            self.waiting = False
            self.DTC_wait_time = 0.0

        # Modus 1: Normale TDC-basierte Regelung (mit Wartezeit und Sicherheitslogik)
        elif mode == 1:
            dtc = tdc_ist - tdc_soll + self.Superheat_soll

            # Priorität 2: Kritische Sicherheitsprüfungen
            if tdc_ist > 130.0:
                self.exv_opening = min(self.exv_opening + 5, 100)
                new_status = "Critical High Temp"
            elif dtc < self.DTC_Superheat_critical_low:
                self.exv_opening = max(0.0, self.exv_opening - self.DTC_Superheat_critical_low_step)
                new_status = "Critical Low SH"

            # Priorität 3: Wartezeit-Logik (nur wenn kein kritischer Status)
            elif self.waiting:
                self.DTC_wait_time -= 1
                if self.DTC_wait_time <= 0:
                    self.waiting = False
                    new_status = "Normal"
                else:
                    new_status = "Waiting"

            # Priorität 4: Normale TDC-basierte Regelung
            elif self.DTC_Superheat <= dtc < self.DTC_Superheat_high:
                new_status = "Normal"
            elif dtc >= self.DTC_Superheat_high:
                self.exv_opening = min(self.exv_opening + 1, 100)
                self.DTC_wait_time = self.DTC_wait_time_high_DTC
                self.waiting = True
                new_status = "High Superheat"
            elif dtc < self.DTC_Superheat_low:
                self.exv_opening = max(0.0, self.exv_opening - 1)
                self.DTC_wait_time = self.DTC_wait_time_low_DTC
                self.waiting = True
                new_status = "Low Superheat"

        # Zustand aktualisieren und Wartezeit zurücksetzen bei Statusänderung
        if new_status != self.last_status:
            self.status = new_status
            self.waiting = False
            self.DTC_wait_time = 0.0
            print(f"Status changed from '{self.last_status}' to '{self.status}'. Wait time reset.")

        return self.exv_opening


# --- Test-Routine ---

def run_test_scenario(exv_instance, test_cases, filename):
    """
    Führt eine Reihe von Testfällen über die Zeit aus und protokolliert die Ergebnisse.

    :param exv_instance: Die Instanz der EM_expansion_valve-Klasse.
    :param test_cases: Eine Liste von Dictionaries mit den Testdaten.
    :param filename: Der Name der Excel-Datei, in die geschrieben werden soll.
    """
    results = []

    for case in test_cases:
        print(f"\n--- Start Szenario: {case['description']} ---")
        exv_instance.start_up()

        for i in range(case['duration']):
            # Simuliere die Datenänderung pro Zeitschritt, falls spezifiziert
            if i < len(case['tdc_ist_profile']):
                current_tdc_ist = case['tdc_ist_profile'][i]
            else:
                current_tdc_ist = case['tdc_ist_profile'][-1]

            new_opening = exv_instance.set_exv_absolut(
                mode=case['mode'],
                tdc_soll=case['tdc_soll'],
                tdc_ist=current_tdc_ist,
                exv_open_soll=case['exv_open_soll']
            )

            # Sammle die Daten für die Protokollierung
            results.append({
                "Zeit (s)": i + 1,
                "Szenario": case['description'],
                "Mode": case['mode'],
                "TDC_ist": current_tdc_ist,
                "TDC_soll": case['tdc_soll'],
                "EXV_Opening_Neu": new_opening,
                "Wait_Time_Left": exv_instance.DTC_wait_time,
                "Is_Waiting": exv_instance.waiting,
                "Status": exv_instance.status,
                "Last_Status": exv_instance.last_status
            })

            # Kurze Pause zur Simulation des Zeitverlaufs
            time.sleep(0.01)

            # Schreibe die Ergebnisse in eine Excel-Datei
    df = pd.DataFrame(results)
    df.to_excel(filename, index=False)
    print(f"\nTest beendet. Ergebnisse in '{filename}' gespeichert.")


# Definieren der Testfälle
test_cases_list = [
    {
        "description": "Modus 0: Direkte manuelle Steuerung auf 70%",
        "mode": 0,
        "tdc_soll": 80.0,
        "tdc_ist_profile": [85.0] * 5,
        "exv_open_soll": 70.0,
        "duration": 5
    },
    {
        "description": "Modus 1: Normale Regelung (keine Änderung)",
        "mode": 1,
        "tdc_soll": 80.0,
        "tdc_ist_profile": [95.0] * 20,
        "exv_open_soll": 50.0,
        "duration": 20
    },
    {
        "description": "Modus 1: Überhitzung zu hoch (Ventil öffnet & Wartezeit beginnt)",
        "mode": 1,
        "tdc_soll": 80.0,
        "tdc_ist_profile": [121.0] * 5,
        "exv_open_soll": 50.0,
        "duration": 5
    },
    {
        "description": "Modus 1: Überhitzung zu niedrig (Ventil schließt & Wartezeit beginnt)",
        "mode": 1,
        "tdc_soll": 80.0,
        "tdc_ist_profile": [86.0] * 5,
        "exv_open_soll": 50.0,
        "duration": 5
    },
    {
        "description": "Modus 1: Wartezeit wird durch kritische Bedingung unterbrochen",
        "mode": 1,
        "tdc_soll": 80.0,
        "tdc_ist_profile": [121.0, 121.0, 79.0, 79.0, 79.0, 79.0, 79.0],
        "exv_open_soll": 50.0,
        "duration": 7
    },
    {
        "description": "Modus 1: Kritische Überhitzung (sofortiges Schließen)",
        "mode": 1,
        "tdc_soll": 80.0,
        "tdc_ist_profile": [79.0] * 5,
        "exv_open_soll": 50.0,
        "duration": 5
    },
    {
        "description": "Modus 1: Notfall-Situation (>130°C)",
        "mode": 1,
        "tdc_soll": 80.0,
        "tdc_ist_profile": [135.0] * 5,
        "exv_open_soll": 50.0,
        "duration": 5
    },
    {
        "description": "Modus 2: PD Kontrolle schnell",
        "mode": 2,
        "tdc_soll": 80.0,
        "tdc_ist_profile": [121.0, 121.0, 79.0, 79.0, 79.0, 79.0, 79.0],
        "exv_open_soll": 50.0,
        "duration": 7
    },
    {
        "description": "Modus 2: PD Kontrolle Umordnung",
        "mode": 2,
        "tdc_soll": 80.0,
        "tdc_ist_profile": [121.0, 121.0, 120.0, 119.0, 117.0, 115.0, 112.0, 108.0, 102.0, 98.0,
                            92.0, 85.0, 80.0, 78.0, 76.0, 78.0, 79.0, 79.0, 79.0, 79.0, 79.0],
        "exv_open_soll": 50.0,
        "duration": 21
    },

]

if __name__ == "__main__":
    exv_test = Expansion_valve(mode="wp")
    run_test_scenario(exv_test, test_cases_list, "EXV_Testprotokoll.xlsx")