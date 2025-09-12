FUNCTION_BLOCK EM_expansion_valve_FB
VAR_INPUT
    mode : INT;
    tdc_soll : REAL;
    tdc_ist : REAL;
    exv_open_soll : REAL := 50.0;
END_VAR
VAR_OUTPUT
    exv_opening : REAL;
END_VAR
VAR
    pump_down_active : BOOL := FALSE;
    Superheat_soll : REAL := 10.0;
    DTC_Superheat_low : REAL := 8.0;
    DTC_Superheat_critical_low : REAL := 3.0;
    DTC_Superheat_high : REAL := 40.0;
    DTC_wait_time : REAL := 0.0;
    DTC_wait_time_high_DTC : REAL := 300.0;
    DTC_wait_time_low_DTC : REAL := 60.0;
    DTC_Superheat_critical_low_step : REAL := 5.0;
    waiting : BOOL := FALSE;
END_VAR

// Hilfsvariable
VAR
    dtc : REAL;
END_VAR

// Methoden als Prozeduren (Funktionen oder Methoden innerhalb des FB)
// Die Logik der Python-Methode 'start_up' wird direkt in der Initialisierung oder einer speziellen Routine behandelt.
// Die Logik der Python-Methode 'pump_down' wird hier direkt in der Logik abgebildet.

// Hauptlogik des Funktionsbausteins (entspricht der Methode 'set_exv_absolut')
IF mode = 0 THEN
    exv_opening := exv_open_soll;
    waiting := FALSE;
    DTC_wait_time := 0.0;
    RETURN; // Beendet die Ausführung des Funktionsbausteins
END_IF;

// Sofortige Sicherheitsprüfung: Kritisch hohe Verdichter-Austrittstemperatur
IF tdc_ist > 130.0 THEN
    exv_opening := MIN(exv_opening + 5.0, 100.0);
    waiting := FALSE;
    DTC_wait_time := 0.0;
    RETURN;
END_IF;

dtc := tdc_ist - tdc_soll + Superheat_soll;

// Sofortige Sicherheitsprüfung: Kritisch niedrige Überhitzung
IF dtc < DTC_Superheat_critical_low THEN
    exv_opening := MAX(0.0, exv_opening - DTC_Superheat_critical_low_step);
    waiting := FALSE;
    DTC_wait_time := 0.0;
    RETURN;
END_IF;

// Wartezeit abfragen und herunterzählen
IF waiting THEN
    DTC_wait_time := DTC_wait_time - 1.0;
    IF DTC_wait_time <= 0.0 THEN
        waiting := FALSE;
    END_IF;
    RETURN; // Im Wartezustand keine weitere Regelung durchführen
END_IF;

// TDC-basierte Regelung (mode != 0)
IF dtc >= DTC_Superheat_high THEN
    exv_opening := MIN(exv_opening + 1.0, 100.0);
    DTC_wait_time := DTC_wait_time_high_DTC;
    waiting := TRUE;
ELSIF dtc < DTC_Superheat_low THEN
    exv_opening := MAX(0.0, exv_opening - 1.0);
    DTC_wait_time := DTC_wait_time_low_DTC;
    waiting := TRUE;
END_IF;