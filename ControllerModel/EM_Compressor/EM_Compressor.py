import json
from typing import List, Tuple
import numpy as np
from pathlib import Path

# Definition eines Punktes als Tuple (x, y)
Point = Tuple[float, float]


class Compressor:
    """
    Objektorientiertes Equipment-Modul für einen Verdichter.
    Liess Polynom-Koeffizienten und Betriebsgrenzen aus einer JSON-Datei.
    """

    def __init__(self, json_file_path, high_value_temporary_out_of_field: int = 300):
        """
        Initialisiert das Objekt durch Laden der Daten aus der JSON-Datei
        und Initialisieren der Zähler.
        """
        try:
            with open(json_file_path, 'r') as f:
                data = json.load(f)
            self.poly_data = data["poly_data"]
            self.polygons = data["polygons"]
            self.n1_values = data["n1_values"]
            self.n2_values = data["n2_values"]
            print(f"Daten erfolgreich aus {json_file_path} geladen.")
        except FileNotFoundError:
            print(f"Fehler: Die Datei {json_file_path} wurde nicht gefunden.")
            raise

        # Initialisierung der neuen Zähler
        self.limit_speed = 0
        self.out_of_field = 0
        self.temporary_out_of_field = 0
        self.high_value_temporary_out_of_field = high_value_temporary_out_of_field

    def check_polygon(self, Tevaporation: float, Tcondensing: float) -> Tuple[bool, float, float]:
        """
        Überprüft, ob der Punkt [Tevaporation, Tcondensing] innerhalb
        eines der Polygone liegt und gibt die zugehörigen n1- und n2-Werte zurück.
        """
        x, y = Tevaporation, Tcondensing

        for i, polygon in enumerate(self.polygons):
            inside = False
            num_points = len(polygon)

            j = 0
            k = num_points - 1
            while j < num_points:
                x1, y1 = polygon[j]
                x2, y2 = polygon[k]

                if ((y1 > y) != (y2 > y)) and (x < (x2 - x1) * (y - y1) / (y2 - y1) + x1):
                    inside = not inside

                k = j
                j += 1

            if inside:
                return True, self.n1_values[i], self.n2_values[i]

        return False, 0.0, 0.0

    def speed_limiter(self, speed: float, T_evaporation: float, T_condensing: float) -> float:
        """
        Begrenzt die Geschwindigkeit basierend auf den Betriebsgrenzen des Verdichters.
        Erhöht Zähler für Fehlerfälle und löst eine Exception aus, wenn die
        Betriebsgrenzen zu lange überschritten werden.
        """
        is_inside, n1, n2 = self.check_polygon(T_evaporation, T_condensing)

        if is_inside:
            self.temporary_out_of_field = 0
            n_corr = max(n1, min(speed, n2))
            if n_corr != speed:
                self.limit_speed += 1
            return n_corr  # return corrected speed
        else:
            self.temporary_out_of_field += 1
            self.out_of_field += 1

            if self.temporary_out_of_field > self.high_value_temporary_out_of_field:
                raise Exception(f"EM_Compressor: reporting out of compressor map for more than "
                                f"{self.high_value_temporary_out_of_field} - stopping to save compressor")

            # Rückgabe der ursprünglichen Geschwindigkeit, da keine Begrenzung möglich ist,
            # wenn sich der Punkt außerhalb der gültigen Bereiche befindet.
            return speed

    def calculate_direct(self, speed: float, t_suction: float, t_condensation: float) -> np.ndarray:
        """
        Berechnung der Heizparameter mit polynomialen Koeffizienten.
        """
        poly_data = self.poly_data

        def calculate_component(il, co, speed, t_suc, t_con, data):
            # Hilfsfunktion zur wiederkehrenden Berechnung
            base = float(data[il + co]) \
                   + data[il + co + 1] * t_suc \
                   + data[il + co + 2] * t_con \
                   + data[il + co + 3] * t_suc ** 2 \
                   + data[il + co + 4] * t_con ** 2

            term1 = t_suc * t_con * (
                    (speed ** 2) * (data[il + co + 5] + data[il + co + 6] * t_suc + data[il + co + 7] * t_con) +
                    speed * (data[il + co + 8] + data[il + co + 9] * t_suc + data[il + co + 10] * t_con) +
                    data[il + co + 11] + data[il + co + 12] * t_suc + data[il + co + 13] * t_con
            )

            term2 = data[il + co + 14] * t_suc ** 3 + data[il + co + 15] * t_con ** 3

            term3 = speed * (
                    data[il + co + 16] + data[il + co + 17] * t_suc + data[il + co + 18] * t_con +
                    data[il + co + 19] * t_suc ** 2 + data[il + co + 20] * t_con ** 2 +
                    data[il + co + 21] * t_suc ** 3 + data[il + co + 22] * t_con ** 3
            )

            term4 = speed ** 2 * (
                    data[il + co + 23] + data[il + co + 24] * t_suc + data[il + co + 25] * t_con +
                    data[il + co + 26] * t_suc ** 2 + data[il + co + 27] * t_con ** 2 +
                    data[il + co + 28] * t_suc ** 3 + data[il + co + 29] * t_con ** 3
            )

            return base + term1 + term2 + term3 + term4

        # Hauptberechnungen
        capacity = calculate_component(0, 0, speed, t_suction, t_condensation, poly_data)
        epower = calculate_component(0, 30, speed, t_suction, t_condensation, poly_data)
        ecurrent = calculate_component(0, 60, speed, t_suction, t_condensation, poly_data)
        comppower = calculate_component(0, 30, speed, t_suction, t_condensation, poly_data)
        massflow = calculate_component(0, 90, speed, t_suction, t_condensation, poly_data)
        Tdischarge = calculate_component(0, 120, speed, t_suction, t_condensation, poly_data)

        # Endberechnungen
        qheat = capacity + comppower
        cop = qheat / epower if epower != 0 else 0
        invpower = epower - comppower

        return np.array([qheat, epower, massflow, ecurrent, capacity, cop, Tdischarge, invpower])


# VZN175 = Compressor("json_data_cmp/VZN175.json")  # Achtung Pfad aus EM_HP geändert hier nur relativ
# VZN220 = Compressor("json_data_cmp/VZN220.json")  # Achtung Pfad aus EM_HP geändert hier nur relativ


# Beispiel für die Verwendung des Objekts
if __name__ == '__main__':
    # Annahme: 'compressor_data.json' wurde mit dem oben gezeigten JSON-Inhalt erstellt.
    # compressor = EM_Compressor("json_data_cmp/VZN175.json")
    project_root = Path(__file__).parent.parent
    json_file_path = project_root / 'json_data' / 'VZN175.json'

    compressor = Compressor("json_data_cmp/VZN220.json")

    # Beispiel für die Verwendung von check_polygon
    T_evaporation = 10.0
    T_condensing = 50.0
    is_inside, n1, n2 = compressor.check_polygon(T_evaporation, T_condensing)
    if is_inside:
        print(
            f"Betriebspunkt ({T_evaporation}, {T_condensing}) liegt innerhalb des Polygons. Drehzahlbereich: {n1} - {n2} rps.")
    else:
        print(f"Betriebspunkt ({T_evaporation}, {T_condensing}) liegt außerhalb des Polygons.")
        compressor.temporary_out_of_field += 1

    # Beispiel für die Verwendung von calculate_direct
    speed_rps = 100.0
    t_suction_degC = 10.0
    t_condensation_degC = 50.0
    results = compressor.calculate_direct(speed_rps, t_suction_degC, t_condensation_degC)

    print("\nErgebnisse der direkten Berechnung:")
    print(f"Wärmeleistung (qheat): {results[0]:.2f} W")
    print(f"Elektrische Leistung (epower): {results[1]:.2f} W")
    print(f"Massenstrom: {results[2]:.5f} kg/s")
    print(f"Stromaufnahme: {results[3]:.2f} A")
    print(f"Kälteleistung (capacity): {results[4]:.2f} W")
    print(f"Leistungszahl (COP): {results[5]:.2f}")
    print(f"Endtemperatur (Tdischarge): {results[6]:.2f} C")