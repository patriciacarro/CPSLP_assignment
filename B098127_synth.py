import os
import simpleaudio
import argparse
import nltk.corpus
import re
import numpy

#import datetime
#...others?

### NOTE: DO NOT CHANGE ANY OF THE EXISTING ARGUMENTS
parser = argparse.ArgumentParser(
    description='A basic text-to-speech app that synthesises an input phrase using diphone unit selection.')
parser.add_argument('--diphones', default="./diphones", help="Folder containing diphone wavs")
parser.add_argument('--play', '-p', action="store_true", default=False, help="Play the output audio")
parser.add_argument('--outfile', '-o', action="store", dest="outfile", type=str, help="Save the output audio to a file",
                    default=None)
parser.add_argument('phrase', nargs=1, help="The phrase to be synthesised")

# Arguments for extensions
parser.add_argument('--spell', '-s', action="store_true", default=False,
                    help="Spell the phrase instead of pronouncing it")
parser.add_argument('--crossfade', '-c', action="store_true", default=False,
					help="Enable slightly smoother concatenation by cross-fading between diphone units")
parser.add_argument('--volume', '-v', default=None, type=int,
                    help="An int between 0 and 100 representing the desired volume")

args = parser.parse_args()

print(args.diphones)


class Synth:
    def __init__(self, wav_folder):
        self.diphones = {}
        self.get_wavs(wav_folder)

    # Populates the self.diphones dictionary with the diphone files
    def get_wavs(self, wav_folder):
        for root, dirs, files in os.walk(wav_folder, topdown=False):
            for file in files:
                path = os.path.join(root, file)
                au = simpleaudio.Audio()
                au.load(path)
                self.diphones[file] = au

    # Creates audio file from diphones
    def get_audio(self, diphone_seq):
        wav_list = []
        for diph in diphone_seq:
            if diph in self.diphones:
                diphone_audio_instance = self.diphones[diph]
                wav_list.append(diphone_audio_instance.data)
        a = numpy.concatenate(wav_list)
        audio = simpleaudio.Audio(rate=diphone_audio_instance.rate)
        audio.data = a
        return audio

    # Modifies volume, plays the file and saves it to chosen directory if arguments are set
    def play_and_save(self, play=False, out=None, vol=None):
        audio = self.get_audio(diphone_seq)
        if vol is not None:
            volume = vol/100
            try:
                audio.rescale(volume)
            except ValueError:
                print("Volume has to be a number between 1 and 100")
                raise
        if play == True:
            audio.play()
        if out is not None:
            audio.save(out)

class Utterance:
    def __init__(self, phrase=None):
        self.phrase = phrase
        if not isinstance(phrase, str):
            raise ValueError("Invalid Phrase: Please insert string")
        print(phrase)

    # Returns a list of words from the input phrase
    def get_word_seq(self, do_spell=False):
        lowerwords = self.phrase.lower()
        wordsandpunct = ""
        for ch in lowerwords:
            if ch in ",.:!?":
                char = " {0}".format(ch)
            else:
                char = ch
            wordsandpunct += char
            # Reference: https://stackoverflow.com/questions/367155/splitting-a-string-into-words-and-punctuation
        wordlist = wordsandpunct.split(" ")
        # Implements Spelling extension: this will only run if the spell argument has been set
        if do_spell == True:
            wordlistaux = []
            for word in wordlist:
                for letter in word:
                    wordlistaux.append(letter)
            wordlist = wordlistaux
        return wordlist

    # Returns a phone sequence from a word sequence input
    def get_phone_seq(self, word_seq):
        phones = []
        dict = nltk.corpus.cmudict.dict()
        for item in word_seq:
            if item in ",.:!?":
                phones.append("pau")
            else:
                try:
                    pronlist = dict[item]
                except KeyError:
                    print("The word '{0}' is not in the dictionary".format(item))
                    raise
                phones += pronlist[0]
        num = re.compile(r"\d")
        phones = [num.sub("", pron) for pron in phones]
        phones.insert(0, "pau")
        phones.insert(len(phones), "pau")
        return phones

    # Returns the names of the diphone files from a phone sequence input
    def get_diphone_seq(self, phone_seq):
        diphone_seq = []
        for index, phon in enumerate(phone_seq[0:-1]):
            thisphon = phon
            nextphon = phone_seq[(index + 1) % len(phone_seq)]
            # Reference: https://stackoverflow.com/questions/2167868/getting-next-element-while-cycling-through-a-list
            diph = thisphon.lower() + "-" + nextphon.lower()+".wav"
            diphone_seq.append(diph)
        return diphone_seq

if __name__ == "__main__":
    utt = Utterance(args.phrase[0])
    word_seq = utt.get_word_seq(args.spell)
    # print(word_seq)
    phone_seq = utt.get_phone_seq(word_seq)
    # print(phone_seq)
    diphone_seq = utt.get_diphone_seq(phone_seq)
    # print(diphone_seq)


    diphone_synth = Synth(wav_folder=args.diphones)
    audio = diphone_synth.get_audio(diphone_seq=diphone_seq)
    diphone_synth.play_and_save(args.play, args.outfile, args.volume)

    # out is the Audio object which will become your output
    # you need to modify out.data to produce the correct synthesis
    out = simpleaudio.Audio(rate=16000)
    print(out.data, type(out.data))


