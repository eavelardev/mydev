#!/bin/bash

# Script to pull all git repositories in the current directory

target_dir="${1:-.}"

if [ ! -d "$target_dir" ]; then
    echo "Error: '$target_dir' is not a valid directory"
    echo "Usage: $0 [folder_path]"
    exit 1
fi

shopt -s nullglob

for dir in "$target_dir"/*/; do
    if [ -d "$dir/.git" ]; then
        echo "Pulling $dir"
        (
            cd "$dir" || exit
            git pull
        )
    else
        echo "$dir is not a git repository"
    fi
done