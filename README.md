# Memo2Anki
CLI Python script to mine from pdfs created with [Mokuro2Pdf](https://github.com/Kartoffel0/Mokuro2Pdf)

### To use this script please make your sure Kindle language is set to either Brazilian Portuguese, English or Japanese

# Features
- Semi-automatic ```Word, Reading, Definition, Manga Page, Audio, BookName``` Anki card creation with definitions from how many Yomichan dictionaries you want and audio from JapanesePod
- Manual selection of which book the script will mine the words from, the amount of cards to be created and the minimum frequency rank a word needs to have in order to be added
- No need to import any APKG files as the cards are created using AnkiCOnnect

# Installation
- Install SudachiPy
```pip install sudachipy sudachidict_full```
- Install [AnkiConnect](https://ankiweb.net/shared/info/2055492159) if you don't have it already installed
- Clone this repository

# Usage
### Converting Mokuro's html overlay to pdf
- DO NOT remove "MKR2PDF" from the generated pdf's filename, without that this script will not work
- After the conversion is finished a `<title you gave to the pdf> - MKR2PDF.json` file is going to be generated, copy that and the folder with all the manga pages to the same directory as this script

### While reading:
- Select the word you want to mine
- Press "Nota|Note|メモ" to add create a note
- Type in the word you want to mine
- Hit save

### Running the script:
#### This script utilizes AnkiConnect, make sure you have Anki running on the background before you run the script
- Plug your kindle into your computer and grab the `My Clippings.txt` file from its storage by going to ```documents/```, or by searching for "My Clippings.txt", and paste it in the same folder as the Memo2Anki.py file
- Run the script
- Choose the book you want to mine from when prompted to
- Choose how many cards you want the script to generate when prompted to
- Wait for it to finish running and enter "OK" to close the script when prompted to

### First run setup
- You'll have to install your dictionaries and frequency lists, make sure you have all of them in the same folder as the Memo2Anki.py file
- The script is not compatible with Pitch Accent dictionaries
- The script is also not compatible with multiple-frequency frequency lists, please use one with only 1 frequency per word
- Be careful when entering your deck and card info, any mistypes will result in the script not working properly

## Note that:
- This script will only create cards for japanese words
- This script will not generate any duplicate cards
- The cards are generated automatically, flaws are expected
- This script will only try to create a card for a specific word once, if you delete a faulty card it will not be created again on the next run.
