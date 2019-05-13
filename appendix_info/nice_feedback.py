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

if __name__ == "__main__":
    data_file = sys.argv[1]
    output_file = sys.argv[2]

    exp_types = ['excerpts', 'human_output','computer_output', 'random_output']
    
    with open(data_file,"r") as rawdata:
        data = json.loads(rawdata.read())
    
    raw_feedback = {}

    for exp_type in exp_types:
        raw_feedback[exp_type] = {'count': 0}
        for entry in data[exp_type]['feedback']:
            if entry == "":
                continue
            feedback = entry[0]
            narrative = get_narrative(entry[1])
            if narrative in raw_feedback[exp_type]:
                raw_feedback[exp_type][narrative].append(feedback)
            else:
                raw_feedback[exp_type][narrative] = [feedback]
            raw_feedback[exp_type]['count'] += 1

    with open(output_file, "w") as dest:
        for exp_type, all_feedback in raw_feedback.items():
            dest.write(f"\n\n\nAll feedback for {exp_type}\n{all_feedback['count']} total responses\n\n")
            for narrative, feedback in all_feedback.items():
                if narrative == 'count':
                    continue
                dest.write(f"Feedback for narrative: {narr_name(narrative)}\n\n\n")
                for f in feedback:
                    dest.write(f"{f}\n\n")
    print(f"Saved to {output_file}")
