import boto3
import json
import base64
from decimal import Decimal

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

def lambda_handler(event, context):
    print("Received event:", json.dumps(event))

    # Bedrock Agents for Amazon Bedrock has TWO formats:
    # 1. Old format: actionGroup, apiPath, parameters
    # 2. New format: agent, actionGroup, function, parameters (tool use)

    # Check which format we received
    if 'agent' in event:
        # New agent format with tool use
        return handle_new_format(event, context)
    else:
        # Old action group format
        return handle_old_format(event, context)

def handle_new_format(event, context):
    """Handle new Bedrock Agent format with function/tool use"""
    print("Using NEW agent format")

    # Extract function name and parameters
    action_group = event.get('actionGroup', '')
    function = event.get('function', '')
    parameters = event.get('parameters', [])

    # Extract parameter values
    param_dict = {}
    for param in parameters:
        param_dict[param['name']] = param['value']

    image_uris = param_dict.get('image_uris')
    policy_id = param_dict.get('policy_id')

    print(f"Parameters - image_uris: {image_uris}, policy_id: {policy_id}")

    # Convert to list if string (handle both "[uri1, uri2]" and "uri1")
    if isinstance(image_uris, str):
        # Remove brackets and parse as list
        image_uris = image_uris.strip('[]').split(', ')
        image_uris = [uri.strip() for uri in image_uris]

    # Perform damage analysis (VIN will be fetched from policy)
    result_body = perform_damage_analysis(image_uris, policy_id)

    # New format response
    return {
        'messageVersion': '1.0',
        'response': {
            'actionGroup': action_group,
            'function': function,
            'functionResponse': {
                'responseBody': {
                    'TEXT': {
                        'body': json.dumps(result_body)
                    }
                }
            }
        }
    }

def handle_old_format(event, context):
    """Handle old action group format"""
    print("Using OLD action group format")

    action_group = event.get('actionGroup', '')
    function_name = event.get('function', '')
    api_path = event.get('apiPath', '')
    http_method = event.get('httpMethod', 'POST')
    parameters = event.get('parameters', [])

    image_uris = next((p['value'] for p in parameters if p['name'] == 'image_uris'), None)
    policy_id = next((p['value'] for p in parameters if p['name'] == 'policy_id'), None)

    print(f"Parameters - image_uris: {image_uris}, policy_id: {policy_id}")

    # Convert to list if string (handle both "[uri1, uri2]" and "uri1")
    if isinstance(image_uris, str):
        # Remove brackets and parse as list
        image_uris = image_uris.strip('[]').split(', ')
        image_uris = [uri.strip() for uri in image_uris]

    # Perform damage analysis (VIN will be fetched from policy)
    result = perform_damage_analysis(image_uris, policy_id)

    # Build response
    bedrock_response = {
        'messageVersion': '1.0',
        'response': {
            'actionGroup': action_group,
            'httpMethod': http_method,
            'httpStatusCode': 200,
            'responseBody': {
                'application/json': {
                    'body': json.dumps(result)
                }
            }
        }
    }

    # Return the same field type that was sent
    if function_name:
        bedrock_response['response']['function'] = function_name
    if api_path:
        bedrock_response['response']['apiPath'] = api_path

    print(f"Response: {json.dumps(bedrock_response)}")
    return bedrock_response

def perform_damage_analysis(image_uris, policy_id):
    """Core business logic for damage analysis"""
    from datetime import datetime

    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    vehicles_table = dynamodb.Table('autosettled-vehicles')

    try:
        # Fetch vehicle using policy_id
        vehicle_response = vehicles_table.scan(
            FilterExpression='policy_id = :pid',
            ExpressionAttributeValues={':pid': policy_id}
        )

        if not vehicle_response.get('Items'):
            return {
                'success': False,
                'message': 'No vehicle found for this policy.'
            }

        vehicle = vehicle_response['Items'][0]
        vehicle_vin = vehicle.get('vin')

        # Get current date
        current_date = datetime.now().strftime('%B %d, %Y')

        # VIN is valid, proceed with damage analysis
        s3 = boto3.client('s3', region_name='us-east-1')
        images_base64 = []

        for uri in image_uris:
            bucket, key = parse_s3_uri(uri)
            img_obj = s3.get_object(Bucket=bucket, Key=key)
            images_base64.append(base64.b64encode(img_obj['Body'].read()).decode())

        bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')

        prompt = f"""Today's date is {current_date}.

Analyze these car damage images. The vehicle registered in our database is:
Make: {vehicle['make']}, Model: {vehicle['model']}, Year: {vehicle['year_of_manufacture']}, Color: {vehicle.get('color', 'Unknown')}

IMPORTANT: Compare the car in the images with the database vehicle details above. Only flag if there's an obvious mismatch (different color, completely different vehicle type).

Then provide a detailed analysis in JSON format:
{{
    "vehicle_matches_policy": true/false,
    "vehicle_match_notes": "explanation of match/mismatch",
    "damaged_parts": ["list of damaged parts"],
    "damage_summary": "detailed description",
    "estimated_repair_cost_usd": numeric value,
    "likely_crash_reason": "analysis of how this happened",
    "severity": "minor/moderate/severe",
    "suspicious_indicators": ["any red flags or concerns"]
}}"""

        response = bedrock.invoke_model(
            modelId='us.anthropic.claude-3-7-sonnet-20250219-v1:0',
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "messages": [{
                    "role": "user",
                    "content": [
                        {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": img}}
                        for img in images_base64
                    ] + [{"type": "text", "text": prompt}]
                }]
            })
        )

        bedrock_result = json.loads(response['body'].read())
        analysis_text = bedrock_result['content'][0]['text']

        # Try to parse as JSON, fallback to text
        try:
            analysis_json = json.loads(analysis_text)
            return {
                'success': True,
                'vehicle_vin': vehicle_vin,
                'analysis': analysis_json,
                'vehicle_data': json.loads(json.dumps(vehicle, cls=DecimalEncoder))
            }
        except:
            return {
                'success': True,
                'vehicle_vin': vehicle_vin,
                'analysis': analysis_text,
                'vehicle_data': json.loads(json.dumps(vehicle, cls=DecimalEncoder))
            }

    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

def parse_s3_uri(uri):
    parts = uri.replace("s3://", "").split("/", 1)
    return parts[0], parts[1]