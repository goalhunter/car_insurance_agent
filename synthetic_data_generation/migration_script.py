"""
Legacy migration script - USE generate_and_migrate.py INSTEAD

This file is kept for reference but should NOT be used.
Use synthetic_data_generation/generate_and_migrate.py for all data generation and migration.
"""

import boto3

# Example: Check table counts (uses AWS CLI configured credentials)
def check_table_counts():
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

    tables = ['customers', 'policies', 'vehicles']

    for table_name in tables:
        try:
            table = dynamodb.Table(table_name)
            count = table.scan()['Count']
            print(f"{table_name}: {count} items")
        except Exception as e:
            print(f"Error checking {table_name}: {e}")

if __name__ == "__main__":
    print("Checking DynamoDB table counts...")
    check_table_counts()
