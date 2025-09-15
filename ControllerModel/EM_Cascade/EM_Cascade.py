from pathlib import Path
import json
import math
import collections


# --- Platzhalter für HP- und Kompressor-Logik (aus EM_Cascade.py) ---
class MockCompressor:
    def predict(self, T_ambient, humidity):
        """
        Simuliert die Rückgabe von Leistungsdaten für verschiedene Drehzahlen.
        Gibt eine Liste von Tupeln zurück: (speed, power).
        """
        # Beispiel: Vereinfachte Leistungsdaten für VZN175
        return [
            (50, 10.0), (60, 12.5), (70, 15.0), (80, 17.5),
            (90, 20.0), (100, 22.0), (110, 24.5), (120, 27.0)
        ]


class MockHP:
    """Simuliert eine einzelne HP-Einheit mit Laufzeit und Kompressor-Instanz."""

    def __init__(self, hp_type, runtime=0.0):
        self.hp_type = hp_type
        self.compressor = MockCompressor()
        self.runtime_hp = runtime
        self.is_running = False

    def get_power_estimates(self, T_ambient, humidity):
        return self.compressor.predict(T_ambient, humidity)


# --- EM_Cascade Klasse ---
class EM_Cascade:
    def __init__(self, hp_types: list):
        """
        Initialisiert die EM_Cascade mit den HP-Typen.
        """
        print("--- EM_Cascade wird initialisiert ---")
        self.hp_units = [MockHP(hp_type) for hp_type in hp_types]
        self.no_hp = len(self.hp_units)
        self.act_running = [False] * self.no_hp
        self.runtime_hp = [0.0] * self.no_hp

        # FIX: last_time muss initialisiert werden, sonst kommt es zu einem AttributeError
        self.last_time = [0.0] * self.no_hp

    def select_hp(self, desired_power, is_data):
        """
        Wählt die beste Kombination von HPs und Drehzahlen, um die
        gewünschte Leistung zu erzeugen.

        :param desired_power: Die gewünschte thermische Leistung.
        :param is_data: Umfeldsensordaten.
        :return: Eine Liste von Tupeln (hp_index, speed), die die ausgewählten HPs
                 und ihre Ziel-Drehzahlen darstellen.
        """
        if self.no_hp == 1:
            # Bei nur einer HP, keine Auswahllogik erforderlich
            # Wir nehmen einfach die höchste Drehzahl
            hp_powers = self.hp_units[0].get_power_estimates(is_data["Tair"], is_data["Rfair"])
            best_speed = 0.0
            for speed, power in hp_powers:
                if power >= desired_power:
                    best_speed = speed
                    break
            if best_speed == 0.0:
                best_speed = hp_powers[-1][0]

            return [(0, best_speed)]

        # --- Mehr-HP-Logik ---
        running_hps = [i for i, is_running in enumerate(self.act_running) if is_running]
        stopped_hps = [i for i, is_running in enumerate(self.act_running) if not is_running]

        selected_combinations = []
        best_combination = []
        min_power_diff = float('inf')

        # 1. Priorität: Laufende HPs
        # Wir versuchen, die Anforderungen zuerst mit den laufenden HPs zu erfüllen.
        for hp_index in running_hps:
            hp = self.hp_units[hp_index]
            power_estimates = hp.get_power_estimates(is_data["Tair"], is_data["Rfair"])
            for speed, power in power_estimates:
                current_power = power
                # Hier könnte eine komplexere Kombinatorik-Logik für mehrere laufende HPs
                # implementiert werden, um die beste Kombination zu finden.
                if abs(desired_power - current_power) < min_power_diff:
                    min_power_diff = abs(desired_power - current_power)
                    best_combination = [(hp_index, speed)]

        # 2. Zweite Priorität: Wenn die Leistung nicht reicht, füge die HP mit der
        #    niedrigsten Laufzeit hinzu.
        # FIX: Die Überprüfung muss sicherstellen, dass best_combination nicht leer ist,
        #      bevor auf das erste Element zugegriffen wird.
        current_power = 0.0
        if best_combination:
            current_power = best_combination[0][1]

        if current_power < desired_power:
            # Sortiere die gestoppten HPs nach der geringsten Laufzeit
            stopped_hps.sort(key=lambda i: self.runtime_hp[i])

            for hp_index in stopped_hps:
                hp = self.hp_units[hp_index]
                power_estimates = hp.get_power_estimates(is_data["Tair"], is_data["Rfair"])

                # Wir nehmen die HP mit der höchsten Drehzahl und prüfen, ob die Kombination
                # die Anforderung erfüllt.
                for speed, power in power_estimates:
                    if (current_power + power) > desired_power:
                        best_combination.append((hp_index, speed))
                        return best_combination

        return best_combination

    def run(self, desired_power, is_data, current_time):
        """
        Führt die Kaskadenlogik aus.
        """
        # Entscheidung: Einzel-HP- oder Mehr-HP-Logik
        selected_hps = self.select_hp(desired_power, is_data)

        # Aktualisiere den Laufstatus und die Laufzeiten
        hp_starting = [False] * self.no_hp
        for i in range(self.no_hp):
            is_selected = any(hp_index == i for hp_index, speed in selected_hps)
            if is_selected and not self.act_running[i]:
                # Eine neue HP startet
                self.act_running[i] = True
                hp_starting[i] = True
                self.last_time[i] = current_time
            elif not is_selected and self.act_running[i]:
                # Eine laufende HP wird gestoppt
                self.act_running[i] = False
                self.runtime_hp[i] += current_time - self.last_time[i]
                self.last_time[i] = 0.0

        return selected_hps, self.act_running, self.runtime_hp


if __name__ == "__main__":
    # --- Beispiel-Szenario mit 3 HPs ---
    hp_list_multi = ["pro_70", "pro_70", "pro_70"]
    cascade_multi = EM_Cascade(hp_types=hp_list_multi)

    # Simuliere Start- und Sensordaten
    is_data_multi = {"Tair": 10.0, "Rfair": 60.0}

    # Beispiel mit P_soll
    desired_power_multi = 20.0
    current_time_multi = 0

    print("--- Mehr-HP-Szenario: Start ---")
    selected_hps, act_running, runtime = cascade_multi.run(desired_power_multi, is_data_multi, current_time_multi)
    print(f"Gewählte HPs und Drehzahlen: {selected_hps}")
    print(f"Laufstatus: {act_running}")
    print(f"Laufzeiten: {runtime}")

    # Simuliere nächsten Zeitschritt, Leistung steigt an
    current_time_multi = 60
    desired_power_multi = 35.0
    selected_hps, act_running, runtime = cascade_multi.run(desired_power_multi, is_data_multi, current_time_multi)
    print("\n--- Mehr-HP-Szenario: Leistung steigt, weitere HP wird benötigt ---")
    print(f"Gewählte HPs und Drehzahlen: {selected_hps}")
    print(f"Laufstatus: {act_running}")
    print(f"Laufzeiten: {runtime}")

    # Simuliere das Beenden der Simulation und Speichern der Laufzeiten
    current_time_multi = 120
    desired_power_multi = 0.0
    selected_hps, act_running, runtime = cascade_multi.run(desired_power_multi, is_data_multi, current_time_multi)
    print("\n--- Mehr-HP-Szenario: Simulation beendet ---")
    print(f"Gewählte HPs und Drehzahlen: {selected_hps}")
    print(f"Laufstatus: {act_running}")
    print(f"Laufzeiten: {runtime}")

    # --- Beispiel-Szenario mit 1 HP ---
    hp_list_single = ["VZN175"]
    cascade_single = EM_Cascade(hp_types=hp_list_single)
    is_data_single = {"Tair": 10.0, "Rfair": 60.0}
    desired_power_single = 15.0

    print("\n--- Einzel-HP-Szenario ---")
    selected_hps, act_running, runtime = cascade_single.run(desired_power_single, is_data_single, 0)
    print(f"Gewählte HP und Drehzahl: {selected_hps}")
    print(f"Laufstatus: {act_running}")
    print(f"Laufzeiten: {runtime}")