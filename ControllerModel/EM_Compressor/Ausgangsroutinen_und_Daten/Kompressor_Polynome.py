import numpy as np

from TurboCor import corrSH_PolyScroll


def calculate_direct(speed, t_suction, t_condensation, poly_data):
    """Berechnung der Heizparameter mit polynomialen Koeffizienten"""

    # Helper-Funktion für die wiederkehrende Berechnung
    def calculate_component(il, co, speed, t_suc, t_con, data):
        # Array-Indizes an Python (0-basiert) anpassen
        # il -= 1
        # co -= 1

        base = float(data[il][co])
        + data[il][co + 1] * t_suc
        + data[il][co + 2] * t_con
        + data[il][co + 3] * t_suc ** 2
        + data[il][co + 4] * t_con ** 2

        term1 = t_suc * t_con * (
                (speed ** 2) * (data[il][co + 5] + data[il][co + 6] * t_suc + data[il][co + 7] * t_con) +
                speed * (data[il][co + 8] + data[il][co + 9] * t_suc + data[il][co + 10] * t_con) +
                data[il][co + 11] + data[il][co + 12] * t_suc + data[il][co + 13] * t_con
        )

        term2 = data[il][co + 14] * t_suc ** 3 + data[il][co + 15] * t_con ** 3

        term3 = speed * (
                data[il][co + 16]
                + data[il][co + 17] * t_suc
                + data[il][co + 18] * t_con
                + data[il][co + 19] * t_suc ** 2
                + data[il][co + 20] * t_con ** 2
                + data[il][co + 21] * t_suc ** 3
                + data[il][co + 22] * t_con ** 3
        )

        term4 = speed ** 2 * (
                data[il][co + 23]
                + data[il][co + 24] * t_suc
                + data[il][co + 25] * t_con
                + data[il][co + 26] * t_suc ** 2
                + float(data[il][co + 27]) * t_con ** 2
                + float(data[il][co + 28]) * t_suc ** 3
                + float(data[il][co + 29]) * t_con ** 3
        )

        return base + term1 + term2 + term3 + term4

    # Hauptberechnungen
    capacity = calculate_component(2, 9, speed, t_suction, t_condensation, poly_data)
    epower = calculate_component(1, 39, speed, t_suction, t_condensation, poly_data)
    ecurrent = calculate_component(2, 69, speed, t_suction, t_condensation, poly_data)
    comppower = calculate_component(2, 39, speed, t_suction, t_condensation, poly_data)
    massflow = calculate_component(2, 99, speed, t_suction, t_condensation, poly_data)
    Tdischarge = calculate_component(2, 129, speed, t_suction, t_condensation, poly_data)

    # Endberechnungen
    qheat = capacity + comppower
    cop = qheat / epower if epower != 0 else 0
    invpower = epower - comppower

    return np.array([qheat, epower, massflow, ecurrent, capacity, cop, Tdischarge, invpower])


if __name__ == '__main__':
    VZN175 = corrSH_PolyScroll('VZN175 30 coefficients - 85 73 197 1EupdateApr2024FormatW.csv',
                               [30, 140])  # Update Danfoss April 2024 Danfoss Polynome
    # VZN220 = corrSH_PolyScroll('../VZN220_VI_Calculated_Poly_Jun24.csv', [30, 140])  # Danfoss June 2024 Danfoss P
    # Beispiel-Datenstruktur (nur zur Demonstration)
    poly_data = VZN175.poly_data

    result = calculate_direct(
        speed=50.0,
        t_suction=-2.0,
        t_condensation=32.1,
        poly_data=poly_data
    )

    print(f"Heizleistung: {result[0]:.2f} kW")
    print(f"COP: {result[5]:.2f}")
