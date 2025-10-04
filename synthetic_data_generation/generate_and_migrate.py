import boto3
import json
import pandas as pd
import re
from decimal import Decimal

def generate_insurance_data():
    """Generate synthetic insurance data using Bedrock"""
    print("Generating synthetic insurance data using Bedrock...")

    # Initialize the Bedrock client using AWS CLI configured credentials
    bedrock_runtime = boto3.client(
        service_name="bedrock-runtime",
        region_name="us-east-1"
    )

    # The prompt to generate the data
    prompt = """
        Generate a comprehensive synthetic dataset for a car insurance claims processing system. The data must be in valid JSON format with exactly 5 complete records.

        Create four related tables with the following structure:

        1. POLICIES table fields:
        - policy_id (UUID format)
        - policy_number (format: POL-2025-XXXXX where X is random digit)
        - policy_type (varied: Comprehensive, Third-Party, Collision Only, Liability Only, Full Coverage)
        - policy_start_date (YYYY-MM-DD, dates in 2024-2025)
        - policy_end_date (YYYY-MM-DD, typically 6-12 months after start)
        - premium_amount (realistic: $500-$3000 annually)
        - payment_frequency (Monthly, Quarterly, Semi-Annually, Annually)
        - coverage_amount (realistic: $50,000-$500,000)
        - deductible_amount (realistic: $250, $500, $1000, $2500)
        - policy_status (Active, Expired, Cancelled, Lapsed - mostly Active)
        - customer_id (UUID linking to customers table)

        2. CUSTOMERS table fields:
        - customer_id (UUID format)
        - first_name (realistic first names, varied)
        - last_name (realistic last names, varied)
        - age (18-85, realistic distribution)
        - date_of_birth (YYYY-MM-DD, must match age)
        - gender (Male, Female, Non-binary)
        - marital_status (Single, Married, Divorced, Widowed)
        - street_address (realistic street addresses)
        - city (varied US cities)
        - state (US state abbreviations)
        - zip_code (5-digit US ZIP codes)
        - country (USA)
        - phone
        - email
        - driving_license_number (format: DL-STATE-XXXXXXXX)
        - driving_experience_years (logical based on age, minimum 0, maximum age-16)
        - previous_claims_count (0-5, mostly 0-2)

        3. VEHICLES table fields:
        - vehicle_id (UUID format)
        - policy_id (UUID linking to policies table)
        - customer_id (UUID linking to customers table - same as policy)
        - vehicle_type (Car, SUV, Truck, Motorcycle, Van)
        - make (varied: Toyota, Honda, Ford, Chevrolet, BMW, Mercedes, Tesla, Nissan, etc.)
        - model (realistic models matching the make)
        - color (common colors)
        - year_of_manufacture (2000-2025, realistic distribution favoring newer)
        - registration_number (format: XXX-XXXX or XX-XXXXX realistic plates)
        - vin (17-character alphanumeric VIN)
        - engine_size
        - fuel_type
        - odometer_reading (realistic based on year: newer = lower miles)
        - vehicle_value (realistic market value: $5,000-$80,000)
        - anti_theft_device (true/false)

        4. COVERAGE table fields:
        - coverage_id (UUID format)
        - policy_id (UUID linking to policies table)
        - coverage_type (Bodily Injury Liability, Property Damage Liability, Collision, Comprehensive, Personal Injury Protection, Uninsured Motorist, Medical Payments)
        - coverage_limit (dollar amounts)

        CRITICAL REQUIREMENTS:
        - Generate EXACTLY 5 records for each table

        OUTPUT FORMAT:
        Return ONLY a valid JSON object with this exact structure:
        {
        "policies": [array of 5 policy objects],
        "customers": [array of 5 customer objects],
        "vehicles": [array of 5 vehicle objects],
        "coverages": [array of 5 coverage objects]
        }

        Do not include any markdown formatting, code blocks, explanations, or additional text. Output must be pure, valid JSON that can be parsed directly.
        """

    # Set up the request payload
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 4500,
        "temperature": 0.1,
        "messages": [
            {
                "role": "user",
                "content": prompt + "\n\nIMPORTANT: Your response must contain ONLY valid JSON, starting with { and ending with }. No markdown, no explanations."
            }
        ]
    })

    try:
        # Call the Anthropic Claude model
        response = bedrock_runtime.invoke_model(
            modelId="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
            body=body
        )

        # Process the response
        response_body = json.loads(response.get("body").read())
        generated_text = response_body.get("content")[0].get("text")

        # Extract JSON using regex
        json_pattern = r'(?s)\{.*\}'
        match = re.search(json_pattern, generated_text)

        if match:
            json_str = match.group(0)
            data = json.loads(json_str)

            # Save the data to a file
            with open('insurance_data.json', 'w') as f:
                json.dump(data, f, indent=2)

            print(f"✅ Successfully generated insurance data")
            return data
        else:
            print("❌ Could not find JSON content in the response")
            return None

    except Exception as e:
        print(f"❌ Error calling Bedrock: {e}")
        return None


def convert_floats_to_decimal(obj):
    """Convert float values to Decimal for DynamoDB compatibility"""
    if isinstance(obj, list):
        return [convert_floats_to_decimal(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: convert_floats_to_decimal(value) for key, value in obj.items()}
    elif isinstance(obj, float):
        return Decimal(str(obj))
    else:
        return obj


def migrate_to_dynamodb(data):
    """Migrate generated data directly to DynamoDB"""
    print("\nMigrating data to DynamoDB...")

    # Initialize DynamoDB using AWS CLI configured credentials
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

    # Define table mappings
    tables = {
        'customers': 'customers',
        'policies': 'policies',
        'vehicles': 'vehicles',
        'coverages': 'coverages'
    }

    for table_name, dynamo_table_name in tables.items():
        if table_name not in data:
            print(f"⚠️  Skipping {table_name} - not found in generated data")
            continue

        print(f"\nMigrating {table_name}...")
        table = dynamodb.Table(dynamo_table_name)
        records = data[table_name]

        # Convert floats to Decimal for DynamoDB
        records = convert_floats_to_decimal(records)

        success_count = 0
        for record in records:
            try:
                table.put_item(Item=record)
                success_count += 1
            except Exception as e:
                print(f"  ❌ Error inserting record: {e}")
                print(f"  Record: {record}")

        print(f"  ✅ {success_count}/{len(records)} records migrated to {table_name}")

    print("\n🎉 Migration completed!")


def verify_migration():
    """Verify data was migrated successfully"""
    print("\nVerifying migration...")

    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

    tables = ['customers', 'policies', 'vehicles', 'coverages']

    for table_name in tables:
        try:
            table = dynamodb.Table(table_name)
            response = table.scan()
            count = response['Count']
            print(f"  {table_name}: {count} items")
        except Exception as e:
            print(f"  ❌ Error checking {table_name}: {e}")


if __name__ == "__main__":
    # Step 1: Generate synthetic data
    data = generate_insurance_data()

    if data:
        # Step 2: Migrate to DynamoDB
        migrate_to_dynamodb(data)

        # Step 3: Verify migration
        verify_migration()
    else:
        print("❌ Failed to generate data. Migration aborted.")
