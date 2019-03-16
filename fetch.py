import re
import os
import numpy as np
import sys
import string as string_library

import pickle
from dialogue_indexing import WordDialogueIndex

import gensim
import gensim.downloader as api

# nltk.download('stopwords')
from nltk.corpus import stopwords
english_stopwords= set(stopwords.words('english'))

class MosaicPlay:
    def __init__(self):
        self.name = ""
        self.lines = []
        self.char_names = ['JACK', 'JILL']
        self.curr_char_index = 0

    def next_char(self):
        output = self.char_names[self.curr_char_index]
        self.curr_char_index += 1
        if self.curr_char_index >= len(self.char_names):
            self.curr_char_index = 0
        return output

    def add_line(self, line):
        full_line = [self.next_char(), line]
        self.lines.append(full_line)

    def get_lines(self):
        return self.lines

class MosaicConstructor:
    def __init__(self):
        self.play = MosaicPlay()
        
    def load_model(self, model_string):
        self.model = api.load(model_string)
    
    def load_narrative(self, path_to_narrative):
        with open(path_to_narrative, "r") as f:
            text = f.read()
            narrative = text.split("\n")
            # remove empty lines
            for line in narrative:
                if line == '' or line == ' ' or line == '\n':
                    narrative.remove(line)
            self.narrative = narrative

    def load_index(self, index_path, load_into_mem=False):
        with open(index_path, "rb") as obj_file:
            self.index = pickle.load(obj_file)

    def tokenify(self, string, remove_stopwords):
        words = re.sub("\n", " ", string).split(" ")
        tokens = []
        for word in words:
            token = word.lower()
            token = token.translate(token.maketrans('','',string_library.punctuation))
            if remove_stopwords:
                if token not in english_stopwords:
                    tokens.append(token)
            else:
                tokens.append(token)
        return tokens

    def in_vocab(self, word_list):
        filtered = []
        for word in word_list:
            if word in self.model.wv:
                filtered.append(word)
        return filtered

    def get_similar_chunks(self, line, num_candidates, remove_stopwords=False, concatenate=False):
        similar_chunks = []
        # replace new lines with white space then split into words
        narrative_words = self.tokenify(line, remove_stopwords)
        
        # get all chunks that contain words from the narrative line
        for word in narrative_words:
            chunks = self.index.get_dialogue_chunks(word)
            similar_chunks.extend(chunks)

        print("Found %d valid chunks, computing similarity now..." % len(similar_chunks))
        
        # find the similarity for each line
        candidate_chunks = {}
        for chunk in similar_chunks:
            if chunk not in candidate_chunks:
                chunk_words = self.tokenify(chunk, remove_stopwords)
                sim = self.model.n_similarity(self.in_vocab(narrative_words), self.in_vocab(chunk_words))
                candidate_chunks[chunk] = sim
        
        # return top n candidates
        sorted_candidates = sorted(candidate_chunks.items(), key=lambda x: x[1], reverse=True)
        if len(sorted_candidates) >= num_candidates:
            return sorted_candidates[0:num_candidates]
        else:
            return sorted_candidates

    def generate(self, num_candidates, interactive=True):
        for line in self.narrative:
            print("\nMatching --> %s" % line)
            chunks = self.get_similar_chunks(line, num_candidates, remove_stopwords=True)
            for i, candidate in enumerate(chunks):
                print("%d: %s" % (i, candidate))
            if interactive:
                chunk_index = int(input("Choose a candidate to add to the play: "))
            else:
                chunk_index = 0
            self.play.add_line(chunks[chunk_index])

    def print_play(self):
        for line in self.play.get_lines():
            print("%s.\n\t%s" % (line[0], line[1][0]))

    def save_play(self, file_path):
        with open(file_path, "w") as f:
            for line in self.play.get_lines():
                f.write("\n%s.\n\t%s\n" % (line[0], line[1][0]))

if __name__ == "__main__":
    mosaic = MosaicConstructor()

    print("loading model")
    mosaic.load_model(sys.argv[1])
    
    print("loading narrative")
    mosaic.load_narrative(sys.argv[2])

    print("loading index")
    mosaic.load_index(sys.argv[3])

    print("starting generation")
    num_candidates = int(sys.argv[4])
    mosaic.generate(num_candidates)

    mosaic.print_play()

    mosaic.save_play(sys.argv[5])
