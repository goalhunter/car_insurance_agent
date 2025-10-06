import boto3
import json
from datetime import datetime
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

    policy_id = param_dict.get('policy_id')
    customer_id = param_dict.get('customer_id')

    print(f"Parameters - policy_id: {policy_id}, customer_id: {customer_id}")

    # Query DynamoDB
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('policies')

    try:
        response = table.get_item(Key={'policy_id': policy_id})

        if 'Item' not in response:
            result_body = {
                'verified': False,
                'message': 'Policy not found'
            }
        elif response['Item']['customer_id'] != customer_id:
            result_body = {
                'verified': False,
                'message': 'Policy does not belong to this customer'
            }
        elif response['Item']['policy_status'] != 'Active':
            result_body = {
                'verified': False,
                'message': f"Policy is {response['Item']['policy_status']}, not Active"
            }
        else:
            policy = response['Item']
            end_date = datetime.strptime(policy['policy_end_date'], '%Y-%m-%d')
            if end_date < datetime.now():
                result_body = {
                    'verified': False,
                    'message': 'Policy expired'
                }
            else:
                # Fetch vehicle data to get VIN
                vehicle_vin = None
                try:
                    vehicle_table = dynamodb.Table('vehicles')
                    vehicle_response = vehicle_table.scan(
                        FilterExpression='policy_id = :pid',
                        ExpressionAttributeValues={':pid': policy_id}
                    )
                    if vehicle_response.get('Items'):
                        vehicle_vin = vehicle_response['Items'][0].get('vin')
                except Exception as ve:
                    print(f"Error fetching vehicle: {str(ve)}")

                result_body = {
                    'verified': True,
                    'policy_data': json.loads(json.dumps(policy, cls=DecimalEncoder)),
                    'vehicle_vin': vehicle_vin,
                    'message': f"Policy {policy.get('policy_number', policy_id)} verified successfully" + (f". Vehicle VIN: {vehicle_vin}" if vehicle_vin else "")
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

    policy_id = next((p['value'] for p in parameters if p['name'] == 'policy_id'), None)
    customer_id = next((p['value'] for p in parameters if p['name'] == 'customer_id'), None)

    print(f"Parameters - policy_id: {policy_id}, customer_id: {customer_id}")

    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('policies')

    try:
        response = table.get_item(Key={'policy_id': policy_id})

        if 'Item' not in response:
            result = {
                'verified': False,
                'message': 'Policy not found'
            }
        elif response['Item']['customer_id'] != customer_id:
            result = {
                'verified': False,
                'message': 'Policy does not belong to this customer'
            }
        elif response['Item']['policy_status'] != 'Active':
            result = {
                'verified': False,
                'message': f"Policy is {response['Item']['policy_status']}, not Active"
            }
        else:
            policy = response['Item']
            end_date = datetime.strptime(policy['policy_end_date'], '%Y-%m-%d')
            if end_date < datetime.now():
                result = {
                    'verified': False,
                    'message': 'Policy expired'
                }
            else:
                # Fetch vehicle data to get VIN
                vehicle_vin = None
                try:
                    vehicle_table = dynamodb.Table('vehicles')
                    vehicle_response = vehicle_table.scan(
                        FilterExpression='policy_id = :pid',
                        ExpressionAttributeValues={':pid': policy_id}
                    )
                    if vehicle_response.get('Items'):
                        vehicle_vin = vehicle_response['Items'][0].get('vin')
                except Exception as ve:
                    print(f"Error fetching vehicle: {str(ve)}")

                result = {
                    'verified': True,
                    'policy_data': json.loads(json.dumps(policy, cls=DecimalEncoder)),
                    'vehicle_vin': vehicle_vin,
                    'message': f"Policy {policy.get('policy_number', policy_id)} verified successfully" + (f". Vehicle VIN: {vehicle_vin}" if vehicle_vin else "")
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