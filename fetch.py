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
    
    def curr_char(self):
        return self.char_names[self.curr_char_index]

    def add_line(self, line):
        full_line = [self.next_char(), line]
        self.lines.append(full_line)
        
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
        oov_chunk = [('The previous line could not be replied to.', 0)]
        similar_chunks = {}
        
        source_words = self.tokenify(line, remove_stopwords)
        in_vocab_source = self.in_vocab(source_words)
        if len(in_vocab_source) < 1:
            return oov_chunk

        # get all chunks that contain words from the narrative line
        for word in source_words:
            chunk_ids, chunks = self.index.get_dialogue_chunks(word)
            for i in range(0, len(chunk_ids)):
                similar_chunks[chunk_ids[i]] = chunks[i]

        # print("Found %d valid chunks, computing similarity now..." % len(similar_chunks))        
        if len(similar_chunks) < 1:
            return oov_chunk


        # find the similarity for each line
        candidate_ids = {}
        for chunk_id, chunk in similar_chunks.items():
            if chunk not in candidate_ids:
                chunk_words = self.tokenify(chunk, remove_stopwords)
                in_vocab_candidate = self.in_vocab(chunk_words)
                if len(in_vocab_candidate) < 1:
                    continue
                sim = self.model.n_similarity(in_vocab_source, in_vocab_candidate)
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
        
        output_pattern = list(map(int, pattern_string.split(",")))
        for narrative_line in self.narrative:
            source_chunk = narrative_line
            print("\n%s:\n\t%s" % (self.play.curr_char(), source_chunk))
            self.play.add_line(source_chunk)
            for output_type in output_pattern:
                if output_type == 0:
                    similar_chunks = self.get_similar_chunks(source_chunk, num_candidates, remove_stopwords=True, offset=offset)
                    if num_candidates > 1:
                        for i, candidate in enumerate(similar_chunks):
                            if i > num_candidates:
                                break
                        print("%d: %s" % (i, candidate))
                        chunk_index = int(input("Choose a candidate to add to the play: "))
                    else:
                        chunk_index = 0
                    source_chunk = similar_chunks[chunk_index][0]
                    print("\n%s:\n\t%s" % (self.play.curr_char(), source_chunk))
                if output_type == 1:
                    source_chunk = input("\n%s:\n\t" % self.play.curr_char())
                self.play.add_line(source_chunk)

    def print_play(self):
        for line in self.play.get_lines():
            print("\n%s:\n\t%s" % (line[0], line[1]))

    def save_play(self, file_path):
        with open(file_path, "w") as f:
            for line in self.play.get_lines():
                f.write("\n%s:\n\t%s\n" % (line[0], line[1]))

if __name__ == "__main__":
    mosaic = MosaicConstructor()

    print("loading narrative: %s" % sys.argv[2])
    mosaic.load_narrative(sys.argv[2])

    print("loading index: %s" % sys.argv[3])
    mosaic.load_index(sys.argv[3])

    print("loading model: %s" % sys.argv[1])
    mosaic.load_model(sys.argv[1])
    
    print("starting generation")
    num_candidates = 1
    # offset of 1 means the system will select the reply to the most similar piece of dialogue
    offset = 1
    pattern_string = "1,0,1,0"
    mosaic.generate(num_candidates=num_candidates, offset=offset, pattern_string=pattern_string)

    mosaic.print_play()

    mosaic.save_play(sys.argv[4])
