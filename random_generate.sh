#!/bin/bash
clear;

for i in 0 1 2 3 4 5 6 7 8 9
do
    folder_path=$1/$i
    echo $folder_path
    mkdir $folder_path
done

python fetch_random.py play_dialogue_index.obj experiment_narratives random_output 0-0-0
