#include "EMExpansionValve.h"
#include <iostream>
#include <algorithm> // Für std::min und std::max

// Konstruktor-Implementierung
EMExpansionValve::EMExpansionValve(int mode) : mode(mode) {}

// Hilfsmethoden-Implementierung
double EMExpansionValve::startUp() {
    this->exv_opening = 50.0;
    this->pump_down_active = false;
    return this->exv_opening;
}

double EMExpansionValve::pumpDown() {
    this->exv_opening = 0.0;
    this->pump_down_active = true;
    return this->exv_opening;
}

// Hauptregelungs-Methode
double EMExpansionValve::setExvAbsolut(int mode, double tdc_soll, double tdc_ist, double exv_open_soll) {
    // Priorität 1: Direkte Sollwertübernahme (Modus 0)
    if (mode == 0) {
        this->exv_opening = exv_open_soll;
        this->waiting = false;
        this->DTC_wait_time = 0.0;
        return this->exv_opening;
    }

    // Priorität 2: Kritische Sicherheitsprüfung für hohe Temperatur
    if (tdc_ist > 130.0) {
        std::cout << "Compressor discharge Temperature above 130C - taking actions" << std::endl;
        this->exv_opening = std::min(this->exv_opening + 5.0, 100.0);
        this->waiting = false;
        this->DTC_wait_time = 0.0;
        return this->exv_opening;
    }

    double dtc = tdc_ist - tdc_soll + Superheat_soll;

    // Priorität 2: Kritische Sicherheitsprüfung für niedrige Überhitzung
    if (dtc < DTC_Superheat_critical_low) {
        std::cout << "Critical low superheat detected - closing valve" << std::endl;
        this->exv_opening = std::max(0.0, this->exv_opening - DTC_Superheat_critical_low_step);
        this->waiting = false;
        this->DTC_wait_time = 0.0;
        return this->exv_opening;
    }

    // Priorität 3: Wartezeit-Logik
    if (this->waiting) {
        this->DTC_wait_time--; // Wartezeit herunterzählen
        if (this->DTC_wait_time <= 0.0) {
            this->waiting = false;
        }
        return this->exv_opening; // Im Wartezustand keine weitere Regelung
    }

    // Priorität 4: Normale TDC-basierte Regelung
    if (dtc >= DTC_Superheat_high) {
        std::cout << "High superheat detected - opening valve and starting wait period" << std::endl;
        this->exv_opening = std::min(this->exv_opening + 1.0, 100.0);
        this->DTC_wait_time = DTC_wait_time_high_DTC;
        this->waiting = true;
    } else if (dtc < DTC_Superheat_low) {
        std::cout << "Low superheat detected - closing valve and starting wait period" << std::endl;
        this->exv_opening = std::max(0.0, this->exv_opening - 1.0);
        this->DTC_wait_time = DTC_wait_time_low_DTC;
        this->waiting = true;
    }

    return this->exv_opening;
}