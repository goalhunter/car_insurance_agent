import boto3
import csv

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

# Table references
customers_table = dynamodb.Table('autosettled-customers')
policies_table = dynamodb.Table('autosettled-policies')
vehicles_table = dynamodb.Table('autosettled-vehicles')

def load_customers():
    """Load customers from CSV"""
    print("Loading customers...")
    with open('dummy_data/customers.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # No type conversion - keep everything as string
            customers_table.put_item(Item=row)
            print(f"  Added customer: {row['first_name']} {row['last_name']}")
    print("✓ Customers loaded\n")

def load_policies():
    """Load policies from CSV"""
    print("Loading policies...")
    with open('dummy_data/policies.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # No type conversion - keep everything as string
            policies_table.put_item(Item=row)
            print(f"  Added policy: {row['policy_number']}")
    print("✓ Policies loaded\n")

def load_vehicles():
    """Load vehicles from CSV"""
    print("Loading vehicles...")
    with open('dummy_data/vehicles.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # No type conversion - keep everything as string
            vehicles_table.put_item(Item=row)
            print(f"  Added vehicle: {row['make']} {row['model']} ({row['registration_number']})")
    print("✓ Vehicles loaded\n")

if __name__ == '__main__':
    print("=" * 50)
    print("Loading Dummy Data into DynamoDB")
    print("=" * 50 + "\n")

    try:
        load_customers()
        load_policies()
        load_vehicles()

        print("=" * 50)
        print("✓ All data loaded successfully!")
        print("=" * 50)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Make sure your AWS credentials are configured and tables exist.")
