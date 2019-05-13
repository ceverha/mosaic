from scipy.stats import ttest_ind
from statistics import mean

import sys
import os
import re
import json
import csv
import pprint
import numpy

# arr2 has higher mean
def do_test(arr1, arr2):
    print(f"{len(arr1)}, {mean(arr1)}")
    print(f"{len(arr2)}, {mean(arr2)}")
    percent = round((mean(arr2) - mean(arr1))/mean(arr1) * 100.0, 1)
    print(f"{percent}% higher mean")
    t_test = ttest_ind(arr1, arr2)
    print(t_test)

if __name__ == "__main__":
    data_file = sys.argv[1]

    exp_types = ['excerpts', 'human_output','computer_output', 'random_output']
    narratives = [0, 1, 2, 3, 4]

    sample_fields = ['response', 'all_average']
    
    with open(data_file,"r") as rawdata:
        data = json.loads(rawdata.read())
    
    for sample_field in sample_fields:
        print(f"\nFIELD: {sample_field}\n")
        average_values = {'experiment':{}, 'narrative':{}}
        for exp_type in exp_types:
            average_values['experiment'][exp_type] = {'all':[]}
            for n in narratives:
                average_values['experiment'][exp_type][n] = []
        for narrative in narratives:
            average_values['narrative'][narrative] = {'all':[]}
            for e in exp_types:
                average_values['narrative'][narrative][e] = []

        for exp_type, entry in data.items():
            if exp_type not in exp_types:
                continue
            all_values = entry[sample_field]['all_values']
            for value in all_values:
                exp_id = value[1]
                narrative = int(exp_id[len(exp_id)-1])
            
                average_values['experiment'][exp_type][narrative].append(value[0])
                average_values['experiment'][exp_type]['all'].append(value[0])
                
                average_values['narrative'][narrative][exp_type].append(value[0])
                average_values['narrative'][narrative]['all'].append(value[0])
    
        do_test(average_values['experiment']['computer_output']['all'], average_values['experiment']['excerpts']['all'])
