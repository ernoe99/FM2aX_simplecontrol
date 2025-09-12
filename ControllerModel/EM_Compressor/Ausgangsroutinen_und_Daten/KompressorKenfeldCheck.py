from typing import List, Tuple

# Definition eines Punktes als Tuple (x, y)
Point = Tuple[float, float]


def check_polygon(Tevaporation: float, Tcondensing: float, polygons: List[List[Point]], n1_values: List[float],
                  n2_values: List[float]) -> Tuple[bool, float, float]:
    """
    Überprüft, ob der Punkt [Tevaporation, Tcondensing] innerhalb eines der Polygone liegt.
    Gibt die zugehörigen n1- und n2-Werte zurück, falls der Punkt in einem Polygon liegt.

    :param Tevaporation: x-Koordinate des Punkts
    :param Tcondensing: y-Koordinate des Punkts
    :param polygons: Liste der Polygone (jedes Polygon ist eine Liste von Punkten)
    :param n1_values: Liste der n1-Werte für jedes Polygon
    :param n2_values: Liste der n2-Werte für jedes Polygon
    :return: (True, n1, n2) wenn der Punkt in einem Polygon liegt, sonst (False, 0.0, 0.0)
    """
    x, y = Tevaporation, Tcondensing

    for i, polygon in enumerate(polygons):
        inside = False
        num_points = len(polygon)

        # Ray-Casting-Algorithmus
        j = 0
        k = num_points - 1  # Letzter Punkt im Polygon

        while j < num_points:
            # Koordinaten der aktuellen Kante
            x1, y1 = polygon[j]
            x2, y2 = polygon[k]

            # Überprüfe, ob die Kante die horizontale Linie schneidet
            if ((y1 > y) != (y2 > y)) and (x < (x2 - x1) * (y - y1) / (y2 - y1) + x1):
                inside = not inside  # Schnittpunkt gefunden

            k = j  # Aktualisiere den letzten Punkt
            j += 1  # Gehe zum nächsten Punkt

        # Wenn der Punkt im Polygon liegt, gebe die zugehörigen n1 und n2 zurück
        if inside:
            return True, n1_values[i], n2_values[i]

    # Punkt liegt in keinem Polygon
    return False, 0.0, 0.0


# Beispielaufruf
if __name__ == "__main__":
    # Beispiel-Polygone (jedes Polygon ist eine Liste von Punkten)
    polygons = [
        [(-30.0, 10.0), (-30.0, 40.0), (-10.0, 70.0), (0.0, 70.0), (0.0, 60.0), (15.0, 60.0), (15.0, 25.0),
         (0.0, 10.0), (-30.0, 10.0)],  # Polygon 1  30 - 140 rps
        [(-30.0, 40.0), (-30.0, 53.0), (-23.0, 70.0), (-10.0, 70.0), (-30.0, 40.0)], # Polygon 2  50 - 140 rps
        [(-23.0, 70.0), (-15.0, 82.0), (0.0, 82.0), (0.0, 70.0), (-23.0, 70.0)],  # Polygon 3  50 - 120 rps
        [(-0.0, 70.0), (0.0, 60.0), (15.0, 60.0), (15.0, 25.0), (20.0, 30.0), (20.0, 65.0), (15.0, 70.0),
         (-0.0, 70.0)],  # Polygon 4  50 - 120 rps
        [(0.0, 70.0), (0.0, 82.0), (0.0, 82.0), (15.0, 82.0), (25.0, 70.0), (25.0, 35.0), (20.0, 30.0),
         (20.0, 65.0), (15.0, 70.0), (0.0, 70.0)],  # Polygon 5  50 - 100 rps
        [(-30.0, 53.0), (-30.0, 60.0), (-23.0, 70.0), (-30.0, 53.0)]  # Polygon 6  90 - 140 rps wet area
        # Weitere Polygone können hier hinzugefügt werden
    ]

    # Beispielwerte für n1 und n2
    n1_values = [30.0, 50.0, 50.0, 50.0, 50.0, 90.0]  # n1-Werte für jedes Polygon
    n2_values = [140.0, 140.0, 120.0, 120.0, 100.0, 140.0]  # n2-Werte für jedes Polygon

    # Testpunkt
    Tevaporation = -30.0
    Tcondensing = 53.0

    # Überprüfe, ob der Punkt in einem Polygon liegt
    result, n1, n2 = check_polygon(Tevaporation, Tcondensing, polygons, n1_values, n2_values)

    if result:
        print(f"Der Punkt liegt in einem Polygon. n1 = {n1}, n2 = {n2}")
    else:
        print("Der Punkt liegt in keinem Polygon.")
