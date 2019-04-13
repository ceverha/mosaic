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

    def add_line(self, line, verbose=False):
        full_line = [self.next_char(), line]
        self.lines.append(full_line)
        if verbose:
            print("\n%s.\n\t%s" % (full_line[0], full_line[1][0]))

    def get_lines(self):
        return self.lines

    def get_length(self):
        return len(self.lines)

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

    def get_similar_chunks(self, line, num_candidates, remove_stopwords=False, concatenate=False, offset=0):
        similar_chunks = {}
        # replace new lines with white space then split into words
        narrative_words = self.tokenify(line, remove_stopwords)
        
        # get all chunks that contain words from the narrative line
        for word in narrative_words:
            chunk_ids, chunks = self.index.get_dialogue_chunks(word)
            for i in range(0, len(chunk_ids)):
                similar_chunks[chunk_ids[i]] = chunks[i]

        print("Found %d valid chunks, computing similarity now..." % len(similar_chunks))
        
        # find the similarity for each line
        candidate_ids = {}
        for chunk_id, chunk in similar_chunks.items():
            if chunk not in candidate_ids:
                chunk_words = self.tokenify(chunk, remove_stopwords)
                sim = self.model.n_similarity(self.in_vocab(narrative_words), self.in_vocab(chunk_words))
                candidate_ids[chunk_id] = sim
        
        # get offset chunks if necessary
        offset_chunks = {}
        if offset != 0:
            for chunk_id in candidate_ids:
                offset_id, offset_chunk = self.index.get_offset_chunk(chunk_id, offset)
                offset_chunks[offset_id] = candidate_ids[chunk_id]
                # to add the text
                similar_chunks[offset_id] = offset_chunk
            candidate_ids = offset_chunks

        # replace ids with text
        candidate_chunks = {}
        for chunk_id, sim in candidate_ids.items():
            candidate_chunks[similar_chunks[chunk_id]] = sim

        # return top n candidates
        sorted_candidates = sorted(candidate_chunks.items(), key=lambda x: x[1], reverse=True)
        if len(sorted_candidates) >= num_candidates:
            return sorted_candidates[0:num_candidates]
        else:
            return sorted_candidates

    # defaults to 1 candidate with two unsupervised replies
    def generate(self, num_candidates=1, offset=1, pattern_string="0,0"):
        
        output_pattern = pattern_string.split(",")

        for narrative_line in self.narrative:
            source_line = narrative_line
            for output_type in output_pattern:
                if output_type == 0:
                    similar_chunks = self.get_similar_chunks(source_line, num_candidates, remove_stopwords=True, offset=offset)
                    for i, candidate in enumerate(chunks):
                        print("%d: %s" % (i, candidate))
                    chunk_index = int(input("Choose a candidate to add to the play: "))
                    source_line = chunks[chunk_index]
                if output_type == 1:
                    source_line = input("Write a reply to the above line: ")
                self.play.add_line(source_line, True)

    def print_play(self):
        for line in self.play.get_lines():
            print("\n%s.\n\t%s" % (line[0], line[1][0]))

    def save_play(self, file_path):
        with open(file_path, "w") as f:
            for line in self.play.get_lines():
                f.write("\n%s.\n\t%s\n" % (line[0], line[1][0]))

if __name__ == "__main__":
    mosaic = MosaicConstructor()

    print("loading model")
    mosaic.load_model(sys.argv[1])
    
    print("choose from available narratives")
    mosaic.load_narrative(sys.argv[2])

    print("loading index")
    mosaic.load_index(sys.argv[3])

    print("starting generation")
    num_candidates = 5
    # offset of 1 means the system will select the reply to the most similar piece of dialogue
    offset = 1
    pattern_string = "0,0,0,1"
    mosaic.generate(num_candidates=num_candidates, offset=offset, pattern_string=pattern_string)

    mosaic.print_play()

    mosaic.save_play(sys.argv[7])
