@echo off
setlocal enabledelayedexpansion

REM Deploy Frontend Script for Windows
REM This script builds the React frontend and deploys it to S3 + CloudFront

echo ==========================================
echo Frontend Deployment Script
echo ==========================================

REM Get stack name
set STACK_NAME=autosettled-stack

REM Get outputs from CloudFormation stack
echo Fetching CloudFormation stack outputs...

for /f "delims=" %%i in ('aws cloudformation describe-stacks --stack-name %STACK_NAME% --query "Stacks[0].Outputs[?OutputKey=='FrontendBucketName'].OutputValue" --output text') do set FRONTEND_BUCKET=%%i

for /f "delims=" %%i in ('aws cloudformation describe-stacks --stack-name %STACK_NAME% --query "Stacks[0].Outputs[?OutputKey=='CloudFrontDistributionId'].OutputValue" --output text') do set CLOUDFRONT_DISTRIBUTION_ID=%%i

for /f "delims=" %%i in ('aws cloudformation describe-stacks --stack-name %STACK_NAME% --query "Stacks[0].Outputs[?OutputKey=='CloudFrontURL'].OutputValue" --output text') do set CLOUDFRONT_URL=%%i

for /f "delims=" %%i in ('aws cloudformation describe-stacks --stack-name %STACK_NAME% --query "Stacks[0].Outputs[?OutputKey=='ApiGatewayUrl'].OutputValue" --output text') do set API_URL=%%i

echo Frontend Bucket: %FRONTEND_BUCKET%
echo CloudFront Distribution ID: %CLOUDFRONT_DISTRIBUTION_ID%
echo CloudFront URL: %CLOUDFRONT_URL%
echo API URL: %API_URL%

REM Navigate to frontend directory
cd frontend

REM Update environment variables
echo Updating environment variables...
(
echo VITE_API_BASE_URL=https://52xcceuza5i7iuwmrri2xfsnoq0etomm.lambda-url.us-east-1.on.aws
echo VITE_UPLOAD_API_URL=https://ihjp2pdhub.execute-api.us-east-1.amazonaws.com/Prod
) > .env.production

REM Install dependencies
echo Installing dependencies...
call npm install

REM Build the frontend
echo Building frontend...
call npm run build

REM Sync build files to S3
echo Uploading frontend to S3...
aws s3 sync dist/ s3://%FRONTEND_BUCKET%/ --delete

REM Invalidate CloudFront cache
echo Invalidating CloudFront cache...
aws cloudfront create-invalidation --distribution-id %CLOUDFRONT_DISTRIBUTION_ID% --paths "/*"

echo ==========================================
echo Deployment Complete!
echo ==========================================
echo Frontend URL: https://%CLOUDFRONT_URL%
echo.
echo Note: CloudFront invalidation may take a few minutes to complete.

cd ..
endlocal
