import time
import zipfile
import os
import json
from sudachipy import dictionary
import urllib.request
import re
import base64
import pypdfium2 as pdfium

"""
If you run into any problems while trying to use this script 
you can contact me on discord Kartoffel#7357 and I'll try to fix it
no guarantees tho
"""

TKZR = dictionary.Dictionary(dict_type="full").create()
cntCards = 0

def loadJson(filename, default):
    try:
        return json.load(open(f"{filename}.json", encoding="utf-8"))
    except:
        return default

try:
    jpod = json.load(open("app_files/jpodFiles.json", encoding="utf-8"))
except:
    print(" Japanesepod's avaiable audio database not found!\n Please download it from Kindle2Anki's github repository!")
    jpod = []

try:
    freqMain = json.load(open("app_files/mainFreq.json", encoding="utf-8"))
except:
    freqMain = {}

config = loadJson("app_files/config", {"first_run":1})
dicts = loadJson("app_files/dicts", [])
freqlists = loadJson("app_files/freqLists", [])
history = loadJson("app_files/added", [])
historyError = loadJson("app_files/errorHistory", [])

def add_dict(dictN):
    dict = {}
    fileNames = os.listdir("app_files/{}".format(dictN))
    dictName = json.load(open("app_files/{}/index.json".format(dictN), encoding="utf-8"))["title"]
    fileNames.remove("index.json")
    for i in fileNames:
        data = json.load(open("app_files/{}/{}".format(dictN, i), encoding="utf-8"))
        for j in data:
            if (j[0] in dict):
                try:
                    if j[1] == freqMain[j[0]]:
                        dict[j[0]] = j
                except KeyError:
                    continue
            else:
                dict[j[0]] = j
    return [dictName, dict]

def add_freqList(freqN):
    freqlist = {}
    fileNames = os.listdir("app_files/freq/{}".format(freqN))
    fileNames.remove("index.json")
    for i in fileNames:
        data = json.load(open("app_files/freq/{}/{}".format(freqN, i), encoding="utf-8"))
        for j in data:
            if type(j[2]) is dict:
                if "frequency" in j[2]:
                    freqlist[j[0]] = j[2]["frequency"]
            elif re.search("★*\(\d+\)", j[2]) is not None:
                freqlist[j[0]] = j[2]
            else:
                if re.search("/", str(j[2])):
                    freqlist[j[0]] = int(j[2].split("/")[0])
                else:
                    freqlist[j[0]] = j[2]
    return freqlist

print(" Memo2Anki - https://github.com/Kartoffel0/Memo2Anki")
if config["first_run"] == 1:
    print("\n This will only be asked once,\n on the next run you'll not have to inform everything again.")
    dict_Num = int(input("\n Please inform how many dictionaries you want to add:\n "))
    print("\n Ensure the zips are on the same directory as this script")
    config["dictNum"] = dict_Num
    for i in range(dict_Num):
        with zipfile.ZipFile("{}".format(input("\n Enter the filename for your {}° dictionary:\n ".format(i+1))), 'r') as zip_ref:
            zip_ref.extractall("app_files/{}".format(i))
        dict = add_dict(i)
        config("dict_Names").append(dict[0])
        dicts.append(dict[1])
    freqNum = int(input("\n This script don't support multi frequency per word frequency lists,\n make sure the frequency list you'll add has only one frequency per word\n\n Please inform how many frequency lists you want to add,\n enter 0 if you don't want to add one:\n "))
    if freqNum > 0:
        for j in range(freqNum):
            with zipfile.ZipFile("{}".format(input("\n Enter the filename for your {}° frequency list:\n ".format(j+1))), 'r') as zip_ref:
                zip_ref.extractall("app_files/freq/{}".format(j))
            freqlists.append(add_freqList(j))
        freqMax = int(input("\n Please inform the maximum frequency limit\n any words with a frequency rank superior to\n that will not be processed:\n "))
        config["freqMax"] = freqMax
    config["first_run"] = 0
    deck = input("\n Please inform the name of the deck(!!!case sensitive!!!) where you want the cards to be added:\n ")
    config["deckName"] = deck
    cardType = input("\n Please inform the Note Type(!!!case sensitive!!!) you want to use as template for the added cards:\n ")
    config["cardType"] = cardType
    termField = input("\n Please inform the field name(!!!case sensitive!!!) where you want the 'Word' to be:\n ")
    config["termField"] = termField
    readField = input("\n Please inform the field name(!!!case sensitive!!!) where you want the 'Reading' to be:\n ")
    config["readField"] = readField
    pictureField = input("\n Please inform the field name(!!!case sensitive!!!) where you want the 'Page' to be:\n ")
    config["picField"] = pictureField
    dictField = input("\n Please inform the field name(!!!case sensitive!!!) where you want the 'Definitions' to be:\n ")
    config["dictField"] = dictField
    audioField = input("\n Please inform the field name(!!!case sensitive!!!) where you want the 'Audio' to be:\n ")
    config["audioField"] = audioField
    nameField = input("\n Please inform the field name(!!!case sensitive!!!) where you want the 'Book Name' to be\n Enter 0 if you don't want to add the book name to your cards:\n ")
    if nameField != 0:
        config["bookName"] = 1
        config["bookField"] = nameField
    checkScope = int(input("\n Please inform where do you want the script to check for duplicates,\n enter 0 to check for them only on the deck you specified or 1 to check for them on your whole collection:\n "))
    config["scope"] = "deck" if checkScope == 0 else "collection"
    names = []
    for i in range(len(config["dict_Names"])):
        if config["dict_Names"][i] in names:
            continue
        else:
            names.append(config["dict_Names"][i])

    config["dict_Names"] = names
    dict_name = config["dict_Names"]

    with open("app_files/config.json", "w", encoding="utf-8") as file:
        json.dump(config, file, ensure_ascii=False)
    with open("app_files/dicts.json", "w", encoding="utf-8") as file:
        json.dump(dicts, file, ensure_ascii=False)
    with open("app_files/freqLists.json", "w", encoding="utf-8") as file:
        json.dump(freqlists, file, ensure_ascii=False)
    print("\n Done!\n")

dict_name = config["dict_Names"]
freqMax = config["freqMax"]

def newCard(deckInfo, term, reading, defs, pageNumber, page, extension, book=0):
    global jpod
    tmpJpod = (reading+"_"+term)
    if tmpJpod in jpod:
        if book == 0:
            return {"action": "addNote", "version": 6, "params": {"note":{"deckName": deckInfo[0], "modelName": deckInfo[1], "fields": {deckInfo[2]: term, deckInfo[3]: reading, deckInfo[4]: defs.replace("\n", "<br>")}, "options": {"allowDuplicate": False, "duplicateScope": "deck", "duplicateScopeOptions": {"deckName": deckInfo[0], "checkChildren": True, "checkAllModels": True}}, "tags": ["Kindle2Anki", "Manga"], "audio": [{"filename": "{} - {}.mp3".format(reading, term),"url": "https://assets.languagepod101.com/dictionary/japanese/audiomp3.php?kanji={}&kana={}".format(term, reading), "fields": [deckInfo[6]]}], "picture": [{"filename": "{} - {}.{}".format(book, pageNumber, extension), "data": base64.b64encode(page.read()).decode('utf-8'), "fields": [deckInfo[7]]}]}}}
        else:
            return {"action": "addNote", "version": 6, "params": {"note":{"deckName": deckInfo[0], "modelName": deckInfo[1], "fields": {deckInfo[2]: term, deckInfo[3]: reading, deckInfo[4]: defs.replace("\n", "<br>"), deckInfo[7]: book}, "options": {"allowDuplicate": False, "duplicateScope": "deck", "duplicateScopeOptions": {"deckName": deckInfo[0], "checkChildren": True, "checkAllModels": True}}, "tags": ["Kindle2Anki", "Manga"], "audio": [{"filename": "{} - {}.mp3".format(reading, term),"url": "https://assets.languagepod101.com/dictionary/japanese/audiomp3.php?kanji={}&kana={}".format(term, reading), "fields": [deckInfo[6]]}], "picture": [{"filename": "{} - {}.{}".format(book, pageNumber, extension), "data": base64.b64encode(page.read()).decode('utf-8'), "fields": [deckInfo[8]]}]}}}
    else:
        print(" Warning! No audio avaiable: ", term)
        if book == 0:
            return {"action": "addNote", "version": 6, "params": {"note":{"deckName": deckInfo[0], "modelName": deckInfo[1], "fields": {deckInfo[2]: term, deckInfo[3]: reading, deckInfo[4]: defs.replace("\n", "<br>")}, "options": {"allowDuplicate": False, "duplicateScope": "deck", "duplicateScopeOptions": {"deckName": deckInfo[0], "checkChildren": True, "checkAllModels": True}}, "tags": ["Kindle2Anki", "Manga"], "picture": [{"filename": "{} - {}.{}".format(book, pageNumber, extension), "data": base64.b64encode(page.read()).decode('utf-8'), "fields": [deckInfo[7]]}]}}}
        else:
            return {"action": "addNote", "version": 6, "params": {"note":{"deckName": deckInfo[0], "modelName": deckInfo[1], "fields": {deckInfo[2]: term, deckInfo[3]: reading, deckInfo[4]: defs.replace("\n", "<br>"), deckInfo[7]: book}, "options": {"allowDuplicate": False, "duplicateScope": "deck", "duplicateScopeOptions": {"deckName": deckInfo[0], "checkChildren": True, "checkAllModels": True}}, "tags": ["Kindle2Anki", "Manga"], "picture": [{"filename": "{} - {}.{}".format(book, pageNumber, extension), "data": base64.b64encode(page.read()).decode('utf-8'), "fields": [deckInfo[8]]}]}}}

def invoke(params, term="error"):
    global cntCards
    global historyError
    global config
    time.sleep(1)
    try:
        if config["scope"] == "deck":
            requestJson = json.dumps(params).encode('utf-8')
        else:
            params["params"]["note"]["options"]["duplicateScope"] = "collection"
            params["params"]["note"]["options"]["duplicateScopeOptions"].pop("deckName", None)
            params["params"]["note"]["options"]["duplicateScopeOptions"].pop("checkChildren", None)
            requestJson = json.dumps(params).encode('utf-8')
        response = json.load(urllib.request.urlopen(urllib.request.Request('http://localhost:8765', requestJson)))
        if len(response) == 2:
            if response['error'] is None:
                cntCards += 1
                print("", cntCards, "Success:   ", term)
            elif response['error'] == 'cannot create note because it is a duplicate':
                print(" Fail!    Note is a duplicate: ", term)
            else:
                raise Exception
        else:
            raise Exception
    except:
        historyError.append(term)
        print(" Fail!    Failed to add: ", term)

def deconjug(term, mode=0):
    tkTerm = TKZR.tokenize(term)
    if mode == 0:
        return tkTerm[0].dictionary_form()
    else:
        return tkTerm[0].normalized_form()
        
def lookup(term, exact=0, dictN=0):
    if dictN == -1:
        hasEntry = []
        for d in range(config["dictNum"]):
            tmpLp = lookup(term, 0, d)
            if lookup is not None:
                hasEntry.append(tmpLp)
        return len(hasEntry) > 0
    else:
        if exact == 1:
            try:
                definition = dicts[dictN][term]
                return [term, definition[1], definition[5][0], dictN]
            except KeyError:
                return None
        else:
            try:
                definition = dicts[dictN][term]
                return [term, definition[1], definition[5][0], dictN]
            except KeyError:
                try:
                    termTK = deconjug(term)
                    definition = dicts[dictN][termTK]
                    return [termTK, definition[1], definition[5][0], dictN]
                except KeyError:
                    try:
                        termTK = deconjug(term, 1)
                        definition = dicts[dictN][termTK]
                        return [termTK, definition[1], definition[5][0], dictN]
                    except KeyError:
                        return None

entriesPage = {}
entries = {}
addedEntries = {}
books = []
while True:
    try:
        with open("My Clippings.txt", "r", encoding="utf-8") as clipp:
            tmp = []
            for line in clipp:
                if line.strip() == "==========":
                    if re.search("MKR2PDF", tmp[0]) is not None:
                        if re.search("メモ|note|nota", tmp[1], flags=re.IGNORECASE) is not None:
                            if tmp[0].strip() not in books:
                                entries[tmp[0].strip()] = []
                                entriesPage[tmp[0].strip()] = {}
                                addedEntries[tmp[0].strip()] = []
                                books.append(tmp[0].strip())
                            if tmp[3].strip() not in history and lookup(tmp[3].strip(), -1):
                                entries[tmp[0].strip()].append(tmp[3].strip())
                                line1 = []
                                line1.extend(tmp[1].split("|"))
                                pageNumber = re.search("\d+", line1[0])
                                pageNumber = pageNumber.group()
                                entriesPage[tmp[0].strip()][tmp[3].strip()] = pageNumber
                            else:
                                addedEntries[tmp[0].strip()].append(tmp[3].strip())
                    tmp = []
                else:
                    tmp.append(line)
            break
    except:
        print(" Fail loading My Clippings.txt\n File not found, please copy it from documents/My Clippings.txt to Memo2Anki's root directory!")
        tmp = input(" Enter any key to try again:\n")

print("\n Words:\t\tTotal number of words from that book on Kindle's My Clippings.txt\n Avaiable:\tTotal amount of those words not yet processed by this script\n")
print("\n | ID\t| WORDS\t\t| AVAIABLE\t| BOOK NAME")
for i in range(len(books)):
    print(" |", i," \t|",len(entries[books[i]]) + len(addedEntries[books[i]])," \t\t|",len(entries[books[i]]), "    \t|", books[i].replace(" - MKR2PDF", ""))
bookName = int(input("\n Enter the ID of the book to mine from:\n "))
numCards = int(input("\n Enter the number of cards to be added:\n You can also enter 0 to add all avaiable:\n "))
if numCards == 0:
    numCards = 99999
while True:
    try:
        pdf = pdfium.PdfDocument(f"{books[bookName]}.pdf")
        pdf.close()
        break
    except:
        print(f" Fail loading {books[bookName]}.pdf!\n File not found, please copy it to Memo2Anki's root directory!")
        tmp = input(" Enter any key to try again:\n")
for t in range(len(entries[books[bookName]])):
    try:
        if cntCards < numCards:
            subFreq = True
            if len(freqlists) > 0:
                subFreq = False
                for q in range(len(freqlists)):
                    try:
                        tmpTerm = float(freqlists[q][entries[books[bookName]][t]])
                        if tmpTerm <= freqMax:
                            subFreq = True
                    except KeyError:
                        continue
            if subFreq:
                dictEntries = []
                for u in range(config["dictNum"]):
                    if len(dictEntries) == 0:
                        entry = lookup(entries[books[bookName]][t], 1, u)
                        if entry != None:
                            dictEntries.append(entry)
                    else:
                        entry = lookup(dictEntries[0][0], 1, u)
                        if entry != None:
                            if entry[1] == dictEntries[0][1] or entry[0] == dictEntries[0][1] or entry[1] == dictEntries[0][0]:
                                dictEntries.append(entry)
                if len(dictEntries) == 0 or len(dictEntries) < config["dictNum"]:
                    for u in range(config["dictNum"]):
                        if len(dictEntries) == 0:
                            entry = lookup(entries[books[bookName]][t], 0, u)
                            if entry != None:
                                dictEntries.append(entry)
                        else:
                            entry = lookup(dictEntries[0][0], 0, u)
                            if entry != None:
                                if entry[1] == dictEntries[0][1] or entry[0] == dictEntries[0][1] or entry[1] == dictEntries[0][0]:
                                    if entry not in dictEntries:
                                        dictEntries.append(entry)
                if len(dictEntries) > 0:
                    furigana = ''
                    definition = '<div style="text-align: left;"><ol>'
                    for o in dictEntries:
                        if o[1] != "" and furigana == '':
                            furigana = o[1]
                        definition += '<li><i>({})</i>{}</li>'.format(dict_name[o[3]], o[2])
                    definition += '</ol></div>'
                    pdf = pdfium.PdfDocument(f"{books[bookName]}.pdf")
                    pdfPage = pdf.get_page((int(entriesPage[books[bookName]][entries[books[bookName]][t]]) - 1))
                    pil_image = pdfPage.render_topil()
                    pil_image.save("tmp.jpg")
                    with open('tmp.jpg', 'rb') as page:
                        if config["bookName"] == 0:
                            card = newCard([config["deckName"], config["cardType"], config["termField"], config["readField"], config["dictField"], " ", config["audioField"], config["picField"]], dictEntries[0][0], furigana, definition, entriesPage[books[bookName]][entries[books[bookName]][t]], page, "jpg")
                            invoke(card, dictEntries[0][0])
                            history.append(entries[books[bookName]][t])
                        else:
                            card = newCard([config["deckName"], config["cardType"], config["termField"], config["readField"], config["dictField"], " ", config["audioField"], config["bookField"], config["picField"]], dictEntries[0][0], furigana, definition, entriesPage[books[bookName]][entries[books[bookName]][t]], page, "jpg", books[bookName].replace(" - MKR2PDF", ""))
                            invoke(card, dictEntries[0][0])
                            history.append(entries[books[bookName]][t])
                    pdfPage.close()
                    pdf.close()
            else:
                print(" Fail!    Frequency rank > {} or no frequency avaiable: {}".format(freqMax, entries[books[bookName]][t]))
    except:
        historyError.append(entries[books[bookName]][t])
        print(" Fail!")

with open("app_files/added.json", "w", encoding="utf-8") as file:
    json.dump(history, file, ensure_ascii=False)
with open("app_files/errorHistory.json", "w", encoding="utf-8") as file:
    json.dump(historyError, file, ensure_ascii=False)

endVar = input(" Added cards: {}\n\n Enter 'OK' to close the script:\n ".format(cntCards))