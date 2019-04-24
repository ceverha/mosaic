#!/bin/bash
timestamp() {
  date +"%m-%d_%H:%M"
}
folder_path=experiment_output/$1-$(timestamp)
mkdir $folder_path
echo $folder_path

python fetch.py play_dialogue_index.obj glove-wiki-gigaword-100 experiment_narratives $folder_path 1-1-0-1-1 1 yes A-B-C
# python fetch.py play_dialogue_index.obj glove-wiki-gigaword-100 experiment_narratives $folder_path 1-1 1 no A-B-C
# python fetch.py subtitles_100.obj glove-wiki-gigaword-100 experiment_narratives $folder_path 1-1 1 no A-B-C
