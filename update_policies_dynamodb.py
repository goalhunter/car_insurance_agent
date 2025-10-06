import boto3
import csv
from decimal import Decimal

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('policies')

def delete_all_policies():
    """Delete all items from the policies table"""
    print("Scanning and deleting all existing policies...")

    scan = table.scan()
    items = scan.get('Items', [])

    with table.batch_writer() as batch:
        for item in items:
            batch.delete_item(Key={'policy_id': item['policy_id']})
            print(f"Deleted policy: {item['policy_id']}")

    # Handle pagination if there are more items
    while 'LastEvaluatedKey' in scan:
        scan = table.scan(ExclusiveStartKey=scan['LastEvaluatedKey'])
        items = scan.get('Items', [])
        with table.batch_writer() as batch:
            for item in items:
                batch.delete_item(Key={'policy_id': item['policy_id']})
                print(f"Deleted policy: {item['policy_id']}")

    print(f"[OK] All policies deleted")

def upload_policies_from_csv():
    """Upload policies from CSV to DynamoDB"""
    print("\nUploading new policies from CSV...")

    csv_file = 'synthetic_data_generation/policies.csv'

    with open(csv_file, 'r') as file:
        reader = csv.DictReader(file)

        with table.batch_writer() as batch:
            count = 0
            for row in reader:
                # Convert numeric values to Decimal for DynamoDB
                item = {
                    'policy_id': row['policy_id'],
                    'policy_number': row['policy_number'],
                    'policy_type': row['policy_type'],
                    'policy_start_date': row['policy_start_date'],
                    'policy_end_date': row['policy_end_date'],
                    'premium_amount': Decimal(str(row['premium_amount'])),
                    'payment_frequency': row['payment_frequency'],
                    'coverage_amount': Decimal(str(row['coverage_amount'])),
                    'deductible_amount': Decimal(str(row['deductible_amount'])),
                    'policy_status': row['policy_status'],
                    'customer_id': row['customer_id']
                }

                batch.put_item(Item=item)
                count += 1
                print(f"Uploaded policy: {row['policy_number']} (ID: {row['policy_id'][:8]}...)")

    print(f"\n[OK] Successfully uploaded {count} policies")

if __name__ == '__main__':
    print("=" * 60)
    print("Updating Policies in DynamoDB")
    print("=" * 60)

    # Step 1: Delete all existing policies
    delete_all_policies()

    # Step 2: Upload new policies from CSV
    upload_policies_from_csv()

    print("\n" + "=" * 60)
    print("[OK] Policies table updated successfully!")
    print("=" * 60)
