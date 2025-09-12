# Import der bereitgestellten EM-Klassen

from pathlib import Path
from ControllerModel.EM_Compressor import EM_Compressor
from ControllerModel.EM_Expansion_valve.EM_Expansion_valve_PDext_testdrv import Expansion_valve
from ControllerModel.EM_Airflow.EM_Airflow import Airflow,FM2_AF_model
from ControllerModel.EM_internal_tk.EM_common_tk_PDctrl import Internal_tk

# VZN175 = EM_Compressor("../json_data_cmp/VZN175.json")


class HP:
    """
    Zentrale Steuerungseinheit (Heat Pump) die alle Equipment-Module (EMs)
    als Komponenten initialisiert und verwaltet.
    """

    def __init__(self, name: str,
                 compressor_type: str,
                 exv_mode: str,
                 tk_plus_dt: float,
                 fan_speed_max: float):
        """
        Initialisiert das HP-Objekt und seine Komponenten mit Variablen aus einer
        simulierten Benutzeroberfläche.

        :param compressor_type: Typ des verwendeten Kompressors (z.B. 'VZN175').
        :param exv_mode: Betriebsmodus des Expansionsventils ('user' oder 'wp').
        :param tk_plus_dt: Erhöhung der Trennkreis-Temperatur.
        :param fan_speed_max: Maximale Drehzahl der Lüfter.
        """
        print("--- HP-Objekt wird initialisiert ---")
        self.name = name

        # Komponenten als Attribute der HP-Klasse initialisieren
        # 1. Kompressor
        project_root = Path(__file__).parent.parent
        json_file_path = project_root / 'EM_Compressor' / 'json_data_cmp' / 'VZN175.json'

        self.compressor = EM_Compressor.Compressor(json_file_path)

        # 2. Expansionsventil
        self.expansion_valve = Expansion_valve()   # PD Controller

        # 3. Interner Trennkreis (Itk)
        self.internal_tk = Internal_tk(tk_plus_dt)

        # 4. Luftstrom (Fans)
        self.airflow = FM2_AF_model

        # 5. Common_tc_request ist Teil der common_tk Klasse, da dort die
        #    Pumpen und Ventil-Steuerung abgebildet sind.

        print("--- Alle HP-Komponenten erfolgreich initialisiert ---")

    def run_cycle(self):
        """
        Führt einen beispielhaften Regelzyklus aus, indem die run-Methoden der
        einzelnen Komponenten aufgerufen werden.
        """
        print("\n--- HP-Regelzyklus gestartet ---")

        # Beispielhafte Aufrufe der Komponenten-Logik
        # Beispiel für die Verwendung von calculate_direct
        speed_rps = 100.0
        t_suction_degC = 10.0
        t_condensation_degC = 50.0

        results = self.compressor.calculate_direct(speed_rps, t_suction_degC, t_condensation_degC)

        x = self.expansion_valve.set_exv_absolut(mode=2, tdc_soll=80, tdc_ist=100)
        y = self.internal_tk.run(Tvl_soll=45, Tvl_tk=46, Trl_tk=28, Tvl_hk=42, Trl_hk=28, Vol_tk=1.0)
        z = self.airflow.set_volume_air(oat=-10, power=50.0)

        print("--- HP-Regelzyklus beendet ---")


if __name__ == "__main__":
    # Beispielhafte GUI-Variablen
    GUI_VARS = {
        "name": "FM_2aX",
        "compressor_type": "VZN175",
        "exv_mode": "wp",
        "tk_plus_dt": 1.5,
        "fan_speed_max": 90.0
    }

    # Initialisierung des HP-Objekts mit den GUI-Variablen
    my_heat_pump = HP(
        name=GUI_VARS["name"],
        compressor_type=GUI_VARS["compressor_type"],
        exv_mode=GUI_VARS["exv_mode"],
        tk_plus_dt=GUI_VARS["tk_plus_dt"],
        fan_speed_max=GUI_VARS["fan_speed_max"]
    )

    # Ausführen eines Testzyklus
    my_heat_pump.run_cycle()