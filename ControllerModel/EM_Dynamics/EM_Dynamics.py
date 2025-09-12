import time


# --- Platzhalter-Klassen für fehlende Routinen ---

class EM_Compressor:
    """
    Simuliert die 'predict'-Funktion eines Kompressors.
    Diese Klasse dient als Platzhalter und muss durch die reale
    Implementierung ersetzt werden.
    """

    def predict(self, P_app, T_ambient, humidity):
        """
        Simuliert die Vorhersage von Drehzahl und EXV-Öffnung.

        :param P_app: Aktuelle thermische Leistungsvorgabe in kW
        :param T_ambient: Außentemperatur in °C
        :param humidity: Luftfeuchtigkeit in %
        :return: Ein Tupel (speed, exv_opening)
        """
        # Annahme: Einfache lineare Beziehung zur Simulation
        speed = 50 + (P_app * 2)
        exv_opening = 30 + (P_app * 0.5)
        return speed, exv_opening

    def predict_p_app(self, P_el_max=None, P_soll=None):
        """
        Simuliert die Umrechnung von elektrischer/thermischer Leistung in P_app.

        :param P_el_max: Maximale elektrische Leistungsaufnahme in kW
        :param P_soll: Gewünschte thermische Leistung in kW
        :return: Berechneter P_app Wert
        """
        if P_soll is not None:
            # Annahme: COP = 3.0 für die Simulation
            return P_soll
        elif P_el_max is not None:
            # Annahme: COP = 3.0 für die Simulation
            return P_el_max * 3.0
        return 0.0


class EM_Cascade:
    """
    Platzhalter für die Kaskaden-Steuerung.
    """

    def update(self, speed, exv_opening):
        """
        Empfängt die neuen Sollwerte und gibt sie aus.
        """
        print(f"--- EM_Cascade: Neue Stellgrößen erhalten ---")
        print(f"Drehzahl: {speed:.2f} rps")
        print(f"EXV-Stellung: {exv_opening:.2f} %")


# --- EM_Dynamics Klasse ---

class EM_Dynamics:
    def __init__(self, Ktime=5.0):
        """
        Initialisiert die Routine für die dynamische Leistungssteuerung.

        :param Ktime: Zeitkonstante für die dynamische Anpassung.
                      Kleinerer Wert bedeutet schnellere Reaktion.
        """
        self.Ktime = Ktime
        self.previous_P_app = 0.0
        self.compressor = EM_Compressor()
        self.cascade = EM_Cascade()

    def run(self, T_rl_ist, T_ambient, humidity, P_el_max=None, P_soll=None):
        """
        Führt die dynamische Leistungsregelung aus.

        :param T_rl_ist: Aktuelle Rücklauftemperatur
        :param T_ambient: Aktuelle Außentemperatur
        :param humidity: Aktuelle Feuchtigkeit
        :param P_el_max: (Optional) Maximale elektrische Leistungsaufnahme
        :param P_soll: (Optional) Gewünschte thermische Leistung
        """
        print("\n--- EM_Dynamics: Lauf gestartet ---")

        # 1. Iterative Berechnung von P_soll oder P_el_max zu P_app
        #    Die iterative Berechnung wird hier simuliert, da sie eine komplexere
        #    Logik erfordert, die über den Rahmen dieser Routine hinausgeht.
        P_soll_target = self.compressor.predict_p_app(P_el_max=P_el_max, P_soll=P_soll)

        # 2. Berechnung des Leistungsdefizits/Überschusses
        #    Der Überschuss/das Defizit wird hier vereinfacht als die Differenz zwischen
        #    der dynamischen Leistungsvorgabe und dem Sollwert berechnet.
        power_error = P_soll_target - self.previous_P_app

        # 3. Dynamische Anpassung mit Zeitkonstante Ktime
        #    Diese Formel simuliert einen I-Anteil für die dynamische Anpassung.
        P_app_dynamic = self.previous_P_app + power_error / self.Ktime

        # Begrenzung des Wertes, um eine realistische Spanne zu gewährleisten
        P_app_dynamic = max(0.0, P_app_dynamic)

        self.previous_P_app = P_app_dynamic

        # 4. Prognose der Stellgrößen (speed, exv_opening)
        speed, exv_opening = self.compressor.predict(P_app_dynamic, T_ambient, humidity)

        # 5. Weitergabe an EM_Cascade
        self.cascade.update(speed, exv_opening)

        print(f"Aktuelle dynamische P_app: {P_app_dynamic:.2f} kW")


if __name__ == "__main__":
    dynamics = EM_Dynamics(Ktime=5.0)

    # Szenario 1: Ziel ist P_soll = 10 kW
    dynamics.run(T_rl_ist=40, T_ambient=10, humidity=60, P_soll=10)
    # Simulation des nächsten Zeitschritts
    dynamics.run(T_rl_ist=38, T_ambient=10, humidity=60, P_soll=10)

    # Szenario 2: Ziel ist P_el_max = 5 kW
    dynamics.run(T_rl_ist=45, T_ambient=10, humidity=60, P_el_max=5)
    # Simulation des nächsten Zeitschritts
    dynamics.run(T_rl_ist=46, T_ambient=10, humidity=60, P_el_max=5)