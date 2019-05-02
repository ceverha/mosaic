import sys
import os
import re
import json
import csv
import pprint

if __name__ == "__main__":
    data_file = sys.argv[1]
    values = ['consistency', 'enjoy', 'response', 'sense', 'all_average']
    fields = ['narrative', 'consistency', 'enjoy', 'response', 'sense', 'all_average']
    exp_types = ['human_output', 'computer_output', 'random_output']
    narratives = [0,1,2,3,4]
    with open(data_file,"r") as rawdata:
        output = {}
        data = json.loads(rawdata.read())
    
    for exp_type in exp_types:
        rows = []
        rows.append(fields)
        for narrative in narratives:
            rows.append([narrative])
        for field in values:
            narrative_vals = data[exp_type][field]['narratives']
            for i, val in enumerate(narrative_vals):
                rows[i+1].append(val)
        pprint.pprint(rows)
        output_path = f"narrative_csv/{exp_type}.csv"
        input(f"Save to {output_path}?")
        with open(output_path, "w") as csv_file:
            writer = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            for row in rows:
                writer.writerow(row)
