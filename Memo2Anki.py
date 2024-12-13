import time
import zipfile
import os
import json
from sudachipy import dictionary
import urllib.request
import re
import base64
import pypdfium2 as pdfium
import shutil

"""
discord Kartoffel#7357 
"""

TKZR = dictionary.Dictionary(dict="full").create()
cntCards = 0

def loadJson(filename, default):
    try:
        return json.load(open(f"{filename}.json", encoding="utf-8"))
    except:
        return default

def dumpJson(filename, var):
    with open(f"app_files/{filename}", "w+", encoding="utf-8") as file:
        json.dump(var, file, ensure_ascii=False)

try:
    jpod = json.load(open("app_files/jpodFiles.json", encoding="utf-8"))
except:
    print(" Japanesepod's avaiable audio database not found!\n Please download it from Memo2Anki's github repository!")
    jpod = []

try:
    freqMain = json.load(open("app_files/mainFreq.json", encoding="utf-8"))
except:
    freqMain = {}

config = loadJson("app_files/config", {"first_run":1, "dict_Names": []})
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

def checkConfig(configDict):
    queries = [
        ["deckName", lambda : input("\n Please inform the name of the deck(!!!case sensitive!!!) where you want the cards to be added:\n ")], 
        ["cardType", lambda : input("\n Please inform the Note Type(!!!case sensitive!!!) you want to use as template for the added cards:\n ")],
        ["termField", lambda : input("\n Please inform the field name(!!!case sensitive!!!) where you want the 'Word' to be, make sure it is the first field of the Note Type you've chosen:\n ")],
        ["readField", lambda : input("\n Please inform the field name(!!!case sensitive!!!) where you want the 'Reading' to be:\n ")],
        ["dictField", lambda : input("\n Please inform the field name(!!!case sensitive!!!) where you want the 'Definitions' to be:\n ")],
        ["picField", lambda : input("\n Please inform the field name(!!!case sensitive!!!) where you want the 'Manga Page' to be:\n ")],
        ["audioField", lambda : input("\n Please inform the field name(!!!case sensitive!!!) where you want the 'Audio' to be:\n ")],
        ["freqField", lambda : input("\n Please inform the field name(!!!case sensitive!!!) where you want the 'Word Frequency' to be, or enter 0 if you don't want it on your cards:\n ")],
        ["bookName", lambda : input("\n Please inform the field name(!!!case sensitive!!!) where you want the 'Book Name' to be\n Enter 0 if you don't want to add the book name to your cards:\n ")],
        ["bookField", lambda : configDict["bookName"] if configDict["bookName"] != 0 else None],
        ["scope", lambda : "deck" if int(input("\n Please inform where do you want the script to check for duplicates,\n enter 0 to check for them only on the deck you specified or 1 to check for them on your whole collection:\n ")) == 0 else "collection"]
    ]
    for i in queries:
        if i[0] not in configDict:
            configDict[i[0]] = i[1]()
    return configDict

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
        config["dict_Names"].append(dict[0])
        dicts.append(dict[1])
        shutil.rmtree("app_files/{}".format(i), ignore_errors=True)
    freqNum = int(input("\n This script don't support multi frequency per word frequency lists,\n make sure the frequency list you'll add has only one frequency per word\n\n Please inform how many frequency lists you want to add,\n enter 0 if you don't want to add one:\n "))
    if freqNum > 0:
        for j in range(freqNum):
            with zipfile.ZipFile("{}".format(input("\n Enter the filename for your {}° frequency list:\n ".format(j+1))), 'r') as zip_ref:
                zip_ref.extractall("app_files/freq/{}".format(j))
            freqlists.append(add_freqList(j))
        freqMax = int(input("\n Please inform the maximum frequency limit\n any words with a frequency rank superior to that will not be processed, enter 0 to not set a limit:\n "))
        config["freqMax"] = freqMax
        freqField = input("\n Please inform the field name(!!!case sensitive!!!) where you want the 'Word Frequency' to be, or enter 0 if you don't want it on your cards:\n")
        config["freqField"] = freqField
        shutil.rmtree("app_files/freq", ignore_errors=True)
    if freqNum == 0:
        config["freqMax"] = 0
        config["freqField"] = 0
    config = checkConfig(config)
    config["first_run"] = 0
    names = []
    for i in range(len(config["dict_Names"])):
        if config["dict_Names"][i] in names:
            continue
        else:
            names.append(config["dict_Names"][i])

    config["dict_Names"] = names
    dict_name = config["dict_Names"]

    dumpJson("config.json", config)
    dumpJson("dicts.json", dicts)
    dumpJson("freqLists.json", freqlists)
    print("\n Done!\n")

config = checkConfig(config)
dumpJson("config.json", config)

dict_name = config["dict_Names"]
freqMax = config["freqMax"]

def newCard(config, args):
    global jpod
    tmpJpod = (args["reading"]+"_"+args["term"])
    card = {"action": "addNote", "version": 6, "params": {"note":{"deckName": config["deckName"], "modelName": config["cardType"], "fields": {config["termField"]: args["term"], config["readField"]: args["reading"], config["dictField"]: args["definition"].replace("\n", "<br>")}, "options": {"allowDuplicate": False, "duplicateScope": "deck", "duplicateScopeOptions": {"deckName": config["deckName"], "checkChildren": True, "checkAllModels": True}}, "tags": ["Kindle2Anki", "Manga"], "picture": [{"filename": "{} - {}.{}".format(args["bookName"], args["pageNumber"], "jpg"), "data": base64.b64encode(args["page"].read()).decode('utf-8'), "fields": [config["picField"]]}]}}}
    if tmpJpod in jpod:
        card["params"]["note"]["audio"] = [{"filename": "{} - {}.mp3".format(args["reading"], args["term"]),"url": "https://assets.languagepod101.com/dictionary/japanese/audiomp3.php?kanji={}&kana={}".format(args["term"], args["reading"]), "fields": [config["audioField"]]}]
    else:
        print(" Warning!    No audio avaiable: ", args["term"])
    if "frequency" in args:
        card["params"]["note"]["fields"][config["freqField"]] = args["frequency"]
    if "bookName" in args:
        card["params"]["note"]["fields"][config["bookField"]] = args["bookName"]
    return card

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
        for d in range(config["dictNum"]):
            tmpLp = lookup(term, 0, d)
            if tmpLp is not None:
                return True
        return False
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
booksTmp = []
books = []
while True:
    try:
        with open("My Clippings.txt", "r", encoding="utf-8") as clipp:
            tmp = []
            for line in clipp:
                if line.strip() == "==========":
                    if re.search("MKR2PDF", tmp[0]) is not None:
                        if re.search("メモ|note|nota", tmp[1], flags=re.IGNORECASE) is not None:
                            if tmp[0].strip() not in booksTmp:
                                entries[tmp[0].strip()] = []
                                entriesPage[tmp[0].strip()] = {}
                                addedEntries[tmp[0].strip()] = []
                                booksTmp.append(tmp[0].strip())
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
        print(" Failed to load My Clippings.txt\n File not found, please copy it from documents/My Clippings.txt to Memo2Anki's root directory!")
        tmp = input(" Enter any key to try again:\n")
        
for b in range(len(booksTmp)):
    if len(entries[booksTmp[b]]) != 0:
        books.append(booksTmp[b])

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
        print(f" Failed to load {books[bookName]}.pdf!\n File not found, please copy it to Memo2Anki's root directory!")
        tmp = input(" Enter any key to try again:\n")
for t in range(len(entries[books[bookName]])):
    try:
        if cntCards < numCards:
            subFreq = True
            freqs = []
            if len(freqlists) > 0:
                if freqMax == 0:
                    subFreq = True
                else:
                    subFreq = False
                for q in range(len(freqlists)):
                    try:
                        tmpTerm = float(freqlists[q][entries[books[bookName]][t]])
                        if tmpTerm <= freqMax or subFreq == True:
                            subFreq = True
                            freqs.append(tmpTerm)
                    except KeyError:
                        continue
            if len(freqs) == 0:
                        freqs.append(123456789)
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
                    pil_image.save("app_files/tmp.jpg")
                    with open('app_files/tmp.jpg', 'rb') as page:
                        args = {"term": dictEntries[0][0], "reading": furigana, "definition": definition, "pageNumber": entriesPage[books[bookName]][entries[books[bookName]][t]], "page": page}
                        if config["bookName"] != 0:
                            args["bookName"] = books[bookName].replace(" - MKR2PDF", "")
                        if "freqField" in config and config["freqField"] != 0:
                            args["frequency"] = str(int(min(freqs))).replace("123456789", "")
                        card = newCard(config, args)
                        invoke(card, dictEntries[0][0])
                        history.append(entries[books[bookName]][t])
                    pdfPage.close()
                    pdf.close()
            else:
                print(" Fail!    Frequency rank > {} or no frequency avaiable: {}".format(freqMax, entries[books[bookName]][t]))
    except Exception as e:
        historyError.append(entries[books[bookName]][t])
        print(" Fail!   ", e)

dumpJson("added.json", history)
dumpJson("errorHistory.json", historyError)

endVar = input(" Added cards: {}\n\n Enter 'OK' to close the script:\n ".format(cntCards))