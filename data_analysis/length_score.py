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

def get_length(play_id, values):
    if play_id in values:
        return values[play_id], values
    else:
        path = play_id.replace("--", "-")
        path = path.replace("-", "/")
        path = path.replace("going_for_p_value", "all_output")
        if 'computer' in path or 'random' in path:
            path = path + "_0-0-0_True_1"
        if 'human' in path:
            path = path + "_1-0-1_True_1"
        with open(path, "r") as play_file:
            length = len(play_file.read())
            values[play_id] = length
            return length, values
        
if __name__ == "__main__":
    data_file = sys.argv[1]
    fields = ['Protocol', 'Length', 'Average']
    exp_types = ['excerpts', 'human_output', 'computer_output', 'random_output']

    with open(data_file,"r") as rawdata:
        data = json.loads(rawdata.read())
    
    all_rows = []
    all_rows.append(fields)
    
    threshold_score = 2.5

    length_values = {}
    for exp_type, entry in data.items():
        if exp_type not in exp_types:
            continue
        
        length_rows = []
        average_value_rows = []
        
        # add load-in from pickle
        for i, value in enumerate(entry['all_average']['all_values']):
            length, new_length_values = get_length(value[1], length_values)
            length_values = new_length_values
            if value[0] >= threshold_score:
                length_rows.append(length)
                average_value_rows.append(value[0])
            
        exp_rows = [exp_type] * len(length_rows)
        data_rows = [exp_rows, length_rows, average_value_rows]
        all_rows.extend(numpy.transpose(data_rows).tolist())
        print(f"{exp_type}: {len(length_rows)} added")


    output_path = f"length_average_{threshold_score}.csv"
    input(f"Save to {output_path}?")
    with open(output_path, "w") as csv_file:
        writer = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for row in all_rows:
            writer.writerow(row)

    # average value per length band

    band_size = 200
    max_length = 0
    for _, value in length_values.items():
        if value > max_length:
            max_length = value
    print(f"\n\nmax length: {max_length}")
    curr_min = 0
    band_values = {}
    while curr_min < max_length:
        curr_max = curr_min + band_size
        for row in all_rows[1:]:
            length = int(row[1])
            score = float(row[2])
            if length >= curr_min and length < curr_max:
                if curr_min in band_values:
                    band_values[curr_min].append(score)
                else:
                    band_values[curr_min] = [score]
        curr_min += band_size
    input(f"num bands: {len(band_values)}")
    average_band_values = {}
    for band, values in band_values.items():
        sum = 0
        for val in values:
            sum += val
        average_band_values[band] = sum / len(values)
    average_rows = []
    average_rows.append(["Band", "Value"])
    for band, val in average_band_values.items():
        average_rows.append([band, val])
    pprint.pprint(average_rows)
    
    output_path = f"band_values_{threshold_score}.csv"
    input(f"Save to {output_path}?")
    with open(output_path, "w") as csv_file:
        writer = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for row in average_rows:
            writer.writerow(row)
