#!/bin/bash

BUCKET="s3://storycorps-signature-remote/"

# List all "folders"
FOLDERS=$(aws s3 ls ${BUCKET}/Processed/ --recursive | awk '{print $4}' | awk -F/ '{print $1}' | sort | uniq)

for folder in $FOLDERS
do
    # Count the number of files in each "folder"
    COUNT=$(aws s3 ls ${BUCKET}${folder} --recursive --summarize | grep "Total Objects: " | awk '{print $3}')
    echo "Folder: ${folder}, File Count: ${COUNT}"
done | sort -nrk4