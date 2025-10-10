import boto3
import csv

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('vehicles')

def delete_all_vehicles():
    """Delete all items from the vehicles table"""
    print("Scanning and deleting all existing vehicles...")

    scan = table.scan()
    items = scan.get('Items', [])

    with table.batch_writer() as batch:
        for item in items:
            batch.delete_item(Key={'vehicle_id': item['vehicle_id']})
            print(f"Deleted vehicle: {item['vehicle_id']}")

    # Handle pagination if there are more items
    while 'LastEvaluatedKey' in scan:
        scan = table.scan(ExclusiveStartKey=scan['LastEvaluatedKey'])
        items = scan.get('Items', [])
        with table.batch_writer() as batch:
            for item in items:
                batch.delete_item(Key={'vehicle_id': item['vehicle_id']})
                print(f"Deleted vehicle: {item['vehicle_id']}")

    print(f"[OK] All vehicles deleted")

def upload_vehicles_from_csv():
    """Upload vehicles from CSV to DynamoDB"""
    print("\nUploading new vehicles from CSV...")

    csv_file = 'synthetic_data_generation/vehicles.csv'

    with open(csv_file, 'r') as file:
        reader = csv.DictReader(file)

        with table.batch_writer() as batch:
            count = 0
            for row in reader:
                item = {
                    'vehicle_id': row['vehicle_id'],
                    'policy_id': row['policy_id'],
                    'customer_id': row['customer_id'],
                    'vehicle_type': row['vehicle_type'],
                    'make': row['make'],
                    'model': row['model'],
                    'color': row['color'],
                    'year_of_manufacture': row['year_of_manufacture'],
                    'registration_number': row['registration_number'],
                    'vin': row['vin'],
                    'engine_size': row['engine_size'],
                    'fuel_type': row['fuel_type'],
                    'odometer_reading': row['odometer_reading'],
                    'vehicle_value': row['vehicle_value'],
                    'anti_theft_device': row['anti_theft_device']
                }

                batch.put_item(Item=item)
                count += 1
                print(f"Uploaded vehicle: {row['year_of_manufacture']} {row['make']} {row['model']} (ID: {row['vehicle_id'][:8]}...)")

    print(f"\n[OK] Successfully uploaded {count} vehicles")

if __name__ == '__main__':
    print("=" * 60)
    print("Updating Vehicles in DynamoDB")
    print("=" * 60)

    # Step 1: Delete all existing vehicles
    delete_all_vehicles()

    # Step 2: Upload new vehicles from CSV
    upload_vehicles_from_csv()

    print("\n" + "=" * 60)
    print("[OK] Vehicles table updated successfully!")
    print("=" * 60)
