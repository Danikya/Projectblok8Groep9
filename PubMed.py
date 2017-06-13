"""
autheurs: Anne van Ewijk, Amber Janssen Groesbeek, Glenn Hulsscher en Danique Bodt
naam: PubMed.py - projectblok8
opdracht: Voegt verschillende soorten planten en anthocyanen toe aan de database. En zoek doormiddel van verschillende 
combinaties plant en anthocyaan naar artikelen waarvan informatie wordt opgehaald (abstacts, keywords, PubMed ids, titels). 
Deze informatie wordt in de database opgeslagen per relatie (plant-anthocyaan).
klas: Bi2c
datum: 13-06-2017
known bugs: -
opmerkingen: Om dit script goed te laten runnen moet de goede database zijn gedownload en moet hiermee verbinding 
gemaakt kunnen worden door middel van PHP MyAdmin.
"""
import itertools
from Bio import Entrez, Medline
import mysql.connector

host="127.0.0.1"
user="root"
password="usbw"
db="database"
port=3307

def main():
    """
    In de main worden de meeste methodes aangeroepen.
    """
    #De plant_List en anthocyanin_List kan de bioloog naar wensen in vullen.
    plant_List = ["Solanum","Fragaria","Helianthus","Aquilegia","Alstroemeria","Dianthus","Malus","Anthurium","Musa","Phaseolus","Theobroma","Manihot","Chrysanthemum","Phoenix","Vitis","Pisum","Eucalyptus","Rubus","Freesia","Pelargonium","Gerbera","Hordeum","Setaria","Citrus","Avena","Gossypium","Castanea","Prunus","Cicer","Actinidia" ]
    anthocyanin_List = ["anthocyanin", "malvidin", "aurantinidin", "cyanidin", "delphinidin", "europinidin", "pelargonidin", "peonidin", "petunidin", "rosinidin"]

    comb_plant_anthocyanin = getCombinations(plant_List, anthocyanin_List)
    insertDatabase(plant_List, anthocyanin_List)
    getPubMedIDs(comb_plant_anthocyanin, plant_List, anthocyanin_List)

def getCombinations(plant_List, anthocyanin_List):
    """
    Deze methode maakt alle mogelijke combinaties met de lijsten van planten en anthocyanen. 
    Alle combinaties van een plant met de anthocyanen worden gereturned in de variabel plant_anthocyanin.

    :param    plant_List: een lijst met alle planten. 
              anthocyanin_List: een lijst met alle anthocyanen
    :return   comb_plant_anthocyanin: Een lijst met alle mogelijke combinaties tussen planten en anthocyanen
    """
    comb_plant_anthocyanin = list(itertools.product(plant_List, anthocyanin_List))
    return comb_plant_anthocyanin

def insertDatabase(plant_List, anthocyanin_List):
    """
    Deze methode zet alle verschillende planten uit plant_List en alle verschillende anthocyanen uit anthocyanin_List 
    in de (lokale) database.

    :param    plant_List: een lijst met alle planten. 
              anthocyanin_List: een lijst met alle anthocyanen
    """
    conn = mysql.connector.connect(host=host, user=user, password=password, db=db, port=port) #(host="127.0.0.1", user="root", password="usbw", db="database", port=3307)
    cursor = conn.cursor()

    primaryKey_ID_plants = 1 #zorgt ervoor dat de primaire key (ID) steeds anders is van de planten
    for plant in plant_List:
        cursor.execute("""INSERT INTO planten VALUES('%d','%s')""" % (primaryKey_ID_plants, plant))
        primaryKey_ID_plants += 1

    primaryKey_ID_antho = 1  #zorgt ervoor dat de primaire key (ID) steeds anders is van de anthocyanen
    for anthocyanin in anthocyanin_List:
        cursor.execute("""INSERT INTO anthocyanen VALUES ('%d','%s')""" % (primaryKey_ID_antho, anthocyanin))
        primaryKey_ID_antho += 1

    conn.commit()
    cursor.close()
    conn.close()

def getPubMedIDs(comb_plant_anthocyanin, plant_List, anthocyanin_List):
    """
    Deze methode haalt alle combinaties (plant en type anthocyanin) worden gebruikt om PubMed IDs op te halen 
    waar de combinatie in voorkomt op.

    :param    comb_plant_anthocyanin: Een lijst met alle mogelijke combinaties tussen planten en anthocyanen
              plant_List: een lijst met alle planten. 
              anthocyanin_List: een lijst met alle anthocyanen
    """
    IDforCombinations = [] # De lengte van de lijst wordt gebruikt om de ID te bepalen van de plant-anthocyaan combinaties (voor de database).

    # Over alle mogelijke combinaties loopen. Per combinatie wordt de functie getInfoOfAbstract() aangeroepen.
    for combination in range(0, len(comb_plant_anthocyanin), 1):
        plant_type = comb_plant_anthocyanin[combination][0]
        anthocyanin_type = comb_plant_anthocyanin[combination][1]

        IDforCombinations.append(plant_type)

        # Query die wordt gebruikt om te zoeken in pubmed naar de artikelen
        query = plant_type + " AND " + anthocyanin_type

        Entrez.email = "Your.Name.Here@example.org"
        handle = Entrez.esearch(db="pubmed", term=query, retmax=10000) #Er worden maximaal 10.000 artikelen opgehaald
        record = Entrez.read(handle)
        idList = record["IdList"]

        # Per combinatie worden in de functie getAbstract() de inhoud van de artikelen opgehaald.
        getInfoOfAbstract(idList, plant_type, anthocyanin_type, plant_List, anthocyanin_List, IDforCombinations)

def getInfoOfAbstract(idList, plant_type, anthocyanin_type, plant_List, anthocyanin_List, IDforCombinations):
    """
    Deze methode haalt alle informatie (ID, titel, abstract, keywords) van een artikel op uit de abstracten die 
    behoren tot een combinatie (plant-anthocyaan).

    :param    idList: een lijst met alle pubmed ids
              plant_type: planten soort van de combinatie 
              anthocyanin_type: anthocyanen soort van de combinatie
              plant_List: een lijst met alle planten. 
              anthocyanin_List: een lijst met alle anthocyanen
              IDforCombinations: Een lijst met elke type plant, type planten kunnen ook dubbel voorkomen. Dit is om later een goed id mee te geven aan de database.
    """
    # Aan de hand van de idList, word de inhoud van artikelen opgehaald.
    handle = Entrez.efetch(db="pubmed", id=idList, rettype="medline", retmode="text", retmax=10000)
    records = Medline.parse(handle)


    # De lijsten die per combinatie van een plant met een anthocyaan gevuldt worden. Wanneer er een nieuwe combinatie aan de beurt is, worden de lijsten geleegd.
    All_abstracts = []
    All_pubmedID = []
    All_keywords = []
    All_titles = []

    # Het ophalen van PubMedID (PMID), de titel (TI), de auteurs (AU) en abstract (AB) van de artikelen die behoren tot één bepaalde combinatie. Deze worden opgeslagen in de database.
    for record in records:
        pubmed_ID = record.get("PMID", "NULL")
        pubmed_title = record.get("TI", "NULL").replace(",", ";").replace("'", " ") #de , en ' worden gereplaced omdat de database anders moeilijk doet bij het inserten van deze informatie
        pubmed_abstract = record.get("AB", "NULL").replace(",", ";").replace("'", " ") #de , en ' worden gereplaced omdat de database anders moeilijk doet bij het inserten van deze informatie
        pubmed_keywords = record.get("OT", "NULL")

        #pubmed_keywords is een lijst hierbij kan je niet replace.
        # door de eventuele , en ' er uit ta halen wordt er over de lijst heen geloopt als de lijst niet leeg ("NULL") is.
        if pubmed_keywords != "NULL":
            for keyword in pubmed_keywords:
                All_keywords.append(keyword.replace(",", ";").replace("'", " ")) #de , en ' worden gereplaced omdat de database anders moeilijk doet bij het inserten van deze informatie

        # Alle gegevens van een combinatie worden hierin opgeslagen.
        All_pubmedID.append(pubmed_ID)
        All_abstracts.append(pubmed_abstract)
        All_titles.append(pubmed_title)

    #Wanneer het er geen pubmedid aanwezig is maakt hij de lijst leeg.
    if All_pubmedID[0] == "NULL":
        All_pubmedID = []


    insertInfoDatabase(All_pubmedID, All_abstracts, All_keywords, All_titles, plant_type, anthocyanin_type, plant_List, anthocyanin_List, IDforCombinations)

def insertInfoDatabase(All_pubmedID, All_abstract, All_keywords, All_titles, plant_type, anthocyanin_type, plant_List, anthocyanin_List, IDforCombinations):
    """
    Deze methode zet alle informatie van de artikelen in de database.

    :param    All_pubmedID: Een lijst met alle pubmedids
              All_abstract: Een lijst met alle abstracten
              All_keywords: Een lijst met alle keywords
              All_titles: Een lijst met alle titels
              plant_List: een lijst met alle planten. 
              anthocyanin_List: een lijst met alle anthocyanen
              plant_List: een lijst met alle planten. 
              anthocyanin_List: een lijst met alle anthocyanen
              IDforCombinations: Een lijst met elke type plant, type planten kunnen ook dubbel voorkomen. Dit is om later een goed id mee te geven aan de database.
    """
    conn = mysql.connector.connect(host=host, user=user, password=password, db=db, port=port) #(host="127.0.0.1", user="root", password="usbw", db="database", port=3307)
    cursor = conn.cursor()

    #Alle lijsten worden aan elkaar geplakt.
    #Ze worden nog wel gescheiden door ;;;, zodat het nog gescheiden kan worden nadat je de informatie uit de database hebt gehaald
    str_keywords = ';;;'.join(All_keywords)
    str_titel = ';;;'.join(All_titles)
    str_abstract = ';;;'.join(All_abstract)
    str_pubmedID = ';;;'.join(All_pubmedID)

    # Hier worden de IDs bepaald die in de database worden gezet.
    plantID_database = plant_List.index(plant_type) + 1
    anthocyaninID_database = anthocyanin_List.index(anthocyanin_type) + 1
    combinationID_database = len(IDforCombinations)


    cursor.execute("""INSERT INTO relaties VALUES ('%d','%d','%d', '%s', '%s', '%s', '%s')""" % (combinationID_database, len(All_pubmedID), plantID_database, str_pubmedID, str_abstract, str_keywords, str_titel))
    cursor.execute("""INSERT INTO relatieantho VALUES ('%d','%d','%d')""" % (combinationID_database, plantID_database, anthocyaninID_database))

    conn.commit()
    cursor.close()
    conn.close()

main()