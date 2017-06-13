"""
autheurs: Anne van Ewijk, Amber Janssen Groesbeek, Glenn Hulsscher en Danique Bodt
naam: Textmining.py - projectblok8
opdracht: Van elke relatie (plant-anthocyaan) wordt uit de database informatie gehaald (anthocyaan_id, naam_anthocyanen, 
plant_id, naam_plant, relatie_id, abstracts, keywords, titels en pubmedids). Uit de abstracts en titels worden de stopwoorden 
gefilterd. Er worden woorden geteld door een bepaalde punten telling (Woord in het abstract; 1 punt, Woord is een keyword; 
5 punten, Woord in titel; 10 punten, Woord en soort anthocyaan in één zin; 15 punten, Woord en soort anthocyaan in één titel; 
25 punten). Van deze woorden wordt een top 10 gemaakt. Deze top 10 woorden met hun puntentelling worden in de database gezet. 
Ook wordt er in elke titel en abstract gezocht naar genen, deze genen worden ook in de database gezet.
klas: Bi2c
datum: 13-06-2017
known bugs: -
opmerkingen: Om dit script goed te laten runnen moet de goede database zijn gedownload en moet hiermee verbinding 
gemaakt kunnen worden door middel van PHP MyAdmin.
"""
from nltk.corpus import stopwords
import mysql.connector
from nltk.tokenize import word_tokenize, sent_tokenize
import string
import urllib.request
import bioc


ENCODING = "utf-8"
URL_BASE = "https://www.ncbi.nlm.nih.gov/CBBresearch/Lu/Demo/RESTful/tmTool.cgi/"
CONCEPT = "BioConcept"
FORMAT = "BioC"

host="127.0.0.1"
user="root"
password="usbw"
db="database"
port=3307

gen_for_id = []

def main():
    """
    In de main worden de meeste methodes aangeroepen.
    """
    ID_Words_db = []
    plantid_abstract_relatieid_key_titel_id = get_database()
    removeStopwords(plantid_abstract_relatieid_key_titel_id, ID_Words_db)

def get_database():
    """
    Deze methode haalt eerst alle planten die in de database staan op.
    vervolgens haalt hij van elke plant; het anthocyanen_ic, naam_anthocyanen, plant_id, naam_plant, relatie_id, 
    abstracts, keywords, titels en pubmedids op.

    :return:  plantid_abstract_relatieid_key_titel_id: Is een geneste lijst met de plant ids, abstracten, relatie ids, keys, tites, pubmed ids, naam anthocyaan
    """
    conn = mysql.connector.connect(host=host, user=user, password=password, db=db, port=port) #host="127.0.0.1", user="root", password="usbw", db="database", port=3307
    cursor = conn.cursor()

    # Ophalen van de typen planten
    cursor.execute("""SELECT naam_plant
                            FROM planten""")

    # Alle planten toevoegen aan de plant_List.
    plant_List = []
    for plant_naam in cursor.fetchall():
        plant = str(plant_naam).replace("('", "").replace("',)", "")
        plant_List.append(plant)

    allInfoDatabase =[] # In deze lijst komt alle info over de planten te staan

    # Ophalen van anthocyanenID, naam anthocyaan, plant ID, naam plant, relatie ID, abstracts, keywords, titel en pubmed IDs.
    for info in range(0, len(plant_List), 1):
        cursor.execute(
            """SELECT anthocyanen.anthocyanen_id, anthocyanen.naam_anthocyanen, planten.plant_id, planten.naam_plant, relaties.relatie_id, relaties.abstracts, relaties.keywords, relaties.titel, relaties.pubmedids
                FROM relaties 
                  JOIN  relatieantho
                    ON relatieantho.relaties_relatie_id = relaties.relatie_id  
                  JOIN  anthocyanen
                    ON relatieantho.anthocyanen_anthocyanen_id = anthocyanen.anthocyanen_id
                  JOIN  planten
                    ON planten.plant_id = relaties.planten_plant_id
                WHERE  naam_plant like '%"""+plant_List[info] + """%'""")

        for info in cursor.fetchall():
            allInfoDatabase.append(info)

    plantid_abstract_relatieid_key_titel_id = []
    # Alle woorden worden in een lijst gezet in plaats van een tuple (allInfoDatabase). plantid_abstract_relatieid_key_titel_id is een geneste lijst.
    for info in range(0, len(allInfoDatabase), 1):
        list_info = []
        list_info.append(allInfoDatabase[info][2]) #plant 3, plantid 2
        list_info.append(allInfoDatabase[info][5]) #abstract 5
        list_info.append(allInfoDatabase[info][4]) #relatieid 4
        list_info.append(allInfoDatabase[info][6]) #keywords
        list_info.append(allInfoDatabase[info][7]) #titel
        list_info.append(allInfoDatabase[info][8]) #pubmedids
        list_info.append(allInfoDatabase[info][1]) #antho 1, anthoid, 0
        plantid_abstract_relatieid_key_titel_id.append(list_info)

    cursor.close()
    conn.close()

    return plantid_abstract_relatieid_key_titel_id

def removeStopwords(plantid_abstract_relatieid_key_titel_id, ID_Words_db):
    """
    Deze methode Verwijdert alle stopwoorden.

    :param    plantid_abstract_relatieid_key_titel_id:  Is een geneste lijst met de plant ids, abstracten, relatie ids, keys, tites, pubmed ids, naam anthocyaan
              ID_Words_db: Is een lege lijst die later wordt gebruikt
    :return   countWords_dict: een dictonary met als key het woord en als value de puntentelling van het woord
    """

    # De stopwoorden worden uit de abstracten gehaald per anthocyaan - plant relatie.
    for index in range(0, len(plantid_abstract_relatieid_key_titel_id), 1):
        countWords_dict = {}
        infoOfRelation = plantid_abstract_relatieid_key_titel_id[index] # Informatie over één relatie (plant met anthocyaan)
        allAbstracts = infoOfRelation[1] # Index 1 zijn alle abstracten van de relatie.

        # In relatie_plant_id worden de plant ID, relatie ID en PubMed IDs gezet. Deze drie IDs zijn van belang bij de functie genenZoeken().
        relatie_plant_id = []
        relatie_plant_id.append(plantid_abstract_relatieid_key_titel_id[index][0])  # Plant ID
        relatie_plant_id.append(plantid_abstract_relatieid_key_titel_id[index][2])  # Relatie ID (relatie is de combinatie van een plant met een anthocyaan)
        relatie_plant_id.append(plantid_abstract_relatieid_key_titel_id[index][5])  # PubMed IDs

        if allAbstracts != "NULL":
            allWords = word_tokenize(allAbstracts.lower()) # De abstracts worden in woorden verdeeld

            good_Words = [] # in deze lijst worden alle woorden gestopt die geen stopwoorden zijn.
            for word in allWords:
                leestekens = list(string.punctuation)

                # Het toevoegen van extra stopwoorden.
                stop_words = stopwords.words("english") + leestekens + ['+/-']
                if word not in stop_words:
                    good_Words.append(word)

            stringSentence = findSentences(allAbstracts, infoOfRelation[6])
            countWords_dict = countWords(good_Words, countWords_dict, relatie_plant_id, ID_Words_db, infoOfRelation, stringSentence)
            genenZoeken(relatie_plant_id)
        else:
            print("Abstract leeg.")

    return countWords_dict

def findSentences(allAbstracts, anthocyaan):
    """
    Deze methode maakt van het abstract lossen zinnen.

    :param    allAbstracts: Alle abstracten van een relatie
              anthocyaan: Het soort anthocyaan
    :return   stringSentence: Een string met alle zinnen waarin het soort anthocyaan voorkomt
    """
    stringSentence = ""
    abstracts = allAbstracts.replace(";;;", ",") #replace anders gaat het fout bij de zinnen maken.
    sentence = sent_tokenize(abstracts) #hakt de abstracts in zinnen

    # Wanneer het soort anthocyaan in de zin voorkomt zet hij deze zin in de stringSentence.
    for s in sentence:
        if anthocyaan in s:
            stringSentence += s + "  "
    return stringSentence

def countWords(good_Words, countWords_dict, relatie_plant, ID_Words_db, infoOfRelation, stringSentence):
    """
    Deze methode telt per abstract het aantal woorden en telt deze op bij de voorafgaande abstracts.
    Wanneer een woord voorkomt in het abstract wordt er 1 bij opgeteld.

    :param    good_Words: Een lijst met woorden, deze lijst bevat geen stopwoorden
              countWords_dict: een dictonary met als key het woord en als value de puntentelling van het woord
              relatie_plant: Een lijst met het relatie id, planten id, en de pubmed ids
              ID_Words_db:
              infoOfRelation: Informatie over één relatie (plant met anthocyaan); plant id, abstracten, relatie id, keys, tites, pubmed ids, naam anthocyaan
              stringSentence: Een string met alle zinnen waarin het soort anthocyaan voorkomt
    :return   countWords_dict: een dictionary met als key het woord en als value de puntentelling van het woord
    """
    for indexOfWord in range(0, len(good_Words), 1):
        # Wanneer het woord nog niet in de dictionary countWords_dict staat als key, wordt het aantal voorkomens van dit woord geteld en toegevoegd
        if good_Words[indexOfWord] not in countWords_dict:
            # Tellen hoe vaak een woord voorkomt in het abstract
            number_occurence = good_Words.count(good_Words[indexOfWord])

            # Het woord word in de dictionary gezet met daarbij het aantal voorkomens.
            countWords_dict[good_Words[indexOfWord]] = number_occurence

    # In deze functies worden de scores berekent en geplaatst in de countWords_dict.
    countWords_dict = countKeywords(infoOfRelation, countWords_dict)
    countWords_dict = countTitles(infoOfRelation, countWords_dict)
    countWords_dict = countZinnen(countWords_dict, stringSentence)

    # Nadat countWords_dict helemaal klaar is, wordt er in de functie topTenWords de top 10 meest voorkomende woorden opgehaald.
    topTenWords(countWords_dict, relatie_plant, ID_Words_db)
    return countWords_dict

def countKeywords(infoOfRelation, countWords_dict):
    """
    Deze mehode telt per artikel wordt het aantal keywords en telt deze op bij de eerder gemaakte dictionary.
    Wanneer een keyword voorkomt wordt er 5 bij de score opgeteld.

    :param    infoOfRelation: Informatie over één relatie (plant met anthocyaan); plant id, abstracten, relatie id, keys, tites, pubmed ids, naam anthocyaan
              countWords_dict: een dictionary met als key het woord en als value de puntentelling van het woord
    :return   countWords_dict: een dictionary met als key het woord en als value de puntentelling van het woord
    """
    # De keywords zijn de woorden die de abstracten omschrijven en zijn bepaald in pubmed.
    keywords = infoOfRelation[3]
    keywords_list = keywords.split(';;;')

    for word in keywords_list:
        if word in countWords_dict:
            countWords_dict[word] += 5
        else:
            countWords_dict[word] = 5

    return countWords_dict

def countTitles(infoOfRelation, countWords_dict):
    """
    Deze methode telt per artikel het aantal woorden in de titel en telt deze op bij de eerder gemaakte dictonary.
    Wanneer een woord voorkomt in de titel wordt er 10 bij de score opgetelt.
    Wanneer er in de titel een woord met de soort anthocyaan voorkomt, dan wordt er 25 punten bij de score opgeteld. Ook worden uit de titel de stopwoorden gefilterd.

    :param    infoOfRelation: Informatie over één relatie (plant met anthocyaan); plant id, abstracten, relatie id, keys, tites, pubmed ids, naam anthocyaan
              countWords_dict: een dictionary met als key het woord en als value de puntentelling van het woord
    :return   countWords_dict: een dictionary met als key het woord en als value de puntentelling van het woord
    """
    titles = infoOfRelation[4]
    titles_list = titles.split(';;;')

    allTitles_string = ""           # Alle titels
    titlesWithAnthocyanin = ""      # Alle titels met anthocyaan erin.

    for title in titles_list:
        # Als de anthocyaan (infoOfRelation[6]) in de titel staat
        if infoOfRelation[6] in title:
            titlesWithAnthocyanin = titlesWithAnthocyanin + title + "  "

        allTitles_string += " " + title

    # Filteren van alle titels op stopwoorden en interpunctie.
    allWords_titles = word_tokenize(allTitles_string.lower())
    filtered_titles = []
    for w in allWords_titles:
        leestekens = list(string.punctuation)
        stop_words = stopwords.words("english") + leestekens + ['+/-']
        if w not in stop_words:
            filtered_titles.append(w)

    # Elk woord dat in de titel voorkomt (behalve de stopwoorden en interpuctie) word een score van 10 toegekend.
    for word in filtered_titles:
        if word in countWords_dict:
            countWords_dict[word] += 10
        else:
            countWords_dict[word] = 10

    # Filteren van de titels, waarin de type anthocyaan in voorkomt, op stopwoorden en interpunctie.
    allWordsInTitel = word_tokenize(titlesWithAnthocyanin.lower())
    titel_filter = []
    for woord in allWordsInTitel:
        leestekens = list(string.punctuation)
        stop_words = stopwords.words("english") + leestekens + ['+/-']
        if woord not in stop_words:
            titel_filter.append(woord)

    # Elk woord dat in de titel voorkomt en waarbij in de titel het soort anthocyaan voorkomt (behalve de stopwoorden en interpuctie) word een score van 25 toegekend.
    for wordd in titel_filter:
        if wordd in countWords_dict:
            countWords_dict[word] += 25
        else:
            countWords_dict[word] = 25

    return countWords_dict

def countZinnen(countWords_dict, stringSentence):
    """
    Deze methode telt per zin het aantal woorden die voorkomen met het soort anthocyaan en telt deze bij de eerder gemaakte dictonary op.
    Wanneer een woord voorkomt in een zin met het soort anthocyaan wordt er 15 bij opgeteld.

    :param    countWords_dict: een dictionary met als key het woord en als value de puntentelling van het woord
              stringSentence: Een string met alle zinnen waarin het soort anthocyaan voorkomt
    :return   countWords_dict: een dictionary met als key het woord en als value de puntentelling van het woord
    """
    # Filteren van de zinnen op stopwoorden en interpunctie. stringSentence bevat alleen de zinnen waarin anthocyaan in voorkomt.
    allWords_zin = word_tokenize(stringSentence.lower())
    filtered_zin = []
    for w in allWords_zin:
        leestekens = list(string.punctuation)
        stop_words = stopwords.words("english") + leestekens + ['+/-']
        if w not in stop_words:
            filtered_zin.append(w)

    # Per zin wordt er gekeken naar de woorden die erin voorkomen en daarbij wordt 15 bij de score opgeteld.
    for word in filtered_zin:
        if word in countWords_dict:
            countWords_dict[word] += 15
        else:
            countWords_dict[word] = 15

    return countWords_dict

def topTenWords(countWords_dict, relatie_plant, ID_Words_db):
    """
    Deze methode bepaald van alle woorden in de dictonary de top 10.

    :param    countWords_dict: een dictionary met als key het woord en als value de puntentelling van het woord
              relatie_plant: Een lijst met de relatie id, planten id, en de pubmed ids
              ID_Words_db:
    """
    temp = countWords_dict

    woordAantal = []
    # Top 10 bepalen van de meest voorkomende woorden in de abstracts.
    for rank in range(0,10,1):
        woordenLijst = []
        # Haalt de hoogste value op uit de dictionary
        key = max(temp, key=temp.get)
        value = temp.get(key)
        ID_Words_db.append(key)
        # De hoogste wordt verwijderd uit de dictionary zodat de op een na hoogste gevonden kan worden.
        del temp[key]

        woordenLijst.append(key)
        woordenLijst.append(value)
        woordAantal.append(woordenLijst)
        insertDatabase(key, value, relatie_plant, ID_Words_db)

def genenZoeken(relatie_plant_id):
    """
    Deze methode zoekt in de PubMed abstracts naar genen.
    En zet deze genen in de database.

    :param    relatie_plant_id: Een lijst met plant id, relatie id, en pubmedids.
    """
    ids = relatie_plant_id[2]
    pubMedIDs = ids.split(";;;")
    All_gene = []
    for pmid in pubMedIDs:
        url = URL_BASE + CONCEPT + "/" + str(pmid) + "/" + FORMAT + "/"
        response = urllib.request.urlopen(url).read()
        if response:
            try:
                response_decoded = response.decode(ENCODING)
                collection = bioc.loads(response_decoded, ENCODING)
                document = collection.documents[0]  # index 0 because we only searcher one PMID
                for anno in list(bioc.annotations(document)):
                    tag = anno.infons['type']
                    if tag == "Gene":
                        if anno.text not in All_gene:
                            All_gene.append(anno.text)
            except:
                continue

    for gen in All_gene:
        gene = gen.replace(",", ";").replace("'", " ")
        gen_for_id.append(gene)
        conn = mysql.connector.connect(host=host, user=user, password=password, db=db, port=port) #host="127.0.0.1", user="root", password="usbw", db="database", port=3307
        cursor = conn.cursor()

        cursor.execute(
                """INSERT INTO genen VALUES ('%d','%s')""" % (len(gen_for_id), gene))
        cursor.execute("""INSERT INTO relatiegenen VALUES('%d','%d','%d')""" % (int(relatie_plant_id[1]), int(relatie_plant_id[0]), len(gen_for_id)))
        conn.commit()
        cursor.close()
        conn.close()

def insertDatabase(key, value, relatieID_plantID, ID_Words_db):
    """
    In deze methode worden de top tien woorden in de database gezet samen met hoevaak deze voorkomen. Ook wordt de tussentabel gevuld.

    :param    key: woord 
              value: puntentelling van het woord
              relatieID_plantID: Een lijst met plant id, relatie id, en pubmedids.
              ID_Words_db:
    """
    connect = mysql.connector.connect(host=host, user=user, password=password, db=db, port=port)
    cursor = connect.cursor()
    word = key.replace(",", ";").replace("'", " ")
    cursor.execute(
            """INSERT INTO woorden VALUES ('%d','%s','%d')""" % (len(ID_Words_db), str(word), int(value)))
    cursor.execute("""INSERT INTO woordenrelatie VALUES('%d','%d','%d')""" % (len(ID_Words_db), int(relatieID_plantID[1]), int(relatieID_plantID[0])))
    connect.commit()
    cursor.close()
    connect.close()


main()