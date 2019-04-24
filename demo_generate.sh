#!/bin/bash

clear;

folder_path=experiment_output/demo

python fetch.py play_dialogue_index.obj glove-wiki-gigaword-50 demo_narratives $folder_path 1-0 1 yes A-B
