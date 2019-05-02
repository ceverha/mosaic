import sys
import os
import re
import json
import csv
import pprint
import numpy

if __name__ == "__main__":
    data_file = sys.argv[1]
    three_values = ['consistency', 'enjoy', 'sense']
    fields = ['exp_type','response','three_average']
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

        response_row = []
        for value in entry['response']['all_values']:
            response_row.append(value[0])
        
        three_average_row = []
        for value in entry['consistency']['all_values']:
            three_average_row.append(value[0])
        for i, value in enumerate(entry['sense']['all_values']):
            three_average_row[i] += value[0]
        for i, value in enumerate(entry['sense']['all_values']):
            three_average_row[i] += value[0]
        for i, point in enumerate(three_average_row):
            three_average_row[i] = point / 3

        data_rows = [exp_row, response_row, three_average_row]
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
