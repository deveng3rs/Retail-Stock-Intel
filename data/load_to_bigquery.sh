#!/bin/sh
# Load the generated CSVs into BigQuery dataset retail_stock.
# Run from the project root after:  python3 data/generate_seed.py
# Requires the dataset to exist (bq mk --dataset PROJECT_ID:retail_stock) and your account to have BigQuery access.
set -e
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
DATASET=retail_stock
LOCATION=asia-south1
echo "Loading into $PROJECT_ID:$DATASET ($LOCATION)"
for t in stores skus store_distances daily_sales batches; do
  bq --location=$LOCATION load --replace --source_format=CSV --skip_leading_rows=1 --autodetect \
     "$PROJECT_ID:$DATASET.$t" "data/out/$t.csv"
done
echo "Done. Check with:  bq ls $PROJECT_ID:$DATASET"
