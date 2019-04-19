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
        self.dialogue_text = {}
        self.english_stopwords= set(stopwords.words('english'))
        self.unique_chunks = set()
        
    #################################################
    # DATA INPUT #
    #################################################

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
    def add_entry(self, word, chunk_id):
        word = self.stem_word(word)
        if word in self.index.keys():
            # add word to pre-existing entry
            if chunk_id not in self.index[word]:
                self.index[word].append(chunk_id)
                self.num_entries += 1
            return False
        else:
            # add new word with new entry
            self.index[word] = [chunk_id]
            self.num_entries += 1
            self.unique_chunks.add(chunk_id)
            return True

    # processes identified chunks of dialogue by adding entries
    # to an index for all non-stop words in the chunk
    def process_chunk(self, dialogue):
        chunk_key = "%s-%s-%d" % (self.curr_author, self.curr_play, self.curr_chunk_index)
        self.curr_chunk_index += 1
        for word in dialogue.split(" "):
            if self.valid_word(word):
                if self.add_entry(word, chunk_key):
                    self.num_words += 1
        
    # processes read document, identifying chunks of dialogue
    # finish changing to regex and dialogue pos from file
    def process_document(self, document, dialogue_pos, regex):
        document_sections = document.split("\n\n")
        
        # for writing the chunk
        self.curr_chunk_index = 0

        chunk_list = []
        for i in range(len(document_sections)):
            # remove leading and trailing whitespace
            section = document_sections[i].strip()
            
            match = re.match(regex, section)
            if match != None:
                dialogue = False
                if dialogue_pos == 'same':
                    dialogue = section[match.span()[1]:]
                if dialogue_pos == 'next':
                    i += 1
                    if i >= len(document_sections):
                        continue
                    dialogue = document_sections[i].strip()
                # input(section)
                # input(dialogue)
                self.process_chunk(dialogue)
                if dialogue:
                    self.num_dialogue_chunks += 1
                    chunk_list.append(dialogue)
                
        return chunk_list
        
    # breaks document into chunks and adds the chunks to an inverted index
    # on non-stop words in each chunk
    def add_document(self, document_path, dialogue_pos, regex):
        # for count display
        prev_num_words = self.num_words
        prev_num_dialogue_chunks = self.num_dialogue_chunks
        prev_num_entries = self.num_entries
        
        document = self.read_document(document_path)
        chunk_list = self.process_document(document, dialogue_pos, regex)
        
        num_words = self.num_words - prev_num_words
        num_dialogue_chunks = self.num_dialogue_chunks - prev_num_dialogue_chunks
        num_entries = self.num_entries - prev_num_entries
        # print("%d words added (%d --> %d)" % (num_words, prev_num_words, self.num_words))
        print("%d chunks added (%d --> %d)" % (num_dialogue_chunks, prev_num_dialogue_chunks, self.num_dialogue_chunks))
        # print("%d entries added (%d --> %d)" % (num_entries, prev_num_entries, self.num_entries))
        return chunk_list

    def add_play(self, corpus_root, author, path, dialogue_pos, delim):
        print("unimplemented")

    # returns dict mapping folder names of plays to manually written regex 
    # strings for identifying dialogue in each file
    # TODO
    # add entry in regex.txt (rename parse_info.txt) for dialogue position
    # add dialogue position as argument 
    def get_parse_info(self, corpus_root, author):
        regex_path = "%s/%s/%s" % (corpus_root, author, "plays/regex.txt")
        with open(regex_path, "r") as regex_file:
            regex_lines = regex_file.read().split("\n")
            regex_dict = {}
            pos_dict = {}
            for line in regex_lines:
                if line == '':
                    break
                data = line.split(" == ")
                pos_dict[data[0]] = data[1]
                if data[1] == '0':
                    pos_dict[data[0]] = "same"
                if data[1] == '2':
                    pos_dict[data[0]] = "next"
                regex_dict[data[0]] = data[2]

            return pos_dict, regex_dict
            
    def add_plays_from_author(self, corpus_root, author):
        self.curr_author = author
        
        # set up index map
        if author in self.dialogue_text:
            author_entry = self.dialogue_text[author]
        else:
            author_entry = {}
    
        # get author regex file
        # authors/<author>/plays/regex.txt
        pos_dict, regex_dict = self.get_parse_info(corpus_root, author)

        author_folder = "%s/%s/plays" % (corpus_root, author)
        print("\nIndexing %d plays from %s" % (len(os.listdir(author_folder))-1, author))
        for play in os.listdir(author_folder):
            play_folder = "%s/%s" % (author_folder, play)
            if Path(play_folder).is_dir():
                play_path  = play_folder + "/play.txt"
                dialogue_pos = pos_dict[play]
                regex = regex_dict[play]
                if dialogue_pos == '-1' or regex == '-1':
                    print("Skipping play: %s\n" % play)
                    continue
                print(play)
                self.curr_play = play
                play_entry = index.add_document(play_path, dialogue_pos, regex)
                author_entry[play] = play_entry

        self.dialogue_text[author] = author_entry

    #################################################
    # DATA ACCESS #
    #################################################
    
    # lookup in index from word
    def get_chunk_ids(self, key):
        if key in self.index:
            return self.index[key]
        else:
            return None

    # get all chunk ids
    def get_all_chunk_ids(self):
        return list(self.unique_chunks)

    # lookup text from id
    def get_text_from_id(self, chunk_id):
        keys = chunk_id.split("-")
        author = keys[0]
        play = keys[1]
        number = int(keys[2])
        if number in range(0, len(self.dialogue_text[author][play])):
            return self.dialogue_text[author][play][number]
        else:
            return "Invalid"
    # stems word and gets dialogue chunks stored in the index for the stem
    def get_dialogue_chunks(self, word):
        stemmed_word = self.stem_word(word)
        chunk_ids = self.get_chunk_ids(stemmed_word)
        if chunk_ids != None:
            chunks = []
            for id in chunk_ids:
                chunk = self.get_text_from_id(id)
                if chunk != None:
                    chunks.append(chunk)
            return chunk_ids, chunks
        else:
            return [], []

    # function to get other chunks in proximity to a provided chunk id
    def get_offset_chunk(self, chunk_id, offset):
        keys = chunk_id.split("-")
        offset_id = "%s-%s-%d" % (keys[0], keys[1], int(keys[2]) + offset)
        offset_chunk = self.get_text_from_id(offset_id)
        if offset_chunk == "Invalid":
            # print("Cannot apply offset %d to chunk id %s" % (offset, chunk_id))
            # print("Using original...")
            offset_chunk = self.get_text_from_id(chunk_id)
        return offset_id, self.get_text_from_id(offset_id)

    def get_index_info(self):
        return self.num_words, self.num_dialogue_chunks, self.num_entries
        
if __name__ == "__main__":
    corpus_root = sys.argv[1]
    author = sys.argv[2]
    index_path = sys.argv[3]
    new = sys.argv[4]
    if new == "new":
        index = WordDialogueIndex()
    else:
        with open(index_path, "rb") as obj_file:
            index = pickle.load(obj_file)
    
    index.add_plays_from_author(corpus_root, author)

    # example usage
    # chunk_ids, chunks = index.get_dialogue_chunks('chuck')
    # print("%s --> %s" % (chunk_ids[10], chunks[10]))
    # offset_id, offset_chunk = index.get_offset_chunk(chunk_ids[10], 3)
    # print("%s --> %s" % (offset_id, offset_chunk))
    # offset_id, offset_chunk = index.get_offset_chunk(chunk_ids[10], -3)
    # print("%s --> %s" % (offset_id, offset_chunk))
    
    with open(index_path, "wb") as obj_file:
        pickle.dump(index, obj_file)
