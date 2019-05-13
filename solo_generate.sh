#!/bin/bash
clear;
timestamp() {
  date +"%m-%d_%H:%M"
}
folder_path=experiment_output/$1_$(timestamp)
mkdir $folder_path
echo $folder_path

# fix this, consult fetch.py

for i in 0 1 2 3 4 5 6 7 8 9
do
    sub=$folder_path/$i
    echo $sub
    mkdir $sub
done

python fetch.py play_dialogue_index.obj glove-wiki-gigaword-50 experiment_narratives $folder_path 1-0-1 1 yes A-B
# python fetch.py play_dialogue_index.obj glove-wiki-gigaword-100 experiment_narratives $folder_path 1-0-1 1 no A-B
# python fetch.py subtitles_200.obj glove-wiki-gigaword-100 experiment_narratives $folder_path 1-0-1 1 no A-B
