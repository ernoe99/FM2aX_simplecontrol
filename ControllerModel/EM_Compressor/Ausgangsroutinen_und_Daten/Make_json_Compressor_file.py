from TurboCor import corrSH_PolyScroll
from CoolProp.CoolProp import PropsSI
import json

if __name__ == '__main__':
    VZN175 = corrSH_PolyScroll('VZN175 30 coefficients - 85 73 197 1EupdateApr2024FormatW.csv',
                               [30, 140])

    poly_data_175 = VZN175.poly_data[2, 9:159].astype(float).tolist()  # Convert NumPy array to a list

    polygons = [
        [(-30.0, 10.0), (-30.0, 40.0), (-10.0, 70.0), (0.0, 70.0), (0.0, 60.0), (15.0, 60.0), (15.0, 25.0),
         (0.0, 10.0), (-30.0, 10.0)],
        [(-30.0, 40.0), (-30.0, 53.0), (-23.0, 70.0), (-10.0, 70.0), (-30.0, 40.0)],
        [(-23.0, 70.0), (-15.0, 82.0), (0.0, 82.0), (0.0, 70.0), (-23.0, 70.0)],
        [(-0.0, 70.0), (0.0, 60.0), (15.0, 60.0), (15.0, 25.0), (20.0, 30.0), (20.0, 65.0), (15.0, 70.0),
         (-0.0, 70.0)],
        [(0.0, 70.0), (0.0, 82.0), (0.0, 82.0), (15.0, 82.0), (25.0, 70.0), (25.0, 35.0), (20.0, 30.0),
         (20.0, 65.0), (15.0, 70.0), (0.0, 70.0)],
        [(-30.0, 53.0), (-30.0, 60.0), (-23.0, 70.0), (-30.0, 53.0)]
    ]

    n1_values = [30.0, 50.0, 50.0, 50.0, 50.0, 90.0]
    n2_values = [140.0, 140.0, 120.0, 120.0, 100.0, 140.0]

    json_data_175 = {
        "poly_data": poly_data_175,
        "polygons": polygons,
        "n1_values": n1_values,
        "n2_values": n2_values
    }

    with open('VZN175.json', 'w') as f:
        json.dump(json_data_175, f, indent=4)

    print("Successfully wrote data to VZN175.json")

    # Repeat for VZN220
    VZN220 = corrSH_PolyScroll('VZN220_VI_Calculated_Poly_Jun24.csv', [30, 140])

    poly_data_220 = VZN220.poly_data[2, 9:159].astype(float).tolist()  # Convert NumPy array to a list

    json_data_220 = {
        "poly_data": poly_data_220,
        "polygons": polygons,
        "n1_values": n1_values,
        "n2_values": n2_values
    }

    with open('VZN220.json', 'w') as f:
        json.dump(json_data_220, f, indent=4)

    print("Successfully wrote data to VZN220.json")
