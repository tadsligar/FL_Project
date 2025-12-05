#!/bin/bash
# Demo script for Clinical MAS Planner

set -e

echo "========================================="
echo "Clinical MAS Planner - Demo"
echo "========================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "Error: .env file not found. Please copy .env.example to .env and add your API keys."
    exit 1
fi

# Example 1: Cardiac case
echo "Running Example 1: Cardiac case"
echo "---"
poetry run mas run \
    --question "A 65-year-old man presents with sudden onset chest pain radiating to the left arm, diaphoresis, and nausea. Pain started 30 minutes ago. Which of the following is the most likely diagnosis?" \
    --options "A. GERD||B. Acute Myocardial Infarction||C. Pulmonary Embolism||D. Musculoskeletal pain"

echo ""
echo "========================================="
echo ""

# Example 2: Pediatric case
echo "Running Example 2: Pediatric case"
echo "---"
poetry run mas run \
    --question "A 3-year-old boy is brought to the emergency department with a barking cough, stridor, and fever. His mother reports symptoms started 2 days ago. What is the most likely diagnosis?" \
    --options "A. Epiglottitis||B. Croup||C. Asthma||D. Foreign body aspiration"

echo ""
echo "========================================="
echo "Demo complete!"
echo "========================================="
