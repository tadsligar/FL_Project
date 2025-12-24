#!/bin/bash
# Quick connect script for Easley HPC cluster
# Usage: ./connect.sh <your-auburn-id>

if [ -z "$1" ]; then
    echo "Usage: ./connect.sh <your-auburn-id>"
    echo "Example: ./connect.sh abc0123"
    exit 1
fi

AUBURN_ID=$1

echo "Connecting to Easley HPC cluster as $AUBURN_ID..."
echo "You will be prompted for:"
echo "  1. Your Auburn password"
echo "  2. DUO two-factor authentication"
echo ""

ssh ${AUBURN_ID}@easley.auburn.edu
