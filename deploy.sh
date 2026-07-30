#!/usr/bin/env bash
# Cloud Run deployment script for ADK Market Intelligence Agent

set -e

PROJECT_ID=${GOOGLE_CLOUD_PROJECT:-$(gcloud config get-value project)}
REGION=${GOOGLE_CLOUD_REGION:-"us-central1"}
SERVICE_NAME="adk-market-intel-agent"

echo "=========================================================="
echo "🚀 Deploying ADK Market Intelligence Agent to Cloud Run"
echo "Project ID: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo "=========================================================="

gcloud builds submit --tag "gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest" .

gcloud run deploy ${SERVICE_NAME} \
  --image "gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest" \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --set-env-vars "GOOGLE_CLOUD_PROJECT=${PROJECT_ID},ENVIRONMENT=production"

echo "✅ Deployment completed successfully!"
