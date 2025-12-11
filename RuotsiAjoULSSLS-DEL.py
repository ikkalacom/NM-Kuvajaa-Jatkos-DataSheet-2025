import csv
import os
import subprocess
import time

# 1. Luetaan results.csv ja otetaan toinen sarake (arvo TestName-muuttujaan)
with open("./TempFiles/result.csv", newline='', encoding="utf-8") as f:
    reader = csv.reader(f)
    row = next(reader)  # esim. ["TestName", "235-104 4D20-660"]
    TestName = row[1]
print("TestName:", TestName)

# 2. Avataan SLS-chart-SLS-0.csv (tässä esimerkissä luetaan sama tiedosto kahdesti)
chart_files = ["./TempFiles/SLS-chart-SLS-0.csv", "./TempFiles/SLS-chart-SLS-1.csv"]
output_chart_file = f"./TempFiles/{TestName}-chart.csv"

# Jos kohdetiedosto on jo olemassa, säilytetään sen nykyinen sisältö
if os.path.exists(output_chart_file):
    with open(output_chart_file, "r", encoding="utf-8") as f:
        existing_content = f.read()
else:
    existing_content = ""

# Avataan kohdetiedosto kirjoitustilassa ja liitetään siihen nykyinen sisältö sekä uusien chart-tiedostojen sisältö
with open(output_chart_file, "w", encoding="utf-8") as f_out:
    # Kirjoitetaan ensin vanha sisältö (jos sellainen on)
    f_out.write(existing_content)
    # Lisätään jokaisen chart-tiedoston sisältö
    for chart_file in chart_files:
        with open(chart_file, "r", encoding="utf-8") as f_chart:
            content = f_chart.read()
            # Lisätään rivinvaihto ennen uuden tiedoston sisällön liittämistä
            #f_out.write("\n")
            f_out.write(content)

# 3. Luetaan SLS-data-1.csv, josta otetaan korvaavat arvot
data_values = {}
with open("./TempFiles/SLS-data-1.csv", newline='', encoding="utf-8") as f: #muokkaa tähän SLS-data-1-1.csv jos ei ole normi symmetrinen
    reader = csv.reader(f)
    for row in reader:
        # Esim. rivi: ["NmaxSLS", "1684.7"]
        key, value = row[0], row[1]
        data_values[key] = value

# Avataan TestName.csv, jonka nimi on esim. "235-104 4D20-660.csv", ja päivitetään kohdissa "NmaxSLS", "NminSLS" ja "NMmaxSLS"
testname_csv_file = f"./TempFiles/{TestName}.csv"

# Luetaan alkuperäinen CSV sisältö listaksi
rows = []
with open(testname_csv_file, newline='', encoding="utf-8") as f:
    reader = csv.reader(f)
    rows = list(reader)

# Päivitetään rivit, joissa arvo on -1 ja avaimena on jokin data_values-sanakirjan avain
for row in rows:
    if row[0] in data_values and row[1] == "-1":
        row[1] = data_values[row[0]]

# Kirjoitetaan päivitetty sisältö takaisin samaan tiedostoon
with open(testname_csv_file, "w", newline='', encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerows(rows)
# 4. Ajetaan datasheetSLS.py samassa kansiossa
subprocess.run(["python", "./datasheetSLS.py"])

# 5. Deletoidaan kaikki temp-kansiossa olevat tiedostot
temp_folder = "./TempFiles"

for filename in os.listdir(temp_folder):
    file_path = os.path.join(temp_folder, filename)
    try:
        if os.path.isfile(file_path) or os.path.islink(file_path):
            os.unlink(file_path)  # Poistaa tiedoston tai linkin
        elif os.path.isdir(file_path):
            import shutil
            shutil.rmtree(file_path)  # Poistaa kansion ja sen sisällön
    except Exception as e:
        print(f"Virhe poistettaessa tiedostoa {file_path}: {e}")
