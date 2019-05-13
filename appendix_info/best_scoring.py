from scipy.stats import ttest_ind
from statistics import mean

import sys
import os
import re
import json
import csv
import pprint
import numpy

def get_narrative(exp_id):
    narrative = int(exp_id[len(exp_id)-1])
    return narrative

def narr_name(narr_num):
    names = {0: 'Love', 1: 'Cave', 2: 'Filler', 3: 'Ball', 4: 'Conflict'}
    return names[narr_num]

def cleanup(raw_text):
    clean_text = raw_text.replace("A:\n", "A:")
    clean_text = clean_text.replace("B:\n", "B:")
    return clean_text

def get_play_text(play_id):
    path = play_id.replace("--", "-")
    path = path.replace("-", "/")
    path = path.replace("going_for_p_value", "all_output")
    if 'computer' in path or 'random' in path:
        path = path + "_0-0-0_True_1"
    if 'human' in path:
        path = path + "_1-0-1_True_1"
    with open(path, "r") as play_file:
        return play_file.read()

if __name__ == "__main__":
    data_file = sys.argv[1]

    exp_types = ['excerpts', 'human_output','computer_output', 'random_output']
    narratives = [0, 1, 2, 3, 4]

    sample_fields = ['all_average']
    
    with open(data_file,"r") as rawdata:
        data = json.loads(rawdata.read())
    
    max_values = {}
    num_values = 5
    for exp_type in exp_types:
        max_values[exp_type] = {}
        for field in sample_fields:
            max_values[exp_type][field] = []
            for i in range(num_values):
                max_values[exp_type][field].append([0, 'start_value'])
    
    for exp_type in exp_types:
        for sample_field in sample_fields:
            entry = data[exp_type][sample_field]
            for item in entry['all_values']:
                if item[0] > max_values[exp_type][field][2][0]:
                    max_values[exp_type][field][4] = item
                    max_values[exp_type][field].sort(key=lambda x: x[0], reverse=True)
    
    pprint.pprint(max_values)

    with open(sys.argv[2], "w") as dest:
        # get text and write for all of these plays
        for exp_type, values in max_values.items():
            dest.write(f"\n\n\nTop {num_values} plays for {exp_type}\n\n\n")
            for score_id in values['all_average']:
                text = cleanup(get_play_text(score_id[1]))
                dest.write(f"\n\nScore: {score_id[0]}\n\n")
                dest.write(text)

    print(f"saved to {sys.argv[2]}")
            
    
