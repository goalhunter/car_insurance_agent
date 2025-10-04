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

    first_name = param_dict.get('first_name')
    last_name = param_dict.get('last_name')
    email = param_dict.get('email')

    print(f"Parameters - first_name: {first_name}, last_name: {last_name}, email: {email}")

    # Query DynamoDB
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('customers')

    try:
        response = table.scan(
            FilterExpression='first_name = :fn AND last_name = :ln AND email = :em',
            ExpressionAttributeValues={
                ':fn': first_name,
                ':ln': last_name,
                ':em': email
            }
        )

        if response['Items']:
            customer = response['Items'][0]
            result_body = {
                'verified': True,
                'customer_id': customer.get('customer_id'),
                'customer_data': customer,
                'message': f"Customer {first_name} {last_name} verified successfully"
            }
        else:
            result_body = {
                'verified': False,
                'message': 'Customer not found in our records'
            }
    except Exception as e:
        print(f"Error: {str(e)}")
        result_body = {
            'verified': False,
            'error': str(e)
        }

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

    # Extract values
    first_name = None
    last_name = None
    email = None

    for p in parameters:
        if p.get('name') == 'first_name':
            first_name = p.get('value')
        elif p.get('name') == 'last_name':
            last_name = p.get('value')
        elif p.get('name') == 'email':
            email = p.get('value')

    print(f"Parameters - first_name: {first_name}, last_name: {last_name}, email: {email}")

    # Query DynamoDB
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('customers')

    try:
        response = table.scan(
            FilterExpression='first_name = :fn AND last_name = :ln AND email = :em',
            ExpressionAttributeValues={
                ':fn': first_name,
                ':ln': last_name,
                ':em': email
            }
        )

        if response['Items']:
            result = {
                'verified': True,
                'customer_id': response['Items'][0].get('customer_id'),
                'customer_data': response['Items'][0],
                'message': f"Customer {first_name} {last_name} verified successfully"
            }
        else:
            result = {
                'verified': False,
                'message': 'Customer not found in our records'
            }
    except Exception as e:
        print(f"Error: {str(e)}")
        result = {
            'verified': False,
            'error': str(e)
        }

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
