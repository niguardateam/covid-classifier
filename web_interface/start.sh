#!/bin/bash

eval "$(conda shell.bash hook)"
conda activate lungs
uvicorn servers:app --reload
