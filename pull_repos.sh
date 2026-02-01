#!/bin/bash

# Script to pull all git repositories in the current directory

for dir in */; do
    if [ -d "$dir/.git" ]; then
        echo "Pulling $dir"
        cd "$dir"
        git pull
        cd ..
    else
        echo "$dir is not a git repository"
    fi
done