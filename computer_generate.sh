#!/bin/bash
clear;

for i in 0 1 2 3 4 5 6 7 8 9
do
    folder_path=computer_output/$i
    echo $folder_path
    mkdir $folder_path
done

python fetch.py play_dialogue_index.obj glove-wiki-gigaword-100 experiment_narratives computer_output 0-0-0 1 yes A-B
