#!/bin/bash
timestamp() {
  date +"%m-%d_%H:%M"
}
folder_path=experiment_output/demo-$(timestamp)
mkdir $folder_path
echo $folder_path

python fetch.py play_dialogue_index.obj glove-wiki-gigaword-50 demo_narratives $folder_path 1-0 1 yes A-B
