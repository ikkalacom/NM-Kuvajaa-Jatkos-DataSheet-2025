import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import interpolate
import csv

"""
Ohjelman käyttö:
---------------
Tämä ohjelma lukee kaksi CSV-tiedostoa, suodattaa tiettyjä koordinaatteja 
ja tallentaa tulokset uuteen CSV-tiedostoon. 

Ohjelmalle voidaan antaa komentoriviparametri `input1`, joka on kokonaisluku (esim. 0 tai 1).
Mikäli parametria ei anneta, oletusarvo on 0.

Esimerkki ajosta:
    python yhdistys4.py 1

Tiedostojen polut muodostuvat seuraavasti:
    - Input-tiedostot: ./TempFiles/SLS-chart-SLS-[input1]-1.csv ja ./TempFiles/SLS-chart-SLS-[input1]-2.csv
    - Output-tiedosto: ./TempFiles/SLS-chart-SLS-[input1].csv
"""

# Luetaan komentoriviparametri, oletuksena 0
input1 = int(sys.argv[1]) if len(sys.argv) > 1 else 0

def read_curve(filename):
    """Lukee CSV-tiedoston ja palauttaa x- ja y-koordinaatit listamuodossa."""
    data = pd.read_csv(filename, header=None)
    x = data.iloc[0, :].tolist()  # Ensimmäinen rivi: x-koordinaatit
    y = data.iloc[1, :].tolist()  # Toinen rivi: y-koordinaatit
    return x, y

def filter_coordinates(x, y, condition, select_best):
    """Suodattaa koordinaatit ehdon perusteella ja säilyttää parhaan pisteen."""
    valid_indices = [i for i in range(len(x)) if condition(x[i], y[i])]
    if not valid_indices:
        return x, y  # Ei löydetty sopivia pareja, palautetaan alkuperäiset

    best_index = min(valid_indices, key=lambda i: y[i]) if select_best == min else max(valid_indices, key=lambda i: y[i])

    new_x = [x[i] for i in range(len(x)) if i not in valid_indices or i == best_index]
    new_y = [y[i] for i in range(len(y)) if i not in valid_indices or i == best_index]

    return new_x, new_y

# Tiedostojen polut dynaamisesti input1-arvon perusteella
file1 = f'./TempFiles/SLS-chart-SLS-{input1}-1.csv'
file2 = f'./TempFiles/SLS-chart-SLS-{input1}-2.csv'

# Lue tiedot
x1, y1 = read_curve(file1)
x2, y2 = read_curve(file2)

# Suodatetaan x=0 ja y>0 (valitaan pienin y)
x1, y1 = filter_coordinates(x1, y1, lambda x, y: x == 0 and y > 0, min)
x2, y2 = filter_coordinates(x2, y2, lambda x, y: x == 0 and y > 0, min)

# Suodatetaan x=0 ja y<0 (valitaan suurin y)
x1, y1 = filter_coordinates(x1, y1, lambda x, y: x == 0 and y < 0, max)
x2, y2 = filter_coordinates(x2, y2, lambda x, y: x == 0 and y < 0, max)

# Lasketaan tarkastelupiste y-arvo
y_ref = (max(y1) + min(y1)) / 2

# Lasketaan tarkasteluvektori tark_y
rajat_y_min = min(y1[0], y2[0])
rajat_y_max = max(y1[-1], y2[-1])
rajat_y = (rajat_y_min, rajat_y_max)

# Yhdistetään y1 ja y2 tark-vektoriksi
tark = y1 + y2

# Järjestetään tark vektori suurimmasta pienimpään
tark_sorted = sorted(tark, reverse=True)

# Poistetaan tark_sorted vektorin arvot, jotka ovat suurempia kuin rajat_y_min ja pienempiä kuin rajat_y_max
tark_filtered = [val for val in tark_sorted if rajat_y_min >= val >= rajat_y_max]

# Poistetaan duplikaatit tark_filtered vektorista
tark_filtered_unique = list(dict.fromkeys(tark_filtered))

print(f"Suodatettu tark vektori (arvot rajojen sisällä ilman duplikaatteja): {tark_filtered_unique}")

def find_x_for_y(x, y, target_y):
    """Etsii x-koordinaatin, joka vastaa tiettyä y-arvoa käyrällä."""
    f = interpolate.interp1d(y, x, kind="linear", fill_value="extrapolate")
    return f(target_y)

# Läpi tark_filtered_unique vektori ja lasketaan x-arvot
x_coords = []
for target_y in tark_filtered_unique:
    x1_at_y = find_x_for_y(x1, y1, target_y)
    x2_at_y = find_x_for_y(x2, y2, target_y)
    
    if x1_at_y < x2_at_y:
        x_coords.append(x1_at_y)
    else:
        x_coords.append(x2_at_y)

# Kirjoitetaan tiedostoon dynaamisella nimellä
output_filename = f'./TempFiles/SLS-chart-SLS-{input1}.csv'

with open(output_filename, 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(x_coords)
    writer.writerow(tark_filtered_unique)

print(f"Tiedosto tallennettu nimellä: {output_filename}")

# Piirretään käyrät ja tulokset
plt.plot(x1, y1, label="Käyrä 1", marker="o")
plt.plot(x2, y2, label="Käyrä 2", marker="s")

# Piirretään x-koordinaatit ja tark_filtered_unique arvot
plt.scatter(x_coords, tark_filtered_unique, color="red", label="Tarkastelupisteet", zorder=5)

plt.xlabel("X")
plt.ylabel("Y")
plt.legend()
plt.title("Tarkastelupisteet käyrillä")
plt.show()
