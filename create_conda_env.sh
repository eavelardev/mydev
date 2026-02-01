#!/bin/bash

current_folder=$(basename "$(pwd)")
python_version="$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)"

if [ "$#" -ne 1 ]; then
    folder_name=$current_folder
else
    is_dir=$( [ -d "$1" ] && echo "true" || echo "false" )
    if [ "$is_dir" = "false" ]; then
        echo "ERROR: $1 is not a valid directory."
        exit 1
    fi

    folder_name=$([ "$1" = "." ] && echo "$current_folder" || echo "${1%/}")
fi

env_name=$folder_name

echo "Creating conda environment '$env_name' with Python $python_version ..."

conda create -n $env_name python=$python_version -y
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate $env_name

requirements_file="$folder_name/requirements.txt"

if [ ! -f "$requirements_file" ]; then
    echo "WARNING: $requirements_file does not exist."
else
    echo "Installing packages from $requirements_file ..."
    pip install -r "$folder_name/requirements.txt" -q
    echo "Packages installed."
fi
