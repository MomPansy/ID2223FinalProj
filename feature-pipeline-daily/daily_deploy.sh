#!/bin/bash

# Variables
PROJECT_ID="id2223finalproj"
FUNCTION_NAME="daily-deploy-scheduler"
RUNTIME="python311"  # or the runtime you are using
TRIGGER_HTTP_METHOD="post"  # or "get" depending on your function
SCHEDULE="0 0 * * *"  # Daily at midnight
FUNCTION_SOURCE="/Users/jayden/Documents/GitHub/Exchange/id2223/finalproject/venv1/scrape"  
ENTRY_POINT="scrape_politifact"
REGION="europe-west3"

# Deploy Cloud Function
gcloud functions deploy "$FUNCTION_NAME" \
    --project "$PROJECT_ID" \
    --runtime "$RUNTIME" \
    --trigger-http \
    --entry-point "$ENTRY_POINT" \
    --source "$FUNCTION_SOURCE" \
    --region "$REGION"

# Get the URL of the deployed Cloud Function
FUNCTION_URL=$(gcloud functions describe "$FUNCTION_NAME" --region "$REGION" --format "value(httpsTrigger.url)")

echo "Deployed Cloud Function URL: $FUNCTION_URL"

# Create Cloud Scheduler Job
gcloud scheduler jobs create http "$FUNCTION_NAME-scheduler" \
    --project "$PROJECT_ID" \
    --schedule "$SCHEDULE" \
    --uri "$FUNCTION_URL" \
    --http-method "$TRIGGER_HTTP_METHOD" \
    --location "$REGION"

echo "Created Cloud Scheduler Job: $FUNCTION_NAME-scheduler"
