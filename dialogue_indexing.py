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
        self.english_stopwords= set(stopwords.words('english'))
        self.dialogue_text = {}
        
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
            return True

    # processes identified chunks of dialogue by adding entries
    # to an index for all non-stop words in the chunk
    def process_chunk(self, section):
        regex = "^([A-Z\. ]+)[\[a-z]"
        match = re.match(regex, section)
        if match == None:
            return False
        dialogue = section[match.span()[1] - 2:]

        chunk_key = "%s-%s-%d" % (self.curr_author, self.curr_play, self.curr_chunk_index)
        self.curr_chunk_index += 1

        for word in dialogue.split(" "):
            if self.valid_word(word):
                if self.add_entry(word, chunk_key):
                    self.num_words += 1

        return dialogue
        
    # processes read document, identifying chunks of dialogue
    def process_document(self, document):
        document_sections = document.split("\n\n")
        
        if self.char_delim == ".":
            char_delim = "\."
        else:
            char_delim = self.char_delim
        # uppercase names
        match_string = "^[A-Z%s ]{3,}" % char_delim
        
        # for writing the chunk
        self.curr_chunk_index = 0

        chunk_list = []
        for i in range(len(document_sections)):
            # remove leading and trailing whitespace
            section = document_sections[i].strip()
            input("section: %s" % section)
            match = re.match(match_string, section)
            if match != None:
                if self.dialogue_pos == 2:
                    i += 1
                    section = document_sections[i].strip()
                    input("next section: %s" % section)
                    
                dialogue = self.process_chunk(section)
                input("dialogue: %s" % dialoue)
                if dialogue:
                    self.num_dialogue_chunks += 1
                    chunk_list.append(dialogue)
                
        return chunk_list
        
    # breaks document into chunks and adds the chunks to an inverted index
    # on non-stop words in each chunk
    def add_document(self, document_path):
        # for count display
        prev_num_words = self.num_words
        prev_num_dialogue_chunks = self.num_dialogue_chunks
        prev_num_entries = self.num_entries
        
        document = self.read_document(document_path)
        chunk_list = self.process_document(document)
        
        num_words = self.num_words - prev_num_words
        num_dialogue_chunks = self.num_dialogue_chunks - prev_num_dialogue_chunks
        num_entries = self.num_entries - prev_num_entries
        print("%d words added (%d --> %d)" % (num_words, prev_num_words, self.num_words))
        print("%d chunks added (%d --> %d)" % (num_dialogue_chunks, prev_num_dialogue_chunks, self.num_dialogue_chunks))
        print("%d entries added (%d --> %d)" % (num_entries, prev_num_entries, self.num_entries))
        
        return chunk_list

    def add_play(self, corpus_root, author, path, dialogue_pos, delim):
        print("unimplemented")

    def add_plays_from_author(self, corpus_root, author, dialogue_pos, delim):
        self.curr_author = author
        self.dialogue_position = dialogue_pos
        self.char_delim = delim
        
        # set up index map
        if author in self.dialogue_text:
            author_entry = self.dialogue_text[author]
        else:
            author_entry = {}
        
        author_folder = "%s/%s/plays" % (corpus_root, author)
        for play in os.listdir(author_folder):
            print(play)
            self.curr_play = play
            play_entry = index.add_document("%s/%s/play.txt" % (author_folder, play))
            author_entry[play] = play_entry
            print("")

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
    
    # need to handle char_case, new line vs. same line, and character delim
    
    # 0 = same line
    # 1 = next line
    # 2 = next next line
    dialogue_position = int(sys.argv[5])
    
    # symbol signifying the end of the character name
    char_delim = sys.argv[6]
    
    index.add_plays_from_author(corpus_root, author, dialogue_position, char_delim)

    chunk_ids, chunks = index.get_dialogue_chunks('chuck')
    print("%s --> %s" % (chunk_ids[10], chunks[10]))
    offset_id, offset_chunk = index.get_offset_chunk(chunk_ids[10], 3)
    print("%s --> %s" % (offset_id, offset_chunk))
    offset_id, offset_chunk = index.get_offset_chunk(chunk_ids[10], -3)
    print("%s --> %s" % (offset_id, offset_chunk))
    
    with open(index_path, "wb") as obj_file:
        pickle.dump(index, obj_file)
