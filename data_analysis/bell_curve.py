from scipy.stats import ttest_ind
from statistics import mean

import sys
import os
import re
import json
import csv
import pprint
import pickle
import numpy

if __name__ == "__main__":
    data_file = sys.argv[1]
    exp_types = ['excerpts', 'human_output', 'computer_output', 'random_output']

    with open(data_file,"r") as rawdata:
        data = json.loads(rawdata.read())
    
    scores = {}
    for exp_type in exp_types:
        scores[exp_type] = []

    for exp_type, entry in data.items():
        if exp_type not in exp_types:
            continue
        for value in entry['all_average']['all_values']:
            scores[exp_type].append(value[0])

    # average value per length band

    band_size = 0.25
    max_score = 5.0
    curr_score = 1.0

    rows = []
    exp_rows = {}
    for exp_type in exp_types:
        exp_rows[exp_type] = []

    all_data_rows = []
    rows.append(["Protocol", "Score-Band", "Count"])
    all_data_rows.append(["Score-Band", "Count"])
    while curr_score <= max_score:
        curr_max = curr_score + band_size
        all_count = 0
        for exp_type in exp_types:
            count = 0
            for score in scores[exp_type]:
                if score >= curr_score and score < curr_max:
                    count += 1
                    all_count += 1
            row = [exp_type, curr_score, count]
            exp_rows[exp_type].append(row)
        all_data_row = [curr_score, all_count]
        all_data_rows.append(all_data_row)
        curr_score += band_size
        curr_score = round(curr_score, 2)
    
    for _, points in exp_rows.items():
        rows.extend(points)
    
    pprint.pprint(rows)
    output_path = f"exp_bell_curves.csv"
    input(f"Save to {output_path}?")
    with open(output_path, "w") as csv_file:
        writer = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for row in rows:
            writer.writerow(row)

    pprint.pprint(all_data_rows)
    output_path = f"all_bell_curves.csv"
    input(f"Save to {output_path}?")
    with open(output_path, "w") as csv_file:
        writer = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for row in all_data_rows:
            writer.writerow(row)
