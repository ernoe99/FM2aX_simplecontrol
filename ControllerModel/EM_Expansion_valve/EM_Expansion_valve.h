#ifndef EM_EXPANSION_VALVE_H
#define EM_EXPANSION_VALVE_H

class EMExpansionValve {
public:
    // Konstruktor
    EMExpansionValve(int mode = 1);

    // Hauptregelungs-Methode
    double setExvAbsolut(int mode, double tdc_soll, double tdc_ist, double exv_open_soll = 50.0);

    // Hilfsmethoden zur Zustandsverwaltung
    double startUp();
    double pumpDown();

private:
    int mode;
    bool pump_down_active;

    // Regelungsparameter
    const double Superheat_soll = 10.0;
    const double DTC_Superheat_low = 8.0;
    const double DTC_Superheat_critical_low = 3.0;
    const double DTC_Superheat_high = 40.0;
    double DTC_wait_time = 0.0;
    const double DTC_wait_time_high_DTC = 300.0;
    const double DTC_wait_time_low_DTC = 60.0;
    const double DTC_Superheat_critical_low_step = 5.0;
    bool waiting = false;

    // Aktueller Zustand
    double exv_opening = 50.0;
};

#endif // EM_EXPANSION_VALVE_H

