FUNCTION_BLOCK EM_heating_cycle_FB
VAR_INPUT
    Tvl_soll : REAL;
    Tvl_tk : REAL;
    Vol_hk : REAL;
    Trl_tk : REAL;
    Tvl_hk : REAL;
    Trl_hk : REAL;
END_VAR
VAR_OUTPUT
    Pump_signal_req_change : REAL;
    P_hk_ist : REAL;
END_VAR
VAR
    K_pump_hk : REAL := 1.0;
    Pump_signal : REAL := 0.0;
    Pump_signal_min : REAL := 0.0;
    cp_hk : REAL := 4182.0; // Spezifische Wärmekapazität von Wasser (J/kg*K)
    rho_hk : REAL := 997.0; // Dichte von Wasser (kg/m³)
END_VAR

// Hilfsvariablen
VAR
    S : REAL;
END_VAR

// Hauptlogik des Funktionsbausteins (entspricht der Python-Methode 'run')
P_hk_ist := Vol_hk * cp_hk * rho_hk * (Tvl_hk - Trl_hk);

S := K_pump_hk * (Tvl_soll - Tvl_hk) / (Tvl_hk - Trl_hk);

Pump_signal := MAX(Pump_signal_min, Pump_signal - S);

Pump_signal_req_change := Pump_signal;