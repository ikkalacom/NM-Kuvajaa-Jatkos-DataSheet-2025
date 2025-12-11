import csv
import os
import matplotlib.pyplot as plt
from matplotlib import rcParams, font_manager
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from pdfrw import PdfReader, PdfWriter, PageMerge
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
import io
from datetime import datetime  # Import datetime module

# Asetetaan Open Sans -fontit kansiosta
FONT_DIR = './font'
OPEN_SANS_REGULAR = os.path.join(FONT_DIR, 'OpenSans-Regular.ttf')
OPEN_SANS_BOLD = os.path.join(FONT_DIR, 'OpenSans-Bold.ttf')

if os.path.exists(OPEN_SANS_REGULAR):
    prop = font_manager.FontProperties(fname=OPEN_SANS_REGULAR)
    rcParams['font.family'] = prop.get_name()
else:
    print("Open Sans Regular -fonttia ei löydy kansiosta. Käytetään oletusfonttia.")

def read_csv_file(file_name):
    if not os.path.exists(file_name):
        raise FileNotFoundError(f"Tiedostoa ei löydy: {file_name}")
    with open(file_name, mode='r', encoding='utf-8') as file:
        reader = csv.reader(file)
        data = [row for row in reader]
    return data

def parse_variable_values(data):
    variables = {}
    for row in data:
        if len(row) == 2:
            key = row[0].strip()
            value = row[1].strip()
            try:
                value = float(value)
                if value.is_integer():
                    value = int(value)
            except ValueError:
                pass
            variables[key] = value
    return variables

def plot_charts(chart_data, variables, show_plot=False, file_extension="png"):
    plt.figure(figsize=(10, 6))
    plt.plot(chart_data["ChartDirect"]["x"], chart_data["ChartDirect"]["y"], 
             label=variables.get("Kuvaaja1", "ChartDirect"), linestyle='-')
    plt.plot(chart_data["ChartBidirect"]["x"], chart_data["ChartBidirect"]["y"], 
             label=variables.get("Kuvaaja2", "ChartBidirect"), linestyle='--')
    plt.title(variables.get("Nimi", "Kuvaaja"))
    plt.xlabel("Moment [kNm]")
    plt.ylabel("Normal force [kN]")
    plt.legend()
    plt.grid(True)

    output_file = f"./TempFiles/kuvaaja.{file_extension}"
    plt.savefig(output_file)
    print(f"Kuvaaja tallennettu tiedostoon: {output_file}")

    if show_plot:
        plt.show()
    else:
        plt.close()

def add_text_and_image_to_pdf(pdf_file, texts, images, output_pdf):
    input_pdf = PdfReader(pdf_file)
    writer = PdfWriter()
    page = input_pdf.pages[0]

    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=A4)

    # Rekisteröi fontit Reportlabille
    if os.path.exists(OPEN_SANS_REGULAR):
        pdfmetrics.registerFont(TTFont('OpenSans-Regular', OPEN_SANS_REGULAR))
    if os.path.exists(OPEN_SANS_BOLD):
        pdfmetrics.registerFont(TTFont('OpenSans-Bold', OPEN_SANS_BOLD))

    # Lisää tekstit
    for text_info in texts:
        font_type = text_info.get('font', 'OpenSans-Regular')
        font_size = text_info.get('size', 10)
        c.setFont(font_type, font_size)

        text = text_info['text']
        if '_{' in text and '}' in text:  # Tarkistetaan, sisältääkö teksti alaindeksin
            # Etsitään alaindeksin alku ja loppu
            base_text, subscript_text = text.split('_{', 1)  # Jaa ensimmäisestä { merkistä
            subscript_text = subscript_text.split('}', 1)[0]  # Poista }-merkki alaindeksistä

            # Piirrä pääteksti
            c.drawString(text_info['x'], text_info['y'], base_text)

            # Pienennä fonttikokoa alaindeksille ja piirrä se
            c.setFont("Helvetica", font_size - 2)  # Pienennetty fonttikoko alaindeksille
            c.drawString(text_info['x'] + c.stringWidth(base_text, "Helvetica", font_size), text_info['y'], subscript_text)

            # Palataan normaaliin fonttiin
            c.setFont(font_type, font_size)

            # Tulostetaan jäljellä oleva normaali teksti, jos sellaista on
            remaining_text = text.split('}', 1)[1:]  # Jäljelle jäävä osa normaalina tekstinä
            if remaining_text:
                c.drawString(text_info['x'] + c.stringWidth(base_text + subscript_text, "Helvetica", font_size), text_info['y'], remaining_text[0])

        else:
            # Jos ei ole alaindeksiä, piirrä normaali teksti
            c.drawString(text_info['x'], text_info['y'], text)

    # Lisää kuvat
    for image_info in images:
        c.drawImage(image_info['image'], image_info['x'], image_info['y'], 
                    width=image_info['width'], height=image_info['height'])

    c.showPage()
    c.save()

    packet.seek(0)
    new_pdf = PdfReader(packet)
    overlay_page = new_pdf.pages[0]

    PageMerge(page).add(overlay_page).render()
    writer.addpage(page)

    output_pdf = f"{output_pdf}.pdf"
    with open(output_pdf, "wb") as output:
        writer.write(output)
    print(f"PDF-tiedosto tallennettu: {output_pdf}")


def parse_chart_data(data):
    chart_data = {
        "ChartDirect": {"x": [], "y": []},
        "ChartBidirect": {"x": [], "y": []}
    }
    if len(data) >= 4:
        chart_data["ChartDirect"]["x"] = [float(x) for x in data[0]]
        chart_data["ChartDirect"]["y"] = [float(y) for y in data[1]]
        chart_data["ChartBidirect"]["x"] = [float(x) for x in data[2]]
        chart_data["ChartBidirect"]["y"] = [float(y) for y in data[3]]
    return chart_data

def main():
    results_data = read_csv_file('./TempFiles/result.csv')
    if not results_data:
        raise ValueError("result.csv on tyhjä tai sitä ei voi lukea.")
    first_row = results_data[0]

    test_name = first_row[0].strip()
    test_file_name = './TempFiles/'+first_row[1].strip() + '.csv'

    if not os.path.exists(test_file_name):
       raise FileNotFoundError(f"Testitiedostoa ei löydy: {test_file_name}")
    
    test_data = read_csv_file(test_file_name)

    variables = parse_variable_values(test_data)

    for var_name, var_value in variables.items():
        print(f"{var_name}: {var_value}")

    chart_file_name = './TempFiles/'+ first_row[1].strip() + '-chart.csv'
    if not os.path.exists(chart_file_name):
        raise FileNotFoundError(f"Käyrätiedostoa ei löydy: {chart_file_name}")
    
    chart_data = read_csv_file(chart_file_name)
    parsed_chart_data = parse_chart_data(chart_data)

    plot_charts(parsed_chart_data, variables, show_plot=False, file_extension="png")

    # Hanki nykyinen päivämäärä
    current_date = datetime.now().strftime("%d.%m.%Y")  # Muoto: pp.kk.vvvv

    # X-koordinaatti muuttujana
    base_x = 315  # Voit muuttaa tätä arvoa siirtääksesi kaikki rivit vaakasuunnassa
    base_x2 = base_x + 180
    myySt = variables.get("myyS")
    myyCt = variables.get("myyC")
    kuva = variables.get("Kuva")

    #Muuttuja jolla ohjataan näytetäänkö myyt
    myyT= 1 if myySt < 1 or myyCt < 1 else 0
    # myyT=1 #Aina näytetään myyt

    #Muuttujat joilla ohjataan lukkojen 2 näyttämistä
    lock2T = 0 if str(variables.get("lv2")) == "0.0" else 1
    # lock2T = 1 #Aina näytetään lukko2

    #Muuttuja jolla ohjataan näytetäänkö rbeff   
    rbeffT = 0 if variables.get("fiieff") == variables.get("fii") else 1
    # rbeffT = 1 #Aina näytetään rbeff

    #Muuttuja jolla ohjataan näytetäänkö RebatL

    LrbT = 0 if variables.get("Lrb") == 0 else 1





    # PDF tiedostoon kirjoitettavat tekstit
    texts_to_add = [
        {"text": variables.get("Nimi"), "x": 40, "y": 700, "font": "OpenSans-Bold", "size": 12},  # Open Sans Bold koko 12
            # Open Sans Regular koko 10 - rivitetty teksti
    # Open Sans Regular koko 10 - rivitetty teksti
    
        {"text": "Dimensions and parameters:", "x": base_x, "y": 695, "font": "OpenSans-Bold", "size": 10},
        {"text": "Joint side length b [mm]", "x": base_x, "y": 680, "font": "OpenSans-Regular", "size": 10},
        {"text": "Lock 1 distance lv1 [mm]", "x": base_x, "y": 665, "font": "OpenSans-Regular", "size": 10},
        #{"text": "Lock 2 distance lv2 [mm]", "x": base_x, "y": 650, "font": "OpenSans-Regular", "size": 10},
        #{"text": "Rebar length Lrb [mm]", "x": base_x, "y": 635, "font": "OpenSans-Regular", "size": 10},
        {"text": "Rebar diameter Φ [mm]", "x": base_x, "y": 620, "font": "OpenSans-Regular", "size": 10},
        #{"text": "Rebar effective diameter Φ  _{eff} [mm]", "x": base_x, "y": 605, "font": "OpenSans-Regular", "size": 10},
        {"text": "F_{yk} [MPa] (EN 1992-1-1)", "x": base_x, "y": 590, "font": "OpenSans-Regular", "size": 10},
        {"text": "F_{ck} [MPa] (EN 206-1, EN 1992-1-1)", "x": base_x, "y": 575, "font": "OpenSans-Regular", "size": 10},
        {"text": "α_{cc} (EC 2 (3.1.6 (1)))", "x": base_x, "y": 560, "font": "OpenSans-Regular", "size": 10},
        {"text": "γ_{c} (EC 2 (2.4.2.4))", "x": base_x, "y": 545, "font": "OpenSans-Regular", "size": 10},
        {"text": "γ_{s} (EC 2 (2.4.2.4))", "x": base_x, "y": 530, "font": "OpenSans-Regular", "size": 10},
        {"text": "γ_{p} (Reduction factor piling)", "x": base_x, "y": 515, "font": "OpenSans-Regular", "size": 10},
        
        #{"text": "µ_{s} (Reduction factor steel)", "x": base_x, "y": 500, "font": "OpenSans-Regular", "size": 10},
        #{"text": "µ_{c} (Reduction factor concrete)", "x": base_x, "y": 485, "font": "OpenSans-Regular", "size": 10},
   

        {"text": str(variables.get("b")), "x": base_x2, "y": 680, "font": "OpenSans-Regular", "size": 10},
        {"text": str(variables.get("lv")), "x": base_x2, "y": 665, "font": "OpenSans-Regular", "size": 10},
        #{"text": str(variables.get("lv2")), "x": base_x2, "y": 650, "font": "OpenSans-Regular", "size": 10},
        #{"text": str(variables.get("Lrb")), "x": base_x2, "y": 635, "font": "OpenSans-Regular", "size": 10},
        {"text": str(variables.get("fii")), "x": base_x2, "y": 620, "font": "OpenSans-Regular", "size": 10},
        #{"text": str(variables.get("fiieff")), "x": base_x2, "y": 605, "font": "OpenSans-Regular", "size": 10},
        {"text": str(variables.get("fyk")), "x": base_x2, "y": 590, "font": "OpenSans-Regular", "size": 10},
        {"text": str(variables.get("fck")), "x": base_x2, "y": 575, "font": "OpenSans-Regular", "size": 10},
        {"text": str(variables.get("alphaCC")), "x": base_x2, "y": 560, "font": "OpenSans-Regular", "size": 10},
        {"text": str(variables.get("gammaC")), "x": base_x2, "y": 545, "font": "OpenSans-Regular", "size": 10},
        {"text": str(variables.get("gammaS")), "x": base_x2, "y": 530, "font": "OpenSans-Regular", "size": 10},
        {"text": str(variables.get("gammaP")), "x": base_x2, "y": 515, "font": "OpenSans-Regular", "size": 10},
        #{"text": str(variables.get("myyS")), "x": base_x2, "y": 500, "font": "OpenSans-Regular", "size": 10},
        #{"text": str(variables.get("myyC")), "x": base_x2, "y": 485, "font": "OpenSans-Regular", "size": 10},
        
        
        

        # Resistance-osio
        {"text": "Resistance:", "x": base_x, "y": 465, "font": "OpenSans-Bold", "size": 10},
        {"text": "N_{max} [kN]", "x": base_x, "y": 450, "font": "OpenSans-Regular", "size": 10},
        {"text": "N_{min} [kN]", "x": base_x, "y": 435, "font": "OpenSans-Regular", "size": 10},
        {"text": "NM_{max} [kNm]", "x": base_x, "y": 420, "font": "OpenSans-Regular", "size": 10},
        {"text": "NM_{0kN} [kNm]", "x": base_x, "y": 405, "font": "OpenSans-Regular", "size": 10},

        {"text": str(variables.get("Nmax")), "x": base_x2, "y": 450, "font": "OpenSans-Regular", "size": 10},
        {"text": str(variables.get("Nmin")), "x": base_x2, "y": 435, "font": "OpenSans-Regular", "size": 10},
        {"text": str(variables.get("NMmax")), "x": base_x2, "y": 420, "font": "OpenSans-Regular", "size": 10},
        {"text": str(variables.get("NM0kN")), "x": base_x2, "y": 405, "font": "OpenSans-Regular", "size": 10},

        # Kuvateksti-osio
        {"text": "Figure 1. Main dimensions of the joint", "x": 60, "y": 445, "font": "OpenSans-Regular", "size": 8},
        {"text": "Figure 2. Normal force - Moment diagram", "x": 60, "y": 63, "font": "OpenSans-Regular", "size": 8},

        # Vastuuvapaus
        {"text": "Calculations based on EN 1990, EN 1992-1-1, EN 1993-1-1, EN 1993-1-8 and EN 12794 in ULS and non-prestressed cross-section under static load. Pile manufacturer should calculate a combined strength ", "x": 60, "y": 30, "font": "OpenSans-Regular", "size": 5},
         {"text": "of a pile and the joint and verify that the joint is suitable for selected pile and conditions with national annex and design rules. More detailed information on the joint is available on request.", "x": 60, "y": 25, "font": "OpenSans-Regular", "size": 5},


         # Lisää päivämäärä
        {"text": f"{current_date}", "x": base_x, "y": 750, "font": "OpenSans-Regular", "size": 10},
        
        {"text": str(variables.get("Tiedot")), "x": 60, "y": 15, "font": "OpenSans-Regular", "size": 5}
        ]
    
    if myyT == 1:
        texts_to_add.append({"text": "µ_{s} (Reduction factor steel)", "x": base_x, "y": 500, "font": "OpenSans-Regular", "size": 10})
        texts_to_add.append({"text": "µ_{c} (Reduction factor concrete)", "x": base_x, "y": 485, "font": "OpenSans-Regular", "size": 10})
        texts_to_add.append({"text": str(variables.get("myyS")), "x": base_x2, "y": 500, "font": "OpenSans-Regular", "size": 10})
        texts_to_add.append({"text": str(variables.get("myyC")), "x": base_x2, "y": 485, "font": "OpenSans-Regular", "size": 10})
    
    if lock2T == 1:
        texts_to_add.append({"text": "Lock 2 distance lv2 [mm]", "x": base_x, "y": 650, "font": "OpenSans-Regular", "size": 10})
        texts_to_add.append({"text": str(variables.get("lv2")), "x": base_x2, "y": 650, "font": "OpenSans-Regular", "size": 10})

    if rbeffT == 1:
        texts_to_add.append({"text": "Rebar effective diameter Φ  _{eff} [mm]", "x": base_x, "y": 605, "font": "OpenSans-Regular", "size": 10})
        texts_to_add.append({"text": str(variables.get("fiieff")), "x": base_x2, "y": 605, "font": "OpenSans-Regular", "size": 10})

    if LrbT == 1:
        texts_to_add.append({"text": "Rebar length Lrb [mm]", "x": base_x, "y": 635, "font": "OpenSans-Regular", "size": 10})
        texts_to_add.append({"text": str(variables.get("Lrb")), "x": base_x2, "y": 635, "font": "OpenSans-Regular", "size": 10})

    


    # PDF tiedostoon lisättävät kuvat
    kuvatiedosto='./JatkosKuvat/'+kuva +'.png'
    images_to_add = [
        {"image": "./TempFiles/kuvaaja.png", "x": 10, "y": 69, "width": 580, "height": 350},
        {"image": kuvatiedosto, "x": 60, "y": 455, "width": 220, "height": 220},
    ]

    outFilePDFName = variables.get("Nimi") + " Fck " + str(variables.get("fck"))

    add_text_and_image_to_pdf('DatasheetPohja.pdf', texts_to_add, images_to_add, outFilePDFName)

if __name__ == "__main__":

    main()