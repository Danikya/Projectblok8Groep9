"""
autheurs: Anne van Ewijk, Amber Janssen Groesbeek, Glenn Hulsscher en Danique Bodt
naam: db.py - projectblok8
opdracht: Informatie uit de database ophalen en door middel van deze informatie sunbursts visualiseren
klas: Bi2c
datum: 13-06-2017
known bugs: -
opmerkingen: Om dit script goed te laten runnen moet de goede database zijn gedownload en moet hiermee verbinding 
gemaakt kunnen worden door middel van PHP MyAdmin.
"""
import datetime
import glob
import os

import mysql.connector
import json
from flask import Flask, request, render_template

app = Flask(__name__)


@app.route('/')
def finder_pagina():
    """
    Roept de finder pagina aan
    """
    plant_lijst = getOrganisms()
    return render_template("finder.html", plant_lijst=plant_lijst)

@app.errorhandler(500)
def page_not_found(e):
    """
    Wanneer er een error 500 optreedt roept hij de pagina error500 aan
    """
    return render_template("error500.html"), 500

@app.route('/home')
def index_pagina():
    """
    Roept de home pagina aan
    """
    return render_template("index.html")

@app.route('/about')
def about_pagina():
    """
    Roept de about pagina aan
    """
    return render_template("about.html")

@app.route('/sunburst', methods=['POST'])
def my_form_post():
    """
    In deze methode worden alle methodes aangeroepen gebruikt in deze code
    :return : ????
    """

    plant = request.form.get('plant_keuze')

    woordenSets, genenSets = get_database(plant)

    #Eerst wordt de woorden dictionary aangemaakt
    first_name_dict_Woorden = maken_dict(woordenSets)
    #Dan wordt de genen dictionary aangemaakt
    first_name_dict_Genen = maken_dict(genenSets)

    maken_json(first_name_dict_Woorden, first_name_dict_Genen)

    #Hier wordt bepaald naar aanleiding van de keuze van de gebruiker welke pagina wordt gevisualiseerd (genen of woorden)
    option = request.form['sunburst_radio']
    if option == "genen":
        return render_template("genen.html")
    elif option == "woorden":
        return render_template("woorden.html")


def getOrganisms():
    """"
    In deze methode wordt verbinding gemaakt met de database en worden de organismen uit de database opgehaald.
    Deze organismen worden vervolgens gebruikt om het dropdown menu mee te vullen
    :return     plant_lijst: een lijst met alle planten gevonden in de database
    """
    conn = mysql.connector.connect(host="127.0.0.1", user="root", password="usbw", db="database", port=3307)
    cursor = conn.cursor()

    cursor.execute("""SELECT naam_plant
                        FROM planten""")
    plant_lijst = []

    # Alle planten toevoegen aan de plant_List.
    for plant_naam in cursor.fetchall():
        temp = str(plant_naam)
        x = temp.replace("('","").replace("',)", "")
        plant_lijst.append(x)

    cursor.close()
    conn.close
    #De planten worden gesorteerd op alfabetische volgorde, zodat het mooi in het dropdown menu komt.
    plant_lijst = sorted(plant_lijst)
    return plant_lijst

def get_database(plant):
    """
    In deze methode wordt weer verbinding gemaakt met de database, hieruit worden vervolgens de gekozen planten naam,
    bijbehorende anthocyanen en woorden gehaald. Er wordt een lijst met genen gemaakt en een lijst met de top 10 woorden
    die in de sunburst gebruikt gaan worden
    :param      plant: De plant gekozen door de gebruiker
    :return     woordenSets: een lijst met de top 10 woorden per anthocyaan
    :return     genenSets: een lijst met de genen gevonden per anthocyaan
    """
    conn = mysql.connector.connect(host="127.0.0.1", user="root", password="usbw", db="database", port=3307)
    cursor = conn.cursor()

    woordenSets =[]

    #De planten naam, anthocyaan namen en de top 10 woorden worden opgehaald uit de database.
    cursor.execute(
            """SELECT naam_plant, anthocyanen.naam_anthocyanen, woorden.woord
                FROM relaties 
                  JOIN  relatieantho
                    ON relatieantho.relaties_relatie_id = relaties.relatie_id  
                  JOIN  anthocyanen
                    ON relatieantho.anthocyanen_anthocyanen_id = anthocyanen.anthocyanen_id
                  JOIN  planten
                    ON planten.plant_id = relaties.planten_plant_id
                  JOIN woordenrelatie
                    ON woordenrelatie.relaties_relatie_id = relaties.relatie_id
                  JOIN woorden
                    ON woorden.woord_id = woordenrelatie.woorden_woord_id
                WHERE  naam_plant like '%"""+ plant + """%'""")

    #Alle woorden worden in een lijst gezet in plaats van een tuple. woordenSets is een geneste lijst.
    for info in cursor.fetchall():
        woordInfo = list(info)
        woordenSets.append(woordInfo)

    genenSets = []
    # De planten naam, anthocyaan namen en de genen worden opgehaald uit de database.
    cursor.execute(
        """SELECT planten.naam_plant, anthocyanen.naam_anthocyanen, genen.gen_naam
            FROM relaties
              JOIN  relatieantho
                ON relatieantho.relaties_relatie_id = relaties.relatie_id
              JOIN  anthocyanen
                ON relatieantho.anthocyanen_anthocyanen_id = anthocyanen.anthocyanen_id
              JOIN  planten
                ON planten.plant_id = relaties.planten_plant_id
              JOIN relatiegenen
                ON relatiegenen.relaties_relatie_id = relaties.relatie_id
              JOIN genen
                ON relatiegenen.genen_gen_id = genen.gen_id
            WHERE  naam_plant like '%""" + plant + """%'""")
    for info in cursor.fetchall():
        genInfo = list(info)
        genenSets.append(genInfo)

    cursor.close()
    conn.close()

    return woordenSets, genenSets




def maken_dict(sets):
    """
    Deze methode wordt eerst gebruikt om de woorden in een dictionary te zetten
    Daarna wordt deze methode nog een keer aangeroepen om de genen in een dictionary te zetten
    :param      sets: alle gegevens verkregen uit de database in de get_database methode 
    :return     first_name_dict: de json template met alles wat in deze file hoort te staan
    """
    count = 2
    wordsOfAntho = []
    allAnthoDict = {}
    iteraties = 1

    #Er wordt door de sets heen gelooped, zolang de iteraties kleiner zijn dan de lengte van de set.
    #in sets staan lijsten waarin de plant soort, type anthocyaan en een woord dat het meest voorkomt instaan.
    #Wanneer de lijsten in de sets dezelfde anthocyaan type bevatten worden de woorden daarvan toegevoegd
    #aan de lijst wordsOfAntho. Wanneer het type anthocyaan niet meer overeenkomt, wordt de type anthocyaan die
    #bij de woorden horen gebruikt als key en de lijst met woorden als value zodat deze goed in de
    #dictionary komen te staan voor de json file om te begrijpen. Daarna wordt in de eerste else het laatste word
    #of gen aan deze dictionary toegevoegd (om de index out of bounds error te vermijden)
    #Daarna wordt in de tweede else de dictionary weer leeggemaakt zodat hij bij het volgende anthocyaan weer leeg is.
    for row in sets:
        if iteraties != len(sets):
            if row[1] != sets[count - 1][1]:
                wordsOfAntho.append(row[2])
                allAnthoDict[row[1]] = wordsOfAntho
                wordsOfAntho = []

            else:
                wordsOfAntho.append(row[2])
                allAnthoDict[row[1]] = wordsOfAntho

            count += 1
            iteraties += 1
        else:
            wordsOfAntho.append(row[2])
            allAnthoDict[row[1]] = wordsOfAntho
            wordsOfAntho = []



    first_child_list = []
    first_name_dict = {}

    #In deze methode wordt de template voor de json file gemaakt.
    for key in allAnthoDict:
        # voor elk nieuwe type anthocyaan wordt de lijst leeggemaakt.
        second_child_list = []
        all_words_per_antho = allAnthoDict.get(key)

        # Voor elke type anthocyaan gaat hij elk woord opslaan in een dictionary en die allemaal toevoegen aan de lijst lijst_voor_woorden
        for word in all_words_per_antho:
            third_name_dict = {}
            third_name_dict['name'] = word
            third_name_dict['size'] = 10
            second_child_list.append(third_name_dict)

        # Voor elke type anthocyaan gaat hij de woorden eraan koppelen.
        second_name_dict = {}
        second_name_dict['name'] = key
        second_name_dict['children'] = second_child_list

        first_child_list.append(second_name_dict)

    first_name_dict['name'] = sets[0][0]

    first_name_dict['children'] = first_child_list

    return first_name_dict


def maken_json(first_name_dict_Woorden, first_name_dict_Genen):
    """
    Deze methode maakt de json files die gebruikt worden voor de sunburst.
    :param      first_name_dict_Woorden: De woorden lijsten per anthocyaan
    :param      first_name_dict_Genen: De genen lijsten per anthocyaan
    """
    #Dit zorgt ervoor dat alle oude json files worden verwijderd voordat er nieuwe worden gemaakt
    files = glob.glob('static/json/*')
    for f in files:
        os.remove(f)

    #json file voor de top 10 woorden
    with open(('static/json/sunburstWoorden{:%#H%#M%#S}.json'.format(datetime.datetime.now())), "w") as out_file:
        json.dump(first_name_dict_Woorden, out_file)

    #json file voor de genen
    with open(('static/json/sunburstGenen{:%#H%#M%#S}.json'.format(datetime.datetime.now())), "w") as out_file:
        json.dump(first_name_dict_Genen, out_file)

        out_file.close()

#
#
#
if __name__ == '__main__':
    app.run()
