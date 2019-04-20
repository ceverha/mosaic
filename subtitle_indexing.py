import random
import os
import sys
import pickle
from pathlib import Path

class SubtitleIndex:
    def __init__ (self):
        self.id_chunk_dict = {}
        self.unique_chunks = set()
    
    def get_all_chunks(self):
        return self.id_chunk_dict
        
    def get_text(self, chunk_id):
        return self.id_chunk_dict[chunk_id]

    def get_offset_chunk(self, chunk_id, offset):
        chunk_id_parts = chunk_id.split("==")
        line_num = int(chunk_id_parts[1])
        new_line_num = line_num + offset
        offset_chunk_id = "%s==%d" % (chunk_id_parts[0], new_line_num)
        if offset_chunk_id in self.id_chunk_dict:
            offset_chunk = self.id_chunk_dict[offset_chunk_id]
            return offset_chunk_id, offset_chunk
        else:
            # return original chunk, don't worry about offset
            return chunk_id, self.id_chunk_dict[chunk_id]
            
    def load_data(self, folder, num_files):
        tagged_data = []
        count = 0
        # select randomly
        used_indexes = []
        files = os.listdir(folder)
        while count < num_files:
            i = random.randint(0, len(files) - 1)
            while i in used_indexes:
                i = random.randint(0, len(files) - 1)
            filename = files[i]
            if ".txt" in filename:
                with open("%s/%s" % (folder, filename), "rb") as file:
                    file_data = file.read()
                    lines = file_data.decode('ISO-8859-1').split("\r\n\r\n\r\n\r\n")
                    for j, line in enumerate(lines):
                        chunk_id = "%s==%d" % (filename, j)
                        self.id_chunk_dict[chunk_id] = line
                    count += 1
                    if count % 100 == 0:
                        print("Loaded in %d files out of %d desired files" % (count, num_files))

if __name__ == "__main__":
    folder = sys.argv[1]
    if not Path(folder).is_dir():
        print("%s cannot be found" % folder)
    
    index = SubtitleIndex()
    index.load_data(folder, int(sys.argv[2]))
    
    # chunk_id = list(index.get_all_chunks().items())[300][0]
    # offset_id, offset_chunk = index.get_offset_chunk(chunk_id, 1)
    # print(chunk_id)
    # print(index.get_text(chunk_id))
    # print(offset_id)
    # print(offset_chunk)

    index_path = sys.argv[3]
    with open(index_path, "wb") as obj_file:
        pickle.dump(index, obj_file)
        print("index saved at %s" % index_path)
    
