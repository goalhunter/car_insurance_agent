import boto3
import json
import pandas as pd
import re

def generate_insurance_data():
    # Initialize the Bedrock client using your configured credentials
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
        
        # Save the raw response first for reference
        with open('raw_response.txt', 'w') as f:
            f.write(generated_text)
            
        print("Saved raw response to raw_response.txt")
        
        # Try to extract the JSON data using regex to find the outermost JSON object
        json_pattern = r'(?s)\{.*\}'
        match = re.search(json_pattern, generated_text)
        
        if match:
            json_str = match.group(0)
            
            # Try to parse the JSON
            try:
                data = json.loads(json_str)
                
                # Save the data to a file
                with open('insurance_data.json', 'w') as f:
                    json.dump(data, f, indent=2)
                
                print(f"Successfully generated and saved insurance data to insurance_data.json")
                
                # Save individual tables to CSV
                for table_name in ['policies', 'customers', 'vehicles', 'coverages']:
                    if table_name in data:
                        df = pd.DataFrame(data[table_name])
                        csv_filename = f"{table_name}.csv"
                        df.to_csv(csv_filename, index=False)
                        print(f"Saved {table_name} table to {csv_filename}")
                
                return data
                
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON: {e}")
                print("Attempting to fix the JSON...")
                
                # Try to fix common JSON issues
                try:
                    # Read the raw response
                    with open('raw_response.txt', 'r') as f:
                        text = f.read()
                    
                    # Extract just the JSON part with more sophisticated regex
                    match = re.search(r'({[\s\S]*})', text)
                    if match:
                        json_text = match.group(1)
                        
                        # Try to fix common issues with the JSON
                        # 1. Fix trailing commas in arrays
                        json_text = re.sub(r',(\s*[\]}])', r'\1', json_text)
                        
                        # 2. Add missing commas between array elements
                        json_text = re.sub(r'(true|false|null|"[^"]*"|[0-9]+)\s*\n\s*("|\{|\[)', r'\1,\n\2', json_text)
                        
                        # 3. Fix single quotes used instead of double quotes
                        json_text = re.sub(r"'([^']*)':", r'"\1":', json_text)
                        
                        # Save the fixed JSON
                        with open('fixed_json.json', 'w') as f:
                            f.write(json_text)
                        
                        print("Attempted to fix JSON, saved to fixed_json.json")
                        
                        # Try to parse the fixed JSON
                        try:
                            data = json.loads(json_text)
                            with open('insurance_data.json', 'w') as f:
                                json.dump(data, f, indent=2)
                            print("Successfully fixed and saved the JSON data!")
                            
                            # Save individual tables to CSV
                            for table_name in ['policies', 'customers', 'vehicles', 'coverages']:
                                if table_name in data:
                                    df = pd.DataFrame(data[table_name])
                                    csv_filename = f"{table_name}.csv"
                                    df.to_csv(csv_filename, index=False)
                                    print(f"Saved {table_name} table to {csv_filename}")
                            
                            return data
                        except json.JSONDecodeError as e2:
                            print(f"Still couldn't parse the fixed JSON: {e2}")
                            print("You might need to fix the JSON manually using the fixed_json.json file")
                            return None
                    else:
                        print("Could not extract JSON with regex")
                        return None
                        
                except Exception as e:
                    print(f"Error in the JSON fixing process: {e}")
                    return None
        else:
            print("Could not find JSON content in the response")
            return None
            
    except Exception as e:
        print(f"Error calling Bedrock: {e}")
        return None

if __name__ == "__main__":
    # Generate the data
    data = generate_insurance_data()