import sys
import os
from pathlib import Path
import re
import json
import hashlib
import pyrebase

def read_document(document_path):
    with open(document_path, "r") as file:
        document = file.read()
        return document

if __name__ == "__main__":
    folder = sys.argv[1]
    # how many times an experiment is added to experiments_to_run
    num_duplicate = 2
    json_source_dict = {}
    experiments_to_run = []
    verification_codes = []
    experiments_finished = [""]
    for exp_type in os.listdir(folder):
        type_path = f"{folder}/{exp_type}"
        for exp_folder in os.listdir(type_path):
            exp_path = f"{type_path}/{exp_folder}"
            for exp_file in os.listdir(exp_path):
                # skip similarity pair files
                if "extra" in exp_file:
                    continue
                full_path = f"{exp_path}/{exp_file}"
                data = read_document(full_path)
                # make id legal on firebase
                id = full_path.replace("/","-")
                # remove unnecessary experiment info
                span = re.search("exp_narrative", id).span()
                id = id[0:span[1]+2]
                file_object = {}
                file_object["text"] = data
                hash_text = hashlib.md5(id.encode()).hexdigest()
                file_object["verificationCode"] = hash_text
                verification_codes.append(hash_text)
                json_source_dict[id] = file_object
                for i in range(0, num_duplicate):
                    experiments_to_run.append(id)
    print(f"Created {len(experiments_to_run)} experiments")
    print(f"With {len(verification_codes)} verification codes")
    json_source_dict["experiments_to_run"] = experiments_to_run
    json_source_dict["verification_codes"] = verification_codes
    json_source_dict["experiments_finished"] = experiments_finished
    input("Upload to firebase?")

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
    results = db.child("experiment_data").set(json_source_dict, user['idToken'])
