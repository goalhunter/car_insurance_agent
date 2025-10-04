# Deployment Checklist

Use this checklist when setting up the project or before pushing to GitHub.

## ✅ Pre-GitHub Push Checklist

- [ ] Remove all hardcoded AWS credentials from code
- [ ] Verify `.env` is in `.gitignore`
- [ ] Verify `aws_env/` is in `.gitignore`
- [ ] Verify generated data files (`.csv`, `.json`) are in `.gitignore`
- [ ] No AWS account-specific files (action groups, agent configs) are committed
- [ ] README.md is comprehensive and up-to-date
- [ ] `.env.example` exists for reference
- [ ] Run: `git status` to verify only safe files will be committed

## 🔒 Security Checks

### Files That Should NEVER Be Committed:
- ❌ `.env` (contains credentials)
- ❌ `aws_env/` (virtual environment)
- ❌ `*.csv` files with real data
- ❌ `*.json` files with real data
- ❌ `bedrock_agent_config.json` (contains account info)
- ❌ `action_group_*.json` (contains ARNs)

### Files That SHOULD Be Committed:
- ✅ `.env.example` (template only)
- ✅ `.gitignore`
- ✅ `README.md`
- ✅ `requirements.txt`
- ✅ All Lambda function code
- ✅ Data generation scripts
- ✅ Deployment scripts (`update_lambdas.py`)

## 🚀 Fresh Setup (For Others Using Your Repo)

1. **Clone the repository**
   ```bash
   git clone <your-repo>
   cd car_insurance_agent
   ```

2. **Create virtual environment**
   ```bash
   python -m venv aws_env
   source aws_env/Scripts/activate  # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure AWS**
   ```bash
   aws configure
   # Enter: Access Key, Secret Key, Region (us-east-1), Format (json)
   ```

5. **Create DynamoDB tables** (via AWS Console or CLI)
   - customers (PK: customer_id)
   - policies (PK: policy_id)
   - vehicles (PK: vehicle_id)
   - claims-records (PK: claim_id)

6. **Generate and migrate data**
   ```bash
   python synthetic_data_generation/generate_and_migrate.py
   ```

7. **Deploy Lambda functions**
   ```bash
   python update_lambdas.py
   ```

8. **Create Bedrock Agent** (AWS Console)
   - Follow README.md instructions

## 📝 Before Each Commit

```bash
# Check what will be committed
git status

# Verify no sensitive files
git diff --cached

# Look for any credentials that might have leaked
grep -r "AKIA" --exclude-dir=aws_env --exclude-dir=.git .
grep -r "aws_secret" --exclude-dir=aws_env --exclude-dir=.git .
```

## 🔄 Updating Lambda Functions

After making changes to Lambda code:

```bash
python update_lambdas.py
```

This will package and deploy all functions to AWS.

## 🧪 Testing

1. Test in Bedrock Agent console first
2. Check CloudWatch Logs for each Lambda
3. Verify DynamoDB data is correct
4. Test all 5 steps of claim filing

## 📊 Monitoring

- **CloudWatch Logs**: Monitor Lambda execution
- **DynamoDB**: Check item counts and data
- **Bedrock**: Review agent conversations
- **Cost Explorer**: Monitor AWS costs

## 🆘 Troubleshooting

See `LAMBDA_FIX_GUIDE.md` for common issues.

### Quick Checks:
- Lambda timeout: Increase to 30s for image/document analysis
- IAM Permissions: Lambda needs DynamoDB, S3, Bedrock, Textract
- Bedrock Model Access: Enable Claude 3.5 and 3.7 Sonnet
- S3 Bucket: Ensure bucket exists and Lambda can access it

## 🔐 Security Best Practices

1. **Never hardcode credentials**
   - Use AWS CLI configured credentials
   - Use IAM roles for Lambda in production
   - Rotate access keys regularly

2. **Least privilege**
   - Lambda roles should only have necessary permissions
   - Use resource-based policies where possible

3. **Data protection**
   - Don't commit real customer data
   - Use synthetic data for testing
   - Encrypt sensitive data in DynamoDB

4. **API security**
   - Use Bedrock Agent authentication
   - Implement rate limiting
   - Log all claim activities

## ✨ Post-Deployment

- [ ] Test complete claim flow
- [ ] Verify all Lambda logs show no errors
- [ ] Check DynamoDB for claim records
- [ ] Document any custom configurations
- [ ] Share repo with team (if applicable)
