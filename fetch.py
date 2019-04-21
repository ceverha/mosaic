import re
import os
import numpy as np
import sys
import string as string_library

import pickle
from dialogue_indexing import WordDialogueIndex
from subtitle_indexing import SubtitleIndex

import gensim
import gensim.downloader as api

from pathlib import Path

# nltk.download('stopwords')
from nltk.corpus import stopwords
english_stopwords= set(stopwords.words('english'))

class MosaicPlay:
    def __init__(self, char_names=['A','B']):
        self.name = ""
        self.lines = []
        self.sim_pairs = []
        self.char_names = char_names
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

    def add_sim_pair(self, left, right):
        self.sim_pairs.append([left, right])

    def get_length(self):
        return len(self.lines)

class MosaicConstructor:
    def new_play(self, characters):
        self.play = MosaicPlay(char_names=characters)

    def load_model(self, model_string):
        self.model = api.load(model_string)
    
    def load_narrative(self, path_to_narrative):
        self.narrative_path = path_to_narrative
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

    def get_similar_chunks(self, line, num_candidates, remove_stopwords=False, concatenate=False, offset=0, use_index=True):
        oov_chunk = [('The previous line could not be replied to.', 0)]
        
        source_words = self.tokenify(line, remove_stopwords)
        in_vocab_source = self.in_vocab(source_words)
        if len(in_vocab_source) < 1:
            return oov_chunk

        similar_chunks = {}
        if use_index:
            # get all chunks that contain words from the narrative line
            for word in source_words:
                chunks_with_word = self.index.get_dialogue_chunks(word)
                similar_chunks.update(chunks_with_word)
        else:
            similar_chunks = self.index.get_all_chunks()
        
        # print("Found %d valid chunks, computing similarity now..." % len(similar_chunks))        
        if len(similar_chunks) < 1:
            return oov_chunk

        # find the similarity for each line
        candidate_ids = {}
        for chunk_id, chunk in similar_chunks.items():
            if chunk not in candidate_ids:
                chunk_words = self.tokenify(chunk, remove_stopwords)
                in_vocab_candidate = self.in_vocab(chunk_words)
                # if for some reason the chunk is empty
                if len(in_vocab_candidate) < 1:
                    continue
                # if they are the same chunk
                if in_vocab_candidate == in_vocab_source:
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
    def generate(self, num_candidates=1, offset=1, pattern_string="0,0", use_index=True):
        # for use in saving the play
        narrative_name = os.path.basename(self.narrative_path).strip(".txt")
        self.output_id = f"{narrative_name}_{pattern_string}_{use_index}_{offset}"

        output_pattern = list(map(int, pattern_string.split("-")))
        for narrative_line in self.narrative:
            source_chunk = narrative_line
            print("\n%s:\n\t%s" % (self.play.curr_char(), source_chunk))
            self.play.add_line(source_chunk)
            for output_type in output_pattern:
                if output_type == 0:
                    similar_chunks = self.get_similar_chunks(source_chunk, num_candidates, remove_stopwords=False, offset=offset, use_index=use_index)
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

    # def print_play(self):
    #     var.format(line[0], line[1])
    #     for line in self.play.get_lines():
    #         print("\n%s:\n\t%s" % (line[0], line[1]))

    def save_play(self, folder_path):
        path = f"{folder_path}/{self.output_id}"
        with open(path, "w") as f:
            for line in self.play.get_lines():
                f.write("\n%s:\n\t%s\n" % (line[0], line[1]))
            print(f"Saved play at {path}")
        extra_path = f"{folder_path}/{self.output_id}-extra"
        with open(extra_path, "w") as f:
            for line in self.play.get_lines():
                f.write("\n%s:\n\t%s\n" % (line[0], line[1]))
            print(f"Saved play at {path}")
if __name__ == "__main__":    
    
    mosaic = MosaicConstructor()

    print("loading index: %s" % sys.argv[1])
    mosaic.load_index(sys.argv[1])

    narratives_folder = sys.argv[3]
    if not Path(narratives_folder).is_dir():
        print(f"invalid folder: {narratives_folder}")

    output_folder = sys.argv[4]
    if not Path(output_folder).is_dir():
        print(f"invalid folder: {output_folder}")

    # pattern_string = input("Pattern string eg. 0-0 or 1-0: ")
    pattern_string = sys.argv[5]
    # offset = int(input("Offset for reply: "))
    offset = int(sys.argv[6])
    # use_index = input("Use index? yes or no: ")
    use_index = sys.argv[7]
    if use_index == "yes":
        use_index = True
    else:
        use_index = False
    # characters
    characters = sys.argv[8].split("-")

    print("loading model: %s" % sys.argv[2])
    mosaic.load_model(sys.argv[2])
    
    while True:
        for narrative in os.listdir(narratives_folder):
            mosaic.new_play(characters)
            print(f"Current narrative: {narrative}")
            mosaic.load_narrative(f"{narratives_folder}/{narrative}")
            print("\nPLAY START\n")
            mosaic.generate(num_candidates=1, offset=offset, pattern_string=pattern_string, use_index=use_index)
            print("\nPLAY END\n")
            mosaic.save_play(output_folder)

        decision = input("Go again with different parameters?")
        if decision == 'yes':
            pattern_string = input("Pattern string eg. 0-0 or 1-0: ")
            offset = int(input("Offset for reply: "))
            use_index = input("Use index? yes or no: ")
            if use_index == "yes":
                use_index = True
            else:
                use_index = False
        else:
            break
