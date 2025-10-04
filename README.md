# Car Insurance Claims Processing Agent

An intelligent AI-powered car insurance claims processing system built with AWS Bedrock Agents, Lambda functions, and DynamoDB.

## Overview

This project implements a conversational AI agent that guides users through a 5-step car insurance claim filing process:

1. **Customer Verification** - Verify identity using name and email
2. **Policy Verification** - Validate policy status and coverage
3. **Damage Analysis** - Analyze damage images and match vehicle details
4. **Document Analysis** - Process police reports and repair estimates
5. **Settlement Decision** - Generate comprehensive claim decision with reasoning

## Architecture

```
┌─────────────────────────────┐
│   Bedrock Agent             │
│   (Claude 3.7 Sonnet)       │
└──────────┬──────────────────┘
           │
           ├──► customerVerification (Lambda)
           ├──► policyVerification (Lambda)
           ├──► analyzeDamageImages (Lambda)
           ├──► analyzeDocuments (Lambda)
           └──► generateSettlementDecision (Lambda)
                      │
                      ▼
           ┌──────────────────────┐
           │   DynamoDB Tables     │
           ├──────────────────────┤
           │ • customers          │
           │ • policies           │
           │ • vehicles           │
           │ • claims-records     │
           └──────────────────────┘
```

## Features

### 🔍 Intelligent Verification
- Customer identity validation via DynamoDB lookup
- Policy status and expiration checking
- Customer-policy relationship validation

### 🚗 AI-Powered Damage Analysis
- Visual analysis of car damage using Claude 3.5 Sonnet vision
- Vehicle matching (compares images to policy vehicle details)
- Estimated repair cost calculation
- Crash reason analysis
- Damage severity assessment

### 📄 Document Processing
- Automated text extraction using AWS Textract
- Police report analysis
- Repair estimate validation
- Cross-verification between documents and images
- Fraud indicator detection

### 🤖 Comprehensive Settlement Decision
- Multi-factor claim analysis
- Risk assessment (low/medium/high)
- Genuine vs suspicious factors identification
- Detailed reasoning with supporting evidence
- Approval/denial recommendations
- Cost breakdown (customer pays vs insurance pays)

## Project Structure

```
car_insurance_agent/
├── lambda_functions/           # AWS Lambda function code
│   ├── customerVerification/
│   ├── policyVerification/
│   ├── analyzeDamageImages/
│   ├── analyzeDocuments/
│   └── generateSettlementDecision/
├── synthetic_data_generation/  # Data generation and migration scripts
│   ├── generate_and_migrate.py
│   └── insurance_policy_data.py
├── update_lambdas.py          # Script to deploy Lambda functions
├── LAMBDA_FIX_GUIDE.md        # Lambda troubleshooting guide
└── README.md
```

## Setup

### Prerequisites

- AWS Account with access to:
  - Amazon Bedrock (Claude 3.7 Sonnet and Claude 3.5 Sonnet)
  - AWS Lambda
  - Amazon DynamoDB
  - Amazon S3
  - Amazon Textract
- Python 3.8+
- AWS CLI configured

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd car_insurance_agent
   ```

2. **Create virtual environment**
   ```bash
   python -m venv aws_env
   source aws_env/Scripts/activate  # Windows
   # or
   source aws_env/bin/activate      # Linux/Mac
   ```

3. **Install dependencies**
   ```bash
   pip install boto3 pandas
   pip install awscli
   ```

4. **Configure AWS credentials**
   ```bash
   aws configure
   # Enter your AWS Access Key ID, Secret Access Key, and region
   ```

### Database Setup

1. **Create DynamoDB tables**
   - `customers` (partition key: `customer_id`)
   - `policies` (partition key: `policy_id`)
   - `vehicles` (partition key: `vehicle_id`)
   - `claims-records` (partition key: `claim_id`)

2. **Generate and load synthetic data**
   ```bash
   python synthetic_data_generation/generate_and_migrate.py
   ```

### Lambda Functions Deployment

1. **Deploy all Lambda functions**
   ```bash
   python update_lambdas.py
   ```

2. **Configure Lambda permissions**
   - Add DynamoDB read/write permissions
   - Add S3 read permissions
   - Add Bedrock invoke permissions
   - Add Textract permissions

### Bedrock Agent Setup

1. **Create a Bedrock Agent**
   - Model: Claude 3.7 Sonnet
   - Instructions: Copy from the agent configuration

2. **Create Action Groups**
   - `verifyCustomer` → customerVerification Lambda
   - `verifyPolicy` → policyVerification Lambda
   - `analyzeDamageImages` → analyzeDamageImages Lambda
   - `analyzeDocuments` → analyzeDocuments Lambda
   - `generateSettlement` → generateSettlementDecision Lambda

3. **Test the agent**

## Usage

### Example Conversation Flow

```
User: I want to file a claim

Agent: Hello! I'll help you file a car insurance claim. Let's start with
       customer verification. Please provide:
       - First name
       - Last name
       - Email address

User: Michael, Johnson, michael.johnson@example.com

Agent: Customer verified! Now, please provide your policy ID.

User: f8c3de3d-1d35-4b77-9b4e-8f1c8b8e1f2a

Agent: Policy verified! Please upload damage images to S3 and provide:
       - S3 URIs for images
       - Vehicle ID

User: s3://bucket/damage1.jpg, vehicle-id-123

Agent: Damage analyzed! Please provide:
       - Police report S3 URI
       - Repair estimate S3 URI

User: s3://bucket/police.pdf, s3://bucket/estimate.pdf

Agent: All documents analyzed! Generating settlement decision...

[Agent provides comprehensive decision with approval/denial, reasoning,
 and next steps]
```

## Key Technologies

- **AWS Bedrock** - AI foundation models (Claude 3.5 & 3.7 Sonnet)
- **AWS Lambda** - Serverless compute
- **Amazon DynamoDB** - NoSQL database
- **Amazon S3** - Object storage
- **Amazon Textract** - Document text extraction
- **Python** - Backend logic
- **Boto3** - AWS SDK for Python

## Lambda Function Details

### customerVerification
- Validates customer identity against DynamoDB
- Returns customer data if verified

### policyVerification
- Checks policy status, expiration, and customer ownership
- Validates policy is active and unexpired

### analyzeDamageImages
- Downloads images from S3
- Analyzes damage using Claude vision
- Verifies vehicle matches policy
- Estimates repair costs

### analyzeDocuments
- Extracts text using Textract
- Analyzes police reports and estimates
- Cross-verifies with damage analysis
- Identifies inconsistencies

### generateSettlementDecision
- Synthesizes all claim data
- Performs risk assessment
- Generates detailed reasoning
- Provides approval/denial recommendation
- Saves to claims-records table

## Security Considerations

⚠️ **Important**: Never commit sensitive data to the repository!

- `.env` files are git-ignored
- AWS credentials should only be in AWS CLI config
- Generated CSV/JSON data is git-ignored
- Use IAM roles for Lambda functions in production

## Troubleshooting

See [LAMBDA_FIX_GUIDE.md](LAMBDA_FIX_GUIDE.md) for common issues and fixes.

### Common Issues

1. **"functionResponse object is required"**
   - Lambda functions now handle both old and new Bedrock Agent formats
   - Ensure latest code is deployed

2. **DynamoDB Permission Errors**
   - Add appropriate IAM policies to Lambda execution roles

3. **Bedrock Access Denied**
   - Enable model access in AWS Bedrock console
   - Add bedrock:InvokeModel permission

## Future Enhancements

- [ ] PDF report generation for claims
- [ ] Email notifications to customers
- [ ] Integration with payment systems
- [ ] Multi-language support
- [ ] Mobile app integration
- [ ] Real-time claim status tracking
- [ ] Analytics dashboard

## License

This project is provided as-is for educational and demonstration purposes.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## Author

Built with AWS Bedrock Agents and Claude AI
