"""
Infrastructure Setup Script
Creates DynamoDB tables for the claims processing system
"""

import boto3
import sys
import os
from botocore.exceptions import ClientError

# Add parent directory to path to import config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DYNAMODB_TABLES, AWS_REGION


def create_dynamodb_tables():
    """Create all required DynamoDB tables"""
    print("=" * 60)
    print("CREATING DYNAMODB TABLES")
    print("=" * 60)

    dynamodb = boto3.client('dynamodb', region_name=AWS_REGION)

    created_tables = []
    existing_tables = []
    failed_tables = []

    for table_key, table_config in DYNAMODB_TABLES.items():
        table_name = table_config['table_name']
        partition_key = table_config['partition_key']
        billing_mode = table_config['billing_mode']

        print(f"\nProcessing table: {table_name}")

        try:
            # Check if table exists
            try:
                dynamodb.describe_table(TableName=table_name)
                print(f"  [EXISTS] Table '{table_name}' already exists")
                existing_tables.append(table_name)
                continue
            except ClientError as e:
                if e.response['Error']['Code'] != 'ResourceNotFoundException':
                    raise

            # Create table
            table_params = {
                'TableName': table_name,
                'KeySchema': [
                    {
                        'AttributeName': partition_key,
                        'KeyType': 'HASH'
                    }
                ],
                'AttributeDefinitions': [
                    {
                        'AttributeName': partition_key,
                        'AttributeType': 'S'
                    }
                ],
                'BillingMode': billing_mode
            }

            response = dynamodb.create_table(**table_params)
            print(f"  [CREATED] Table '{table_name}' created successfully")
            created_tables.append(table_name)

            # Wait for table to be active
            print(f"  [WAITING] Waiting for table '{table_name}' to be active...")
            waiter = dynamodb.get_waiter('table_exists')
            waiter.wait(TableName=table_name)
            print(f"  [ACTIVE] Table '{table_name}' is now active")

        except Exception as e:
            print(f"  [ERROR] Failed to create table '{table_name}': {str(e)}")
            failed_tables.append(table_name)

    # Summary
    print("\n" + "=" * 60)
    print("DYNAMODB SETUP SUMMARY")
    print("=" * 60)
    print(f"Created: {len(created_tables)} table(s)")
    for table in created_tables:
        print(f"  - {table}")

    if existing_tables:
        print(f"\nAlready Existed: {len(existing_tables)} table(s)")
        for table in existing_tables:
            print(f"  - {table}")

    if failed_tables:
        print(f"\nFailed: {len(failed_tables)} table(s)")
        for table in failed_tables:
            print(f"  - {table}")
        return False

    print(f"\nTotal Tables: {len(DYNAMODB_TABLES)}")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = create_dynamodb_tables()
    sys.exit(0 if success else 1)
