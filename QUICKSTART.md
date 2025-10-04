# Quick Start Guide

Get your Car Insurance Claims Processing Agent up and running in minutes!

## Prerequisites

- AWS Account with appropriate permissions
- Python 3.8 or higher
- AWS CLI configured (`aws configure`)

## One-Command Deployment

```bash
python deploy.py --all
```

That's it! The script will:
1. ✅ Create DynamoDB tables
2. ✅ Deploy 5 Lambda functions
3. ✅ Setup Bedrock Agent with action groups
4. ✅ Load synthetic data

**Deployment time:** ~2-3 minutes

## Step-by-Step (If you prefer manual control)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure AWS
```bash
aws configure
# Enter your Access Key, Secret Key, and Region (us-east-1 recommended)
```

### 3. Customize Configuration (Optional)
Edit `config.py` to customize:
- Table names
- Lambda settings
- Agent instructions
- Number of synthetic records

### 4. Deploy Infrastructure
```bash
python setup/setup_infrastructure.py
```

### 5. Deploy Lambda Functions
```bash
python setup/setup_lambda.py
```

### 6. Setup Bedrock Agent
```bash
python setup/setup_agent.py
```

### 7. Load Synthetic Data
```bash
python synthetic_data_generation/generate_and_migrate.py
```

## Selective Deployment

Deploy only specific components:

```bash
# Only DynamoDB tables
python deploy.py --infrastructure

# Only Lambda functions
python deploy.py --lambda

# Only Bedrock Agent
python deploy.py --agent

# Only synthetic data
python deploy.py --data
```

## Testing Your Agent

1. Go to **AWS Console** → **Amazon Bedrock** → **Agents**
2. Find **ClaimsProcessingAgent**
3. Click **Test**
4. Try: `I want to file a claim`

### Sample Test Flow

```
You: I want to file a claim

Agent: Let's start with customer verification. Please provide:
       - First name
       - Last name
       - Email address

You: Michael, Johnson, michael.johnson@example.com

Agent: Customer verified! Please provide your policy ID.

You: f8c3de3d-1d35-4b77-9b4e-8f1c8b8e1f2a

[Continue through the 5 steps...]
```

## Troubleshooting

### "Permission Denied" Errors
- Ensure AWS CLI is configured: `aws sts get-caller-identity`
- Check IAM permissions for Bedrock, Lambda, DynamoDB

### "Model Access Denied"
- Go to **Bedrock Console** → **Model Access**
- Enable **Claude 3.5 Sonnet** and **Claude 3.7 Sonnet**

### Lambda Functions Not Working
- Check CloudWatch Logs: AWS Console → CloudWatch → Log Groups
- Verify IAM role has required permissions

### Agent Not Responding
- Ensure agent is in **PREPARED** status
- Check action groups are **ENABLED**
- Verify Lambda permissions allow Bedrock to invoke

## What Gets Created

### DynamoDB Tables (4)
- `customers` - Customer records
- `policies` - Policy information
- `vehicles` - Vehicle details
- `claims-records` - Processed claims

### Lambda Functions (5)
- `customerVerification` - Verify customer identity
- `policyVerification` - Validate policy
- `analyzeDamageImages` - AI damage analysis
- `analyzeDocuments` - Process documents
- `generateSettlementDecision` - Create claim decision

### Bedrock Agent (1)
- `ClaimsProcessingAgent` - Conversational AI orchestrator

### IAM Roles (2)
- `ClaimsProcessingLambdaRole` - Lambda execution role
- `ClaimsProcessingAgentRole` - Agent execution role

## Clean Up

To avoid AWS charges, delete resources when done:

```bash
# Delete DynamoDB tables
aws dynamodb delete-table --table-name customers
aws dynamodb delete-table --table-name policies
aws dynamodb delete-table --table-name vehicles
aws dynamodb delete-table --table-name claims-records

# Delete Lambda functions
for func in customerVerification policyVerification analyzeDamageImages analyzeDocuments generateSettlementDecision; do
    aws lambda delete-function --function-name $func
done

# Delete Bedrock Agent (via Console - easier)
# Go to Bedrock → Agents → ClaimsProcessingAgent → Delete
```

## Cost Estimate

Typical costs for testing/development (per month):
- DynamoDB: $0-5 (on-demand pricing)
- Lambda: $0-2 (free tier covers most testing)
- Bedrock: $0.05-0.50 per claim (pay per use)
- **Total: ~$1-10/month for light testing**

## Next Steps

- Read [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) for production deployment
- Check [LAMBDA_FIX_GUIDE.md](LAMBDA_FIX_GUIDE.md) for troubleshooting
- See [README.md](README.md) for architecture details

## Support

- Check CloudWatch Logs for errors
- Review [GitHub Issues](https://github.com/your-repo/issues)
- AWS Documentation: [Bedrock Agents](https://docs.aws.amazon.com/bedrock/latest/userguide/agents.html)
