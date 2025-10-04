import boto3
import json
from datetime import datetime
import uuid
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

    # Extract all data from parameters
    customer_data = param_dict.get('customer_data', {})
    policy_data = param_dict.get('policy_data', {})
    damage_analysis = param_dict.get('damage_analysis', {})
    document_analysis = param_dict.get('document_analysis', {})

    # Parse JSON strings if needed
    if isinstance(customer_data, str):
        customer_data = json.loads(customer_data)
    if isinstance(policy_data, str):
        policy_data = json.loads(policy_data)
    if isinstance(damage_analysis, str):
        damage_analysis = json.loads(damage_analysis)
    if isinstance(document_analysis, str):
        document_analysis = json.loads(document_analysis)

    print(f"Processing claim for customer: {customer_data.get('customer_id', 'unknown')}")

    # Generate settlement decision
    result_body = generate_settlement_decision(customer_data, policy_data, damage_analysis, document_analysis)

    # New format response
    return {
        'messageVersion': '1.0',
        'response': {
            'actionGroup': action_group,
            'function': function,
            'functionResponse': {
                'responseBody': {
                    'TEXT': {
                        'body': json.dumps(result_body, cls=DecimalEncoder)
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

    # Extract all data from parameters
    customer_data = next((json.loads(p['value']) if isinstance(p['value'], str) else p['value']
                         for p in parameters if p['name'] == 'customer_data'), {})
    policy_data = next((json.loads(p['value']) if isinstance(p['value'], str) else p['value']
                       for p in parameters if p['name'] == 'policy_data'), {})
    damage_analysis = next((json.loads(p['value']) if isinstance(p['value'], str) else p['value']
                           for p in parameters if p['name'] == 'damage_analysis'), {})
    document_analysis = next((json.loads(p['value']) if isinstance(p['value'], str) else p['value']
                             for p in parameters if p['name'] == 'document_analysis'), {})

    print(f"Processing claim for customer: {customer_data.get('customer_id', 'unknown')}")

    # Generate settlement decision
    result = generate_settlement_decision(customer_data, policy_data, damage_analysis, document_analysis)

    # Build response
    bedrock_response = {
        'messageVersion': '1.0',
        'response': {
            'actionGroup': action_group,
            'httpMethod': http_method,
            'httpStatusCode': 200,
            'responseBody': {
                'application/json': {
                    'body': json.dumps(result, cls=DecimalEncoder)
                }
            }
        }
    }

    # Return the same field type that was sent
    if function_name:
        bedrock_response['response']['function'] = function_name
    if api_path:
        bedrock_response['response']['apiPath'] = api_path

    print(f"Response: {json.dumps(bedrock_response, cls=DecimalEncoder)}")
    return bedrock_response

def generate_settlement_decision(customer_data, policy_data, damage_analysis, document_analysis):
    """Core business logic for generating settlement decision"""
    try:
        bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')

        # Enhanced prompt for comprehensive reasoning
        prompt = f"""You are an expert insurance claims adjuster. Analyze this auto insurance claim comprehensively and provide a detailed settlement decision with full reasoning.

CUSTOMER PROFILE:
- Customer ID: {customer_data.get('customer_id', 'N/A')}
- Name: {customer_data.get('first_name', '')} {customer_data.get('last_name', '')}
- Previous Claims: {customer_data.get('previous_claims_count', 0)}
- Driving Experience: {customer_data.get('driving_experience_years', 'N/A')} years

POLICY DETAILS:
- Policy Type: {policy_data.get('policy_type', 'N/A')}
- Coverage Amount: ${policy_data.get('coverage_amount', 0)}
- Deductible: ${policy_data.get('deductible_amount', 0)}
- Policy Status: {policy_data.get('policy_status', 'N/A')}

DAMAGE ANALYSIS FROM IMAGES:
{json.dumps(damage_analysis, indent=2)}

DOCUMENT ANALYSIS (Police Report & Repair Estimate):
{json.dumps(document_analysis, indent=2)}

Provide a comprehensive JSON response with:
{{
    "recommendation": "APPROVE/MANUAL_REVIEW/DENY",
    "approved_amount": numeric value (or 0 if denied),
    "deductible_applies": boolean,
    "customer_pays": numeric value,
    "insurance_pays": numeric value,
    "genuine_factors": ["list of legitimate aspects"],
    "suspicious_factors": ["list of questionable aspects"],
    "risk_assessment": "low/medium/high",
    "detailed_reasoning": "comprehensive explanation of decision",
    "supporting_evidence": ["key points that support the decision"],
    "next_steps": ["what should happen next"]
}}

Be thorough, fair, and provide detailed reasoning for your decision."""

        response = bedrock.invoke_model(
            modelId='anthropic.claude-3-5-sonnet-20241022-v2:0',
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 4000,
                "temperature": 0.3,
                "messages": [{"role": "user", "content": prompt}]
            })
        )

        bedrock_result = json.loads(response['body'].read())
        decision_text = bedrock_result['content'][0]['text']

        # Try to parse as JSON
        try:
            decision_json = json.loads(decision_text)
        except:
            decision_json = {'raw_decision': decision_text}

        claim_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()

        # Save comprehensive record to DynamoDB
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.Table('claims-records')

        # Convert to Decimal for DynamoDB
        def convert_to_decimal(obj):
            if isinstance(obj, dict):
                return {k: convert_to_decimal(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_to_decimal(i) for i in obj]
            elif isinstance(obj, float):
                return Decimal(str(obj))
            return obj

        table.put_item(Item={
            'claim_id': claim_id,
            'customer_id': customer_data.get('customer_id', 'unknown'),
            'policy_id': policy_data.get('policy_id', 'unknown'),
            'timestamp': timestamp,
            'recommendation': decision_json.get('recommendation', 'MANUAL_REVIEW') if isinstance(decision_json, dict) else 'MANUAL_REVIEW',
            'approved_amount': convert_to_decimal(decision_json.get('approved_amount', 0)) if isinstance(decision_json, dict) else Decimal('0'),
            'decision_summary': decision_text[:500],
            'status': 'processed'
        })

        return {
            'claim_id': claim_id,
            'timestamp': timestamp,
            'decision': decision_json,
            'message': f'Claim {claim_id} processed successfully',
            'status': 'Settlement decision generated'
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'error': str(e),
            'message': 'Error generating settlement decision'
        }