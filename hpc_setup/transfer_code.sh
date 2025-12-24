#!/bin/bash
# Transfer FL_Project to Easley HPC cluster
# Usage: ./transfer_code.sh <your-auburn-id>

if [ -z "$1" ]; then
    echo "Usage: ./transfer_code.sh <your-auburn-id>"
    echo "Example: ./transfer_code.sh abc0123"
    exit 1
fi

AUBURN_ID=$1
PROJECT_DIR="FL_Project"

echo "Transferring $PROJECT_DIR to Easley HPC cluster..."
echo "Target: ${AUBURN_ID}@easley.auburn.edu:~/"
echo ""

# Go to parent directory
cd ..

# Transfer project (excluding large files)
rsync -avz --exclude 'runs/' \
           --exclude 'data/' \
           --exclude '.git/' \
           --exclude '__pycache__/' \
           --exclude '*.pyc' \
           --exclude 'nul' \
           ${PROJECT_DIR}/ ${AUBURN_ID}@easley.auburn.edu:~/${PROJECT_DIR}/

echo ""
echo "Transfer complete!"
echo "To connect: ssh ${AUBURN_ID}@easley.auburn.edu"
