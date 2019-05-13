import sys
import os
import re
import json
import csv
import pprint
import numpy

if __name__ == "__main__":
    data_file = sys.argv[1]
    a_values = ['enjoy', 'sense']
    b_values = ['consistency', 'response']
    fields = ['exp_type','a_average','b_average']
    exp_types = ['excerpts', 'human_output', 'computer_output', 'random_output']

    with open(data_file,"r") as rawdata:
        data = json.loads(rawdata.read())
    
    all_rows = []
    all_rows.append(fields)
    for exp_type, entry in data.items():
        if exp_type not in exp_types:
            continue
        rows = []
        
        exp_row = [exp_type] * entry['count']

        a_average_row = [0] * entry['count']
        for field in a_values:
            for i, value in enumerate(entry[field]['all_values']):
                a_average_row[i] += value[0]
        
        b_average_row = [0] * entry['count']
        for field in b_values:
            for i, value in enumerate(entry[field]['all_values']):
                b_average_row[i] += value[0]
        
        for i in range(entry['count']):
            a_average_row[i] = a_average_row[i] / 2 
            b_average_row[i] = b_average_row[i] / 2

        data_rows = [exp_row, a_average_row, b_average_row]
        rows.extend(numpy.transpose(data_rows).tolist())
        print(exp_type)
        input()
        all_rows.extend(rows)

    output_path = f"scatter.csv"
    input(f"Save to {output_path}?")
    with open(output_path, "w") as csv_file:
        writer = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for row in all_rows:
            writer.writerow(row)
