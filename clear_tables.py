import boto3

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

def clear_table(table_name, key_name):
    """Delete all items from a table while keeping the schema"""
    print(f"Clearing {table_name}...")
    table = dynamodb.Table(table_name)

    # Scan and delete all items
    scan = table.scan()

    with table.batch_writer() as batch:
        for item in scan['Items']:
            batch.delete_item(Key={key_name: item[key_name]})

    # Handle pagination if there are more items
    while 'LastEvaluatedKey' in scan:
        scan = table.scan(ExclusiveStartKey=scan['LastEvaluatedKey'])
        with table.batch_writer() as batch:
            for item in scan['Items']:
                batch.delete_item(Key={key_name: item[key_name]})

    print(f"✓ Cleared {table_name} (deleted {scan['Count']} items)\n")

if __name__ == '__main__':
    print("=" * 50)
    print("Clearing DynamoDB Tables")
    print("=" * 50 + "\n")

    try:
        clear_table('autosettled-customers', 'customer_id')
        clear_table('autosettled-policies', 'policy_id')
        clear_table('autosettled-vehicles', 'vehicle_id')

        print("=" * 50)
        print("✓ All tables cleared successfully!")
        print("=" * 50)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Make sure your AWS credentials are configured and tables exist.")
