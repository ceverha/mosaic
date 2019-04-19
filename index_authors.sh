#!/bin/bash

python dialogue_indexing.py ../corpus/data/authors chekhov new_index.obj new 0 .
python dialogue_indexing.py ../corpus/data/authors brieux_eugene new_index.obj no 0 .
python dialogue_indexing.py ../corpus/data/authors shaw_george_benard new_index.obj no 0 .
python dialogue_indexing.py ../corpus/data/authors oneill new_index.obj no 0 --
