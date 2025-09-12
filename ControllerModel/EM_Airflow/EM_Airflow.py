class Airflow:

    def __init__(self, minpower, maxpower, references, set_volume_WW_factor, set_volume_CO_factor):

        self.minpower = minpower
        self.maxpower = maxpower
        self.set_volume_WW_factor = set_volume_WW_factor
        self.set_volume_CO_factor = set_volume_CO_factor
        self.references = sorted(references, key=lambda x: x["temp"])
        self.temps = [r["temp"] for r in references]

    def set_volume_air(self, oat, power):

        """

        Berechnet einen OAT-abhängigen Parameter basierend auf Power und Temperatur.

        Die Formel ist nun value = K0 + K1 * power (z. B. für -10°C: 12000 + 50*power).


        Interpolation/Extrapolation:
        Die Berechnung erfolgt immer auf Basis der K0/K1-Koeffizienten der Referenztemperaturen.

        Beispiel-Tests:

        python
        Copy
        print(calculate_parameter(-10, 50))  # 12000 + 50*50 = 14.500 → 14.500
        print(calculate_parameter(2, 30))    # 12500 - 150*30 = 8.000 → 12.000 (Mindestwert)
        print(calculate_parameter(12, 80))   # 18000 - 100*80 = 10.000 → 16.500 (Mindestwert)
        print(calculate_parameter(5, 40))    # Interpoliert zwischen 2°C und 12°C
        Mindestwerte:

        Für oat < 12°C: Mindestwert = 12.000

        Für oat >= 12°C: Mindestwert = 16.500

        Optionale Höchstwerte:
        Falls benötigt, kann "max" (z. B. 20.000) als Obergrenze gesetzt werden.

        Hinweis:
        Passen Sie die K0/K1-Werte in references an Ihre tatsächlichen Formeln an.

        Die Funktion wirft einen Fehler, falls power außerhalb von [20, 90] liegt. Args:
            oat (float): Outside Air Temperature in °C (beliebiger Wert) -20 - 42
            power (float): Power-Wert (20 <= power <= 90)

        Returns:
            int: Der berechnete Parameter, begrenzt durch Mindest-/Höchstwerte


        """
        # 1. Input-Validierung
        if not (self.minpower <= power <= self.maxpower):
            raise ValueError("Power muss zwischen minpower und maxpower liegen")  # noch zu prüfen
        calculated = 12000

        # 3. Hilfsfunktion: Berechnet Wert für eine gegebene Referenz
        def calc_value(reference):
            return min(max(reference["K0"] + reference["K1"] * power, reference["min"]), reference["max"])

        # 4. Logik für Interpolation/Extrapolation
        if oat in self.temps:
            # Exakte Referenztemperatur
            calculated = calc_value(next(r for r in self.references if r["temp"] == oat))
        elif oat < self.temps[0]:
            # Extrapolation unterhalb -10°C (verwendet -10°C-Formel)
            calculated = calc_value(self.references[0])
        elif oat > self.temps[-1]:
            # Extrapolation oberhalb 12°C (verwendet 12°C-Formel)
            calculated = calc_value(self.references[-1])
        else:
            # Interpolation zwischen zwei Referenzpunkten
            for i in range(len(self.temps) - 1):
                if self.temps[i] < oat < self.temps[i + 1]:
                    # Lineare Interpolation der Werte
                    t_low, t_high = self.temps[i], self.temps[i + 1]
                    v_low = calc_value(self.references[i])
                    v_high = calc_value(self.references[i + 1])
                    calculated = v_low + (v_high - v_low) * (oat - t_low) / (t_high - t_low)
                    break

        return calculated

    def set_volume_air_WW(self, oat, power):
        vol_rel_to_heating = self.set_volume_WW_factor
        return vol_rel_to_heating * self.set_volume_air(oat, power)


# 2. Referenz-Koeffizienten (OAT, K0, K1)
references = [
    {"temp": -10, "K0": -1500, "K1": 400, "min": 16500, "max": 24000},  # Formel: K0 + K1*power
    {"temp": 2, "K0": 4000, "K1": 266.67, "min": 12000, "max": 24000},  # Formel: K0 + K1*power
    {"temp": 12, "K0": 4000, "K1": 200, "min": 12000, "max": 24000}  # Formel: 18000 - 100*power
]

FM2_AF_model = Airflow(15.0, 90.0, references, 1.2, 1.0)

if __name__ == "__main__":
    # 2. Referenz-Koeffizienten (OAT, K0, K1)
    references = [
        {"temp": -10, "K0": -1500, "K1": 400, "min": 16500, "max": 24000},  # Formel: K0 + K1*power
        {"temp": 2, "K0": 4000, "K1": 266.67, "min": 12000, "max": 24000},  # Formel: K0 + K1*power
        {"temp": 12, "K0": 4000, "K1": 200, "min": 12000, "max": 24000}  # Formel: 18000 - 100*power
    ]

    AF_model = Airflow(15.0, 90.0, references, 1.2, 1.0)
    print(AF_model.set_volume_air(-10, 50))
    print(AF_model.set_volume_air(2, 60))
    print(AF_model.set_volume_air(-18, 55))
    print(AF_model.set_volume_air(15, 20))
    print(AF_model.set_volume_air(-10, 42.0))
