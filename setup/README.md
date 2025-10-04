# Setup Scripts

This directory contains modular setup scripts for deploying the Car Insurance Claims Processing Agent.

## Scripts

### `setup_infrastructure.py`
Creates all required DynamoDB tables:
- customers
- policies
- vehicles
- claims-records

**Usage:**
```bash
python setup/setup_infrastructure.py
```

### `setup_lambda.py`
- Creates IAM role for Lambda functions
- Deploys all 5 Lambda functions
- Configures permissions (DynamoDB, S3, Bedrock, Textract)

**Usage:**
```bash
python setup/setup_lambda.py
```

### `setup_agent.py`
- Creates IAM role for Bedrock Agent
- Creates Bedrock Agent
- Sets up 5 action groups
- Links Lambda functions to action groups
- Prepares agent for use

**Usage:**
```bash
python setup/setup_agent.py
```

## Configuration

All scripts use settings from `config.py` in the project root. Customize:
- Table names
- Lambda configuration (timeout, memory)
- Agent instructions
- Action group schemas
- AWS region

## Notes

- Scripts are idempotent - safe to run multiple times
- Existing resources will be updated, not recreated
- Check AWS Console for detailed status
- IAM roles may take 10-15 seconds to propagate
