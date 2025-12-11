"""
Lyhyt kuvaus:
Tämä ohjelma tarjoaa graafisen käyttöliittymän, jonka avulla käyttäjä voi valita Mathcad-työkirjan, määrittää laskennan aloitus- ja lopetusarvot sekä käynnistää Mathcad Prime -automaation. 
Ohjelma käyttää Tkinteria käyttöliittymän toteuttamiseen ja win32com-komponenttia Mathcad Prime -sovelluksen ohjaamiseen. 
Se iteroi syötearvoja, asettaa ne Mathcad-työkirjaan, lukee laskutulokset, näyttää etenemisen progressbarissa ja sulkee sovelluksen lopuksi.

Cheese FIle valitaan ajettava Mathcad-työkirja, joka sisältää laskentatehtävän.
Start Value ja End Value määrittävät laskentatehtävän syötearvojen aloitus- ja lopetusarvot. Nämä arvot syötetään käyttöliittymän Entry-widgettiin ja laskenta suoritetaan näiden arvojen perusteella.


Yksityiskohtainen kuvaus:
1. Kirjastojen tuonti ja globaalit muuttujat:
   - Ohjelma tuo tarvittavat kirjastot: 'os' tiedostopolkujen käsittelyyn, 'tkinter' sekä sen widgetit käyttöliittymän rakentamiseen, 'ttk.Progressbar' etenemisen näyttämiseen, sekä 'win32com.client.Dispatch' Mathcad Prime -sovelluksen ohjaamiseen COM-automaation avulla.
   - Muuttuja 'worksheet_path' alustetaan tallentamaan valitun Mathcad-työkirjan sijainnin.

2. Apufunktio 'msg(m)':
   - Funktio 'msg' vastaa viestien näyttämisestä sekä käyttöliittymässä (result_label) että komentorivillä, jotta käyttäjä näkee reaaliaikaiset tiedot ohjelman suorituksesta.

3. Tiedoston valinta 'choose_file()':
   - Tämä funktio avaa tiedostonvalintadialogin, josta käyttäjä voi valita Mathcad-tiedoston (.mcdx).
   - Valitun tiedoston nimi ja sijainti tallennetaan muuttujaan 'worksheet_path' ja näytetään käyttöliittymässä, jotta käyttäjä tietää, mikä tiedosto on valittu.

4. Mathcad-toiminnon suorittaminen 'run_mathcad()':
   - Funktiossa haetaan käyttöliittymästä laskennassa käytettävät aloitus- ja lopetusarvot.
   - Mathcad Prime käynnistetään COM-automaatiolla, ja sen näkyvyys määritetään käyttäjän valinnan mukaan.
   - Valittu työskirja avataan Mathcad Prime -sovelluksessa; sen jälkeen asetetaan työskirjan otsikko.
   - Ohjelma noutaa työskirjan syöte- ja tulostekohdat sekä suorittaa silmukan, jossa se muuttaa ensimmäisen syötteen arvoa annetulla arvovälillä, lukee kunkin iteraation laskutuloksen ja näyttää sen käyttöliittymässä.
   - Progressbaria päivitetään dynaamisesti silmukan edetessä, ja lopuksi Mathcad Prime suljetaan ja ohjelman suoritussilmukka päättyy.

5. Ohjelman sulkeminen 'close_program()' sekä käyttöliittymän rakentaminen:
   - 'close_program()'-funktio vastaa Tkinter-ikkunan sulkemisesta, jolloin ohjelman suoritus päättyy.
   - Käyttöliittymä rakennetaan Tkinterin avulla, ja siinä on widgettejä (Label, Button, Entry, Checkbutton, Progressbar) tiedoston valintaan, tulosten näyttämiseen, laskennan arvojen syöttämiseen ja suorituksen ohjaamiseen.
   - Lopuksi 'root.mainloop()' käynnistää käyttöliittymän tapahtumasilmukan, joka pitää ikkunan aktiivisena, kunnes käyttäjä haluaa sulkea sen.
"""


import os, runpy
from tkinter import Tk, Button, Label, filedialog, Entry, Frame, Checkbutton, BooleanVar
from tkinter.ttk import Progressbar
from win32com.client import Dispatch

# Global variables
worksheet_path = None
python_script_path = None  # Valittavan .py-tiedoston polku


def msg(m):
    # This function displays messages in the UI
    result_label.config(text=m)
    print(m)

def choose_file():
    global worksheet_path
    # File selection dialog
    worksheet_name = filedialog.askopenfilename(
        title="Select Mathcad File",
        initialdir=dir_script,  # Set the directory of the script
        filetypes=[("Mathcad Files", "*.mcdx")]
    )

    if worksheet_name:
        worksheet_path = os.path.join(dir_script, os.path.basename(worksheet_name))
        file_label.config(text=f"Selected file: {os.path.basename(worksheet_path)}")
    else:
        file_label.config(text="No file selected.")

def choose_python_file():
    global python_script_path
    selected_file = filedialog.askopenfilename(
        title="Select Python Script",
        initialdir=dir_script,
        filetypes=[("Python Files", "*.py")]
    )
    if selected_file:
        python_script_path = selected_file
        python_file_label.config(text=f"Python: {os.path.basename(python_script_path)}")
    else:
        python_script_path = None
        python_file_label.config(text="No Python file selected.")



def run_mathcad():
    global worksheet_path
    if worksheet_path:
        try:
            start_value = int(start_entry.get())
            end_value = int(end_entry.get())

            # Loop through input values in the specified range
            for value in range(start_value, end_value + 1):
                msg(f"Opening Mathcad for Input value: {value}")
                
                # Käynnistä Mathcad Prime
                mathcad = Dispatch("MathcadPrime.Application")
                mathcad.Visible = visible_var.get()
                mathcad.Activate()

                # Avaa laskentalehti
                worksheet = mathcad.Open(worksheet_path)
                if not worksheet:
                    msg(f"Failed to open file: {worksheet_path}")
                    mathcad.Quit(2)
                    continue

                worksheet.SetTitle("Title from Python Script")

                # Syötearvon asetus
                inputs = worksheet.Inputs
                first_input = inputs.GetAliasByIndex(0)
                worksheet.SetRealValue(first_input, value, "")

                # Tulosarvon lukeminen
                outputs = worksheet.Outputs
                first_output = outputs.GetAliasByIndex(0)
                val = worksheet.OutputGetRealValue(first_output)

                if val:
                    real_result = val.RealResult
                    units = val.Units
                    msg(f"For Input value {value}, Output1 = {real_result} {units}")
                else:
                    msg(f"No result for input {value}")

                # Aja valittu Python-skripti, jos määritelty
                if python_script_path:
                    try:
                        msg(f"Running script: {os.path.basename(python_script_path)}")
                        runpy.run_path(python_script_path, run_name="__main__")
                    except Exception as ex:
                        msg(f"Error in script: {ex}")

                # Sulje Mathcad
                msg("Closing Mathcad Prime...")
                mathcad.CloseAll(0)
                mathcad.Quit(2)

                # Progress bar päivitys
                progress['value'] = (value - start_value) / (end_value - start_value) * 100
                root.update_idletasks()

        except Exception as e:
            msg(f"An error occurred: {e}")


def close_program():
    root.quit()

# Create the main window
root = Tk()
root.title("Mathcad Prime Automation")

# Set the script path so the file can be selected correctly
script_path = os.path.abspath(__file__)
dir_script = os.path.dirname(script_path)

# Display selected file name
file_label = Label(root, text="Select Mathcad file", width=40, height=2)
file_label.pack(padx=10, pady=10)

# Button to choose file
file_button = Button(root, text="Choose File", command=lambda: choose_file())
file_button.pack(pady=10)

# Display messages during execution
result_label = Label(root, text="", width=60, height=5, anchor="w", justify="left", relief="solid")
result_label.pack(padx=10, pady=10)

# Progress bar
progress = Progressbar(root, orient="horizontal", length=300, mode="determinate")
progress.pack(pady=10)

# Start and end values
start_label = Label(root, text="Start Value:")
start_label.pack(pady=5)
start_entry = Entry(root)
start_entry.insert(0, "1")  # Default value
start_entry.pack(pady=5)

end_label = Label(root, text="End Value:")
end_label.pack(pady=5)
end_entry = Entry(root)
end_entry.insert(0, "10")  # Default value
end_entry.pack(pady=5)

# Checkbutton for Mathcad visibility
visible_var = BooleanVar(value=False)  # Default is False (not visible)
visibility_check = Checkbutton(root, text="Show Mathcad Window", variable=visible_var)
visibility_check.pack(pady=5)

# Frame for Run and End buttons
button_frame = Frame(root)
button_frame.pack(pady=20)

# Button to start the Mathcad loop
run_button = Button(button_frame, text="Run", command=run_mathcad)
run_button.pack(side="left", padx=10)

# Button to close the program
end_button = Button(button_frame, text="End", command=close_program)
end_button.pack(side="left", padx=10)

# Näytä valittu Python-tiedosto
python_file_label = Label(root, text="No Python file selected.", width=40, height=2)
python_file_label.pack(padx=10, pady=(10, 0))

# Napin valinta Python-tiedostolle
python_file_button = Button(root, text="Choose Python File", command=choose_python_file)
python_file_button.pack(pady=10)


# Start the UI
root.mainloop()
