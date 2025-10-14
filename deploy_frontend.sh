#!/bin/bash

# Deploy Frontend Script
# This script builds the React frontend and deploys it to S3 + CloudFront

set -e

echo "=========================================="
echo "Frontend Deployment Script"
echo "=========================================="

# Get stack name
STACK_NAME="autosettled-stack"

# Get outputs from CloudFormation stack
echo "Fetching CloudFormation stack outputs..."
FRONTEND_BUCKET=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --query "Stacks[0].Outputs[?OutputKey=='FrontendBucketName'].OutputValue" \
  --output text)

CLOUDFRONT_DISTRIBUTION_ID=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --query "Stacks[0].Outputs[?OutputKey=='CloudFrontDistributionId'].OutputValue" \
  --output text)

CLOUDFRONT_URL=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --query "Stacks[0].Outputs[?OutputKey=='CloudFrontURL'].OutputValue" \
  --output text)

API_URL=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" \
  --output text)

echo "Frontend Bucket: $FRONTEND_BUCKET"
echo "CloudFront Distribution ID: $CLOUDFRONT_DISTRIBUTION_ID"
echo "CloudFront URL: $CLOUDFRONT_URL"
echo "API URL: $API_URL"

# Navigate to frontend directory
cd frontend

# Update environment variables
echo "Updating environment variables..."
cat > .env.production << EOF
VITE_API_BASE_URL=https://52xcceuza5i7iuwmrri2xfsnoq0etomm.lambda-url.us-east-1.on.aws
VITE_UPLOAD_API_URL=https://ihjp2pdhub.execute-api.us-east-1.amazonaws.com/Prod
EOF

# Install dependencies
echo "Installing dependencies..."
npm install

# Build the frontend
echo "Building frontend..."
npm run build

# Sync build files to S3
echo "Uploading frontend to S3..."
aws s3 sync dist/ s3://$FRONTEND_BUCKET/ --delete

# Invalidate CloudFront cache
echo "Invalidating CloudFront cache..."
aws cloudfront create-invalidation \
  --distribution-id $CLOUDFRONT_DISTRIBUTION_ID \
  --paths "/*"

echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo "Frontend URL: https://$CLOUDFRONT_URL"
echo ""
echo "Note: CloudFront invalidation may take a few minutes to complete."
