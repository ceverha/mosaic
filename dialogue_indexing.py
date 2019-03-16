import sys
import os
from pathlib import Path
import re
import nltk
import pickle
# only necessary once
# nltk.download('stopwords')
from nltk.corpus import stopwords
from nltk.stem.snowball import SnowballStemmer
stemmer = SnowballStemmer("english")

class WordDialogueIndex:
    def __init__(self):
        self.index = {}
        self.num_words = 0
        self.num_dialogue_chunks = 0
        self.num_entries = 0
        self.doc_path = ""
        self.english_stopwords= set(stopwords.words('english'))
        
    def read_document(self, document_path):
        with open(document_path, "r") as file:
            document = file.read()
            return document

    def valid_word(self, word):
        if word == "" or word == " " or word == "\n" or word == "\r":
            return False
        return word not in self.english_stopwords

    def stem_word(self, word):
        return stemmer.stem(word)

    # returns true if a new word is added to the index
    # false if a chunk is added to a pre-existing word's entry
    def add_entry(self, word, chunk):
        word = self.stem_word(word)
        if word in self.index.keys():
            # add word to pre-existing entry
            if chunk not in self.index[word]:
                self.index[word].append(chunk)
                self.num_entries += 1
            return False
        else:
            # add new word with new entry
            self.index[word] = [chunk]
            self.num_entries += 1
            return True
        
    # processes identified chunks of dialogue by adding entries
    # to an index for all non-stop words in the chunk
    def process_chunk(self, section):
        # trim character names
        regex = "^([A-Z\. ]+)[\[a-z]"
        match = re.match(regex, section)
        if match == None:
            return False
        dialogue = section[match.span()[1] - 2:]
        
        for word in dialogue.split(" "):
            if self.valid_word(word):
                if self.add_entry(word, dialogue):
                    self.num_words += 1

        return True
        
    # processes read document, identifying chunks of dialogue
    def process_document(self, document):
        document_sections = document.split("\n\n")
        
        #####
        # shaw specific parsing strategy
        match_string = "^[A-Z\. ]{3,}"
        #####

        for section in document_sections:
            # remove leading and trailing whitespace
            section = section.strip()
            match = re.match(match_string, section)
            if match != None:
                if self.process_chunk(section):
                    self.num_dialogue_chunks += 1
                
    # breaks document into chunks and adds the chunks to an inverted index
    # on non-stop words in each chunk
    def add_document(self, document_path):
        prev_num_words = self.num_words
        prev_num_dialogue_chunks = self.num_dialogue_chunks
        prev_num_entries = self.num_entries
        
        document = self.read_document(document_path)
        self.process_document(document)
        
        num_words = self.num_words - prev_num_words
        num_dialogue_chunks = self.num_dialogue_chunks - prev_num_dialogue_chunks
        num_entries = self.num_entries - prev_num_entries
        print("%d words added (%d --> %d)" % (num_words, prev_num_words, self.num_words))
        print("%d chunks added (%d --> %d)" % (num_dialogue_chunks, prev_num_dialogue_chunks, self.num_dialogue_chunks))
        print("%d entries added (%d --> %d)" % (num_entries, prev_num_entries, self.num_entries))

    # stems word and gets dialogue chunks stored in the index for the stem
    def get_dialogue_chunks(self, word):
        word = self.stem_word(word)
        return self.index[word]

    def get_index_info(self):
        return self.num_words, self.num_dialogue_chunks, self.num_entries
        
if __name__ == "__main__":
    author_folder = sys.argv[1]
    if not Path(author_folder).is_dir():
        print("%s cannot be found" % author_folder)
    
    index = WordDialogueIndex()
    for filename in os.listdir(author_folder):
        print(filename)
        index.add_document("%s/%s/play.txt" % (author_folder, filename))
        print("")

    print("chuck")
    print(index.get_dialogue_chunks('chuck'))
    with open("index.obj", "wb") as obj_file:
        pickle.dump(index, obj_file)
