#!/bin/bash

eval "$(conda shell.bash hook)"
conda activate rad
myport="${1:-8000}"
uvicorn servers:app --reload --port $myport --app-dir /home/kobayashi/Scrivania/andreasala/covid-classifier/web_interface
