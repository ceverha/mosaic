import sys
import os
import re
import json
import csv
import pprint

if __name__ == "__main__":
    data_file = sys.argv[1]
    
    narratives = [0,1,2,3,4]
    with open(data_file,"r") as rawdata:
        output = {}
        data = json.loads(rawdata.read())
    
    # average values by experiment types
    values = ['count', 'consistency', 'enjoy', 'response', 'sense', 'all_average']
    exp_types = ['excerpts', 'human_output', 'computer_output', 'random_output']
    fields = ['Protocol', 'Count', 'Consistency', 'Enjoy', 'Response', 'Sense', 'Average']
    rows = []
    rows.append(fields)
    for exp_type in exp_types:
        row = []
        row.append(exp_type)
        for field in values:
            if field == 'count':
                row.append(round(data[exp_type][field], 3))
            else:
                row.append(round(data[exp_type][field]['average_value'], 3))
        rows.append(row)
    pprint.pprint(rows)
    output_path = f"graph_csv/average_by_exp_type.csv"
    input(f"Save to {output_path}?")
    with open(output_path, "w") as csv_file:
        writer = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for row in rows:
            writer.writerow(row)
    # average average by narrative
    values = ['count', 'consistency', 'enjoy', 'response', 'sense', 'all_average']
    exp_types = ['human_output', 'computer_output', 'random_output']
    fields = ['Narrative', 'Count', 'Consistency', 'Enjoy', 'Response', 'Sense', 'Average']
    rows = []
    rows.append(fields)
    for narrative in narratives:
        row = []
        row.append(narrative)
        for field in values:
            row.append(round(data['field_averages']['narratives'][str(narrative)][field], 3))
        rows.append(row)
    pprint.pprint(rows)
    output_path = f"graph_csv/average_by_narrative.csv"
    input(f"Save to {output_path}?")
    with open(output_path, "w") as csv_file:
        writer = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for row in rows:
            writer.writerow(row)

    # average values by narrative for each experiment
    values = ['consistency', 'enjoy', 'response', 'sense', 'all_average']
    exp_types = ['human_output', 'computer_output', 'random_output']
    fields = ['Narrative', 'Consistency', 'Enjoy', 'Response', 'Sense', 'Average']
    for exp_type in exp_types:
        rows = []
        rows.append(fields)
        for narrative in narratives:
            rows.append([narrative])
        for field in values:
            narrative_vals = data[exp_type][field]['narratives']
            for i, val in enumerate(narrative_vals):
                rows[i+1].append(round(val, 3))
        pprint.pprint(rows)
        output_path = f"graph_csv/{exp_type}_by_narrative.csv"
        input(f"Save to {output_path}?")
        with open(output_path, "w") as csv_file:
            writer = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            for row in rows:
                writer.writerow(row)
    
