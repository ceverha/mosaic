import re
import os
import numpy as np
import sys
import string as string_library
import random
import time
import json

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
        
    def get_sim_pairs(self):
        return self.sim_pairs

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

    def end_of_line(self, word):
        punctuation = ['.',',','?','!', ';',':', '-']
        for punc in punctuation:
            if punc in word:
                return True
        return False

    def limit_length(self, input_data, length=30):
        words = input_data.split(" ")
        if len(words) <= length:
            return input_data
        else:
            output_words = []
            for i, word in enumerate(words):
                if len(output_words) < length:
                    output_words.append(word)
                else:
                    last_word = output_words[i-1]
                    if self.end_of_line(last_word):
                        break
                    else:
                        output_words.append(word)
            output_data = " ".join(output_words)
            return output_data

    def get_similar_chunks(self, line, num=1, remove_stopwords=False, concatenate=False, offset=0, use_index=True):
        oov_chunk = ['The previous line could not be replied to.', 0]
        
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
        
        print("Found %d valid chunks, computing similarity now..." % len(similar_chunks))        
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

        sorted_candidates = sorted(candidate_ids.items(), key=lambda x: x[1], reverse=True)
        
        most_similar_ids = []
        for i in range(num):
            most_similar_ids.append(sorted_candidates[i])
        return most_similar_ids

    def get_random_chunk(self):
        all_chunks = self.index.get_all_chunks()
        
        random_index = random.randint(0, len(all_chunks) - 1)
        random_id = list(all_chunks.keys())[random_index]
        random_chunk = all_chunks[random_id]
        # self.play.add_sim_pair("random selection", random_chunk)
        
        return [random_chunk, -1] 

        # return ["text", sim_score]

    # defaults to 1 candidate with two unsupervised replies
    def generate(self, offset=1, pattern_string="0-0", use_index=True, random_chunk=False):
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
                    if not random_chunk:
                        similar_chunks = self.get_similar_chunks(source_chunk, remove_stopwords=False, offset=offset, use_index=use_index)
                    else:
                        similar_chunks = self.get_random_chunk()
                    source_chunk = similar_chunks[0]
                    print("\n%s:\n\t%s" % (self.play.curr_char(), source_chunk))
                if output_type == 1:
                    source_chunk = input("\n%s:\n\t" % self.play.curr_char())
                self.play.add_line(source_chunk)

    def save_play(self, folder_path):
        path = f"{folder_path}/{self.output_id}"
        with open(path, "w") as f:
            for line in self.play.get_lines():
                f.write("\n%s:\n\t%s\n" % (line[0], line[1]))
            print(f"Saved play at {path}")
        extra_path = f"{folder_path}/{self.output_id}-extra"
        with open(extra_path, "w") as f:
            f.write("Similarity pairs\n\n")
            for pair in self.play.get_sim_pairs():
                f.write("%s\n<===>\n%s\n\n" % (pair[0], pair[1]))

if __name__ == "__main__":    
    
    mosaic = MosaicConstructor()

    print("loading index: %s" % sys.argv[1])
    mosaic.load_index(sys.argv[1])

    print("loading model: %s" % sys.argv[2])
    mosaic.load_model(sys.argv[2])

    iterations = int(sys.argv[3])

    # eval index speed and recall vs without index
    # TODO try with top 3 from index vs 1 from without, check if intersection exists

    with_index_chunks = []
    without_index_chunks = []
    for i in range(iterations):
        print(i)
        source_chunk = mosaic.get_random_chunk()[0]
        start = time.time()
        similar_chunk_with = mosaic.get_similar_chunks(source_chunk, num=3, remove_stopwords=False, offset=0, use_index=True)
        end = time.time()
        with_index_chunks.append([end-start, similar_chunk_with])

        start = time.time()
        similar_chunk_without = mosaic.get_similar_chunks(source_chunk, num=3, remove_stopwords=False, offset=0, use_index=False)
        end = time.time()
        without_index_chunks.append([end-start, similar_chunk_without])
    
    pickle.dump({'with': with_index_chunks, 'without': without_index_chunks}, open("intermediate", "wb"))

    same_count = 0
    intersection_count = 0
    average_time_with = 0
    average_time_without = 0
    average_sim_diff = 0
    for i in range(iterations):
        a = with_index_chunks[i]
        b = without_index_chunks[i]
        print(a)
        print(b)
        if b[1][0][0] == a[1][0][0]:
            same_count += 1
        if len(set(b[1][0]).intersection(a[1][0])) > 0:
            intersection_count += 1
        if len(b[1][0]) >= 3 and len(a[1][0]) >= 3:
            average_sim_diff += abs(float(b[1][0][1]) - float(a[1][0][1]))
        average_time_with += a[0]
        average_time_without += b[0]
    average_sim_diff /= iterations
    average_time_with /= iterations
    average_time_without /= iterations
    print(f"{average_sim_diff} = average cosine sim difference between top of each type")
    print(f"{same_count} out of {iterations} same")
    print(f"{intersection_count} out of {iterations} intersect")
    print(f"{average_time_with}s, with index")
    print(f"{average_time_without}s, without index")
    with open(f"eval_index_{iterations}.out", "w") as out_file:
        out_file.write(f"{average_sim_diff} = average cosine sim difference between top of each type\n")
        out_file.write(f"{same_count} out of {iterations} same\n")
        out_file.write(f"{intersection_count} out of {iterations} intersect\n")
        out_file.write(f"{average_time_with}s, with index\n")
        out_file.write(f"{average_time_without}s, without index\n")
