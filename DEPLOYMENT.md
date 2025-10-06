# AutoSettled - AWS SAM Deployment Guide

## Prerequisites

1. **Install AWS SAM CLI**:
   ```bash
   pip install aws-sam-cli
   ```

2. **Configure AWS Credentials**:
   ```bash
   aws configure
   ```
   Enter your AWS Access Key ID, Secret Access Key, and default region.

3. **Get your Bedrock Agent details**:
   - Bedrock Agent ID
   - Bedrock Agent Alias ID

## Step 1: Update Parameters

Edit `template.yaml` and update these parameters:
```yaml
BedrockAgentId:
  Default: "YOUR_BEDROCK_AGENT_ID"  # Replace with your actual Agent ID

BedrockAgentAliasId:
  Default: "YOUR_BEDROCK_AGENT_ALIAS_ID"  # Replace with your actual Alias ID
```

## Step 2: Build the SAM Application

```bash
sam build
```

This will:
- Package all Lambda functions
- Resolve dependencies
- Prepare for deployment

## Step 3: Deploy to AWS

**First-time deployment (guided)**:
```bash
sam deploy --guided
```

You'll be prompted for:
- Stack Name: `autosettled-stack` (or your choice)
- AWS Region: `us-east-1` (or your preferred region)
- Parameter BedrockAgentId: (paste your Agent ID)
- Parameter BedrockAgentAliasId: (paste your Alias ID)
- Confirm changes before deploy: Y
- Allow SAM CLI IAM role creation: Y
- Disable rollback: N
- Save arguments to configuration file: Y

**Subsequent deployments**:
```bash
sam deploy
```

## Step 4: Get API Gateway URL

After deployment completes, look for the output:
```
Outputs
------------------------------------------------------------------------
Key                 ApiGatewayUrl
Description         API Gateway endpoint URL
Value               https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com/Prod/
```

Copy this URL!

## Step 5: Configure Frontend

1. Create `.env` file in the `frontend` folder:
   ```bash
   cd frontend
   echo "VITE_API_BASE_URL=https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com/Prod" > .env
   ```
   (Replace with your actual API Gateway URL)

2. Restart the frontend dev server

## Step 6: Upload Sample Data to DynamoDB

Upload your CSV data to the DynamoDB tables:

```bash
# Install boto3 if not already installed
pip install boto3 pandas

# Run the upload script (create this script to upload CSVs to DynamoDB)
python upload_data_to_dynamodb.py
```

## Testing the Deployment

1. **Test API Gateway**:
   ```bash
   curl https://your-api-url.amazonaws.com/Prod/claim/start -X POST
   ```

2. **Test from Frontend**:
   - Open http://localhost:5174
   - Click "File a Claim Now"
   - Enter customer ID or email
   - The chat should now connect to your AWS backend!

## Stack Resources Created

- ✅ API Gateway REST API
- ✅ 6 Lambda Functions (Orchestrator, FileUpload, + 4 agent functions)
- ✅ S3 Bucket for documents
- ✅ 3 DynamoDB Tables (Customers, Policies, Claims)
- ✅ IAM Roles and Policies

## Cleanup

To delete all resources:
```bash
sam delete
```

## Troubleshooting

**Build fails**:
- Make sure all lambda_function.py files exist in their directories
- Check Python syntax errors

**Deployment fails**:
- Check AWS credentials: `aws sts get-caller-identity`
- Verify Bedrock Agent ID and Alias ID are correct
- Check IAM permissions for creating resources

**API returns errors**:
- Check CloudWatch Logs: `sam logs -t --stack-name autosettled-stack`
- Verify environment variables in Lambda functions
- Test individual Lambda functions in AWS Console

## Environment Variables

The Lambda functions use these environment variables (auto-configured by SAM):
- `BEDROCK_AGENT_ID` - Your Bedrock Agent ID
- `BEDROCK_AGENT_ALIAS_ID` - Your Bedrock Agent Alias ID
- `S3_BUCKET_NAME` - Auto-created S3 bucket name
- `CUSTOMER_TABLE` - DynamoDB customers table
- `POLICY_TABLE` - DynamoDB policies table
- `CLAIMS_TABLE` - DynamoDB claims table
