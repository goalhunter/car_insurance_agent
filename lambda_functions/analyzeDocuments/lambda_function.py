import boto3
import json

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

    police_report_uri = param_dict.get('police_report_uri')
    repair_estimate_uri = param_dict.get('repair_estimate_uri')
    damage_analysis = param_dict.get('damage_analysis')

    print(f"Parameters - police_report: {police_report_uri}, repair_estimate: {repair_estimate_uri}")

    # Perform document analysis
    result_body = perform_document_analysis(police_report_uri, repair_estimate_uri, damage_analysis)

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

    police_report_uri = next((p['value'] for p in parameters if p['name'] == 'police_report_uri'), None)
    repair_estimate_uri = next((p['value'] for p in parameters if p['name'] == 'repair_estimate_uri'), None)
    damage_analysis = next((p['value'] for p in parameters if p['name'] == 'damage_analysis'), None)

    print(f"Parameters - police_report: {police_report_uri}, repair_estimate: {repair_estimate_uri}")

    # Perform document analysis
    result = perform_document_analysis(police_report_uri, repair_estimate_uri, damage_analysis)

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

def perform_document_analysis(police_report_uri, repair_estimate_uri, damage_analysis):
    """Core business logic for document analysis"""
    textract = boto3.client('textract', region_name='us-east-1')
    bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')

    try:
        # Extract text from police report
        police_bucket, police_key = parse_s3_uri(police_report_uri)
        police_response = textract.detect_document_text(
            Document={'S3Object': {'Bucket': police_bucket, 'Name': police_key}}
        )
        police_text = extract_text(police_response)

        # Extract text from repair estimate
        estimate_bucket, estimate_key = parse_s3_uri(repair_estimate_uri)
        estimate_response = textract.detect_document_text(
            Document={'S3Object': {'Bucket': estimate_bucket, 'Name': estimate_key}}
        )
        estimate_text = extract_text(estimate_response)

        # Include damage analysis for cross-verification if provided
        damage_context = ""
        if damage_analysis:
            damage_context = f"\n\nPREVIOUS DAMAGE ANALYSIS FROM IMAGES:\n{damage_analysis}\n\nIMPORTANT: Cross-verify the repair estimate against the damage seen in images."

        prompt = f"""Extract and analyze key information from these claim documents:

POLICE REPORT:
{police_text}

REPAIR ESTIMATE:
{estimate_text}{damage_context}

Return a JSON object with:
{{
    "incident_date": "date from report",
    "incident_location": "location",
    "police_case_number": "case number",
    "fault_determination": "who was at fault",
    "estimated_repair_cost": numeric value from estimate,
    "repair_items": ["list of items to be repaired"],
    "inconsistencies": ["any discrepancies between documents or with image analysis"],
    "red_flags": ["any suspicious elements"],
    "document_authenticity_assessment": "your assessment"
}}"""

        response = bedrock.invoke_model(
            modelId='anthropic.claude-3-5-sonnet-20241022-v2:0',
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 2000,
                "messages": [{"role": "user", "content": prompt}]
            })
        )

        bedrock_result = json.loads(response['body'].read())
        analysis_text = bedrock_result['content'][0]['text']

        # Try to parse as JSON
        try:
            return json.loads(analysis_text)
        except:
            return {'raw_analysis': analysis_text}

    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'error': str(e),
            'message': 'Error analyzing documents'
        }

def extract_text(textract_response):
    text = ""
    for block in textract_response['Blocks']:
        if block['BlockType'] == 'LINE':
            text += block['Text'] + "\n"
    return text

def parse_s3_uri(uri):
    parts = uri.replace("s3://", "").split("/", 1)
    return parts[0], parts[1]