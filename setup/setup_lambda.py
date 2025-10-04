"""
Lambda Functions Setup Script
Creates/updates Lambda functions and IAM roles
"""

import boto3
import sys
import os
import zipfile
import io
import json
import time
from botocore.exceptions import ClientError

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import LAMBDA_FUNCTIONS, AWS_REGION, IAM_ROLES, DYNAMODB_TABLES


def create_lambda_execution_role(iam_client):
    """Create IAM role for Lambda execution"""
    role_name = IAM_ROLES['lambda_role_name']

    print(f"\n[IAM] Checking Lambda execution role: {role_name}")

    try:
        # Check if role exists
        role = iam_client.get_role(RoleName=role_name)
        print(f"  [EXISTS] Role already exists")
        return role['Role']['Arn']
    except ClientError as e:
        if e.response['Error']['Code'] != 'NoSuchEntity':
            raise

    # Create role
    print(f"  [CREATE] Creating role...")
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "lambda.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }]
    }

    role = iam_client.create_role(
        RoleName=role_name,
        AssumeRolePolicyDocument=json.dumps(trust_policy),
        Description='Execution role for Claims Processing Lambda functions'
    )

    role_arn = role['Role']['Arn']
    print(f"  [CREATED] Role ARN: {role_arn}")

    # Attach policies
    policies = [
        'arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole',
        'arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess',
        'arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess',
        'arn:aws:iam::aws:policy/AmazonTextractFullAccess'
    ]

    for policy_arn in policies:
        iam_client.attach_role_policy(RoleName=role_name, PolicyArn=policy_arn)
        print(f"  [ATTACHED] {policy_arn.split('/')[-1]}")

    # Attach Bedrock policy
    bedrock_policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Action": ["bedrock:InvokeModel"],
            "Resource": "*"
        }]
    }

    iam_client.put_role_policy(
        RoleName=role_name,
        PolicyName='BedrockInvokePolicy',
        PolicyDocument=json.dumps(bedrock_policy)
    )
    print(f"  [ATTACHED] BedrockInvokePolicy")

    # Wait for role to propagate
    print(f"  [WAITING] Waiting for role to propagate...")
    time.sleep(10)

    return role_arn


def create_lambda_zip(lambda_dir):
    """Create ZIP file from Lambda function directory"""
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for root, dirs, files in os.walk(lambda_dir):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, lambda_dir)
                    zip_file.write(file_path, arcname)

    zip_buffer.seek(0)
    return zip_buffer.read()


def deploy_lambda_functions(role_arn):
    """Deploy all Lambda functions"""
    print("\n" + "=" * 60)
    print("DEPLOYING LAMBDA FUNCTIONS")
    print("=" * 60)

    lambda_client = boto3.client('lambda', region_name=AWS_REGION)

    deployed = []
    failed = []

    for function_name, config in LAMBDA_FUNCTIONS.items():
        print(f"\nProcessing: {function_name}")

        try:
            # Create ZIP
            lambda_dir = os.path.join('lambda_functions', function_name)
            zip_content = create_lambda_zip(lambda_dir)

            # Check if function exists
            try:
                lambda_client.get_function(FunctionName=function_name)
                # Update existing function
                lambda_client.update_function_code(
                    FunctionName=function_name,
                    ZipFile=zip_content
                )
                print(f"  [UPDATED] Code updated")
                deployed.append(function_name)
            except ClientError as e:
                if e.response['Error']['Code'] != 'ResourceNotFoundException':
                    raise

                # Create new function
                lambda_client.create_function(
                    FunctionName=function_name,
                    Runtime=config['runtime'],
                    Role=role_arn,
                    Handler=config['handler'],
                    Code={'ZipFile': zip_content},
                    Description=config['description'],
                    Timeout=config['timeout'],
                    MemorySize=config['memory'],
                    Environment={'Variables': {'AWS_REGION': AWS_REGION}}
                )
                print(f"  [CREATED] Function created")
                deployed.append(function_name)

        except Exception as e:
            print(f"  [ERROR] {str(e)}")
            failed.append(function_name)

    # Summary
    print("\n" + "=" * 60)
    print("LAMBDA DEPLOYMENT SUMMARY")
    print("=" * 60)
    print(f"Deployed: {len(deployed)}/{len(LAMBDA_FUNCTIONS)}")
    for func in deployed:
        print(f"  - {func}")

    if failed:
        print(f"\nFailed: {len(failed)}")
        for func in failed:
            print(f"  - {func}")
        return False

    print("=" * 60)
    return True


def main():
    """Main setup function"""
    print("=" * 60)
    print("LAMBDA FUNCTIONS SETUP")
    print("=" * 60)

    # Create IAM role
    iam_client = boto3.client('iam', region_name=AWS_REGION)
    role_arn = create_lambda_execution_role(iam_client)

    # Deploy Lambda functions
    success = deploy_lambda_functions(role_arn)

    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
