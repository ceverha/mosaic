import pickle
import sys
import os
from pathlib import Path
import re
import json
import hashlib
import pyrebase
import csv
import pprint

def read_document(document_path):
    with open(document_path, "r") as file:
        document = file.read()
        return document

class MosaicTestData:
    def __init__(self):
        # map experiment id hashes to actual ids
        self.id_map = {}
        # appended to on csv import
        self.batch_data = []
        # map experiment ids to data from corresponding MTurk submission
        self.processed_data = {}
        self.experiment_types = ["excerpts", "human_output", "computer_output", "random_output"]
        # map experiment type to average data from all submissions of that type
        # as well as lists of all points
        self.experiment_data = {}
        # map data type to each average
        self.data_averages = {}

    # master process method
    def process(self):
        # unpack data
        print(f"Inputting {len(self.batch_data)} unique responses from MTurk...")
        for row in self.batch_data:
            data = {}
            data['consistency'] = int(row['Answer.consistency'])
            data['enjoy'] = int(row['Answer.enjoy'])
            data['feedback'] = row['Answer.feedback']
            data['response'] = int(row['Answer.response'])
            data['sense'] = int(row['Answer.sense'])
            code = row['Answer.verify_code']
            
            if code not in self.id_map:
                continue

            exp_id = self.id_map[code]

            if exp_id in self.processed_data:
                if self.processed_data[exp_id] == None:
                    self.processed_data[exp_id] = [data]
                else:
                    self.processed_data[exp_id].append(data)
            else:
                self.processed_data[exp_id] = [data]
        print(f"Inputted {self.get_data_size()} valid responses")
        # average data for each experiment type
        self.experiment_data = self.get_experiment_data()
        # average data for each value
        self.data_averages = self.get_data_averages()
        self.experiment_data["field_averages"] = self.data_averages

    def save_data_as_json(self, json_path):
        with open(json_path, "w") as json_file:
            data = json.dumps(self.experiment_data, indent=2)
            json_file.write(data)
                    
    def get_data_averages(self):
        fields = ['consistency', 'enjoy', 'response', 'sense', 'all_average']
        sums = {'narratives':{}, 'overall': {}}
        for field in fields:
            sums['overall'][field] = 0
        for i in range(0,5):
            data = {'count':0}
            for field in fields:
                data[field] = 0
            sums['narratives'][i] = data

        for exp_id, data_points in self.processed_data.items():
            narrative = int(exp_id[len(exp_id)-1])
            exp_type = self.get_experiment_type(exp_id)
            for data in data_points:
                if exp_type != 'excerpts':
                    sums['narratives'][narrative]['count'] += 1
                for key, value in data.items():
                    if key in fields:
                        sums['overall'][key] += value
                        sums['overall']['all_average'] += value / 4
                        if exp_type != 'excerpts':
                            sums['narratives'][narrative][key] += value
                            sums['narratives'][narrative]['all_average'] += value / 4
        averages = {'narratives':{}, 'overall': {}}
        length = len(self.processed_data)
        for field, value in sums['overall'].items():
            averages['overall'][field] = value / length
        for narrative, values in sums['narratives'].items():
            averages['narratives'][narrative] = {}
            for field, value in values.items():
                if field != 'count':
                    averages['narratives'][narrative][field] = value / sums['narratives'][narrative]['count']
                else:
                    averages['narratives'][narrative]['count'] = value
        return averages
        
    def get_experiment_data(self):
        sums = {}
        narrative_count = {}
        for exp_type in self.experiment_types:
            sums[exp_type] = {
                'count': 0,
                'consistency': {'average_value':0, 'all_values':[], 'narratives': [0,0,0,0,0]},
                'enjoy': {'average_value':0, 'all_values':[], 'narratives': [0,0,0,0,0]},
                'feedback':[""],
                'response': {'average_value':0, 'all_values':[], 'narratives': [0,0,0,0,0]},
                'sense': {'average_value':0, 'all_values':[], 'narratives': [0,0,0,0,0]},
                'all_average': {'average_value':0, 'all_values':[], 'narratives': [0,0,0,0,0]}
            }
            narrative_count[exp_type] = [0,0,0,0,0]
        fields = ['consistency', 'enjoy', 'response', 'sense']
        for exp_id, data_points in self.processed_data.items():
            for data in data_points:
                exp_type = self.get_experiment_type(exp_id)
                narrative = int(exp_id[len(exp_id)-1])
                
                entry = sums[exp_type]
                entry['count'] += 1
                
                narrative_count[exp_type][narrative] += 1
                for field in fields:
                    entry[field]['average_value'] += data[field]
                    entry[field]['all_values'].append([data[field], exp_id])
                    entry[field]['narratives'][narrative] += data[field]
                
                entry['feedback'].append([data['feedback'], exp_id])
                
                entry['all_average']['average_value'] += (data['consistency']+data['enjoy']+
                                                  data['response']+data['sense'])/4
                entry['all_average']['all_values'].append([(data['consistency']+data['enjoy']+
                                                            data['response']+data['sense'])/4, exp_id])
                entry['all_average']['narratives'][narrative] += (data['consistency']+data['enjoy']+
                                                  data['response']+data['sense'])/4
                sums[exp_type] = entry

        averages = sums
        fields = ['consistency', 'enjoy', 'response', 'sense', 'all_average']
        for exp_type, entry in sums.items():
            for field in fields:
                averages[exp_type][field]['average_value'] /= entry['count']
                for narrative in range(5):
                    averages[exp_type][field]['narratives'][narrative] /= narrative_count[exp_type][narrative]
        return averages
            
    def get_data_size(self):
        sum = 0
        for key, value in self.processed_data.items():
            sum += len(value)
        return sum

    # determine the experiment type based on id
    def get_experiment_type(self, id):
        for exp_type in self.experiment_types:
            if exp_type in id:
                return exp_type
        return "invalid"

    # load csv from mturk
    def import_csv(self, csv_path):
        print("Importing: " + csv_path)
        self.csv_file = csv_path
        # read file
        with open(csv_path, newline='') as data:
            self.batch_data.extend(list(csv.DictReader(data, delimiter=',')))
    
    # build map of hashes to ids
    def load_id_hashes_from_firebase(self):
        config = {
            "apiKey": "AIzaSyDPMyxg4zici21EKtWhOaVGgCmtapC6jwA",
            "authDomain": "mosaic-7a697.firebaseapp.com",
            "databaseURL": "https://mosaic-7a697.firebaseio.com",
            "projectId": "mosaic-7a697",
            "storageBucket": "mosaic-7a697.appspot.com",
            "messagingSenderId": "303343650684"
        }
        firebase = pyrebase.initialize_app(config)
        email = "write@mosaic.com";
        password = "123456"; 
        auth = firebase.auth()
        user = auth.sign_in_with_email_and_password(email, password)
        db = firebase.database()
        experiment_data = db.child("experiment_data").get(user['idToken']).val()
        submitted_runs = experiment_data["experiments_finished"]
        for key, data in experiment_data.items():
            if key == "experiments_to_run":
                continue
            if key == "experiments_finished":
                continue
            if key == "verification_codes":
                continue
            code = data['verificationCode']
            self.id_map[code] = key

    def load_id_hashes_from_json(self, json_path):
        with open(json_path, "r") as data:
            parsed_data = json.loads(data.read())
            experiment_data = parsed_data['experiment_data']
            submitted_runs = experiment_data["experiments_finished"]
            for key, exp_id in submitted_runs.items():
                if key == '0':
                    continue
                experiment = experiment_data[exp_id]
                code = experiment['verificationCode']
                self.id_map[code] = exp_id

if __name__ == "__main__":
    batch_folder = sys.argv[1]
    json_folder = sys.argv[2]
    mosaic_data = MosaicTestData()
    # load csv batches
    for batch_file in os.listdir(batch_folder):
        mosaic_data.import_csv(f"{batch_folder}/{batch_file}")
    # get all experiments from firebase to unpack from verification codes
    mosaic_data.load_id_hashes_from_firebase()
    for json_file in os.listdir(json_folder):
        mosaic_data.load_id_hashes_from_json(f"{json_folder}/{json_file}")
    # unpack from verification codes
    # build averages for each experiment type
    # excerpt, human, computer
    mosaic_data.process()
    mosaic_data.save_data_as_json(sys.argv[3])
