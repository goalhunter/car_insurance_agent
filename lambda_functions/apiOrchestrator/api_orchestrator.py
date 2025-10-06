import json
import boto3
from botocore.config import Config
import os
import uuid
from datetime import datetime

# Configure boto3 with extended timeouts for long-running agent calls
bedrock_config = Config(
    read_timeout=600,  # 10 minutes
    connect_timeout=60,
    retries={'max_attempts': 3, 'mode': 'adaptive'}
)

bedrock_agent_runtime = boto3.client('bedrock-agent-runtime', config=bedrock_config)
dynamodb = boto3.resource('dynamodb')

BEDROCK_AGENT_ID = os.environ['BEDROCK_AGENT_ID']
BEDROCK_AGENT_ALIAS_ID = os.environ['BEDROCK_AGENT_ALIAS_ID']
CLAIMS_TABLE = os.environ.get('CLAIMS_TABLE', 'autosettled-claims')

def lambda_handler(event, context):
    """
    API Gateway Orchestrator for AutoSettled
    Handles all API routes and invokes Bedrock Agent
    """

    # Headers (CORS handled by Function URL)
    headers = {
        'Content-Type': 'application/json'
    }

    # Normalize event format (support both API Gateway and Function URL)
    request_context = event.get('requestContext', {})

    # Lambda Function URL format
    if 'http' in request_context:
        method = request_context['http']['method']
        path = request_context['http']['path']
    # API Gateway format
    else:
        method = event.get('httpMethod', '')
        path = event.get('path', '')

    # Handle OPTIONS request for CORS
    if method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({'message': 'OK'})
        }

    try:
        body = json.loads(event.get('body', '{}')) if event.get('body') else {}

        # Route: POST /agent/invoke - Invoke Bedrock Agent
        if path == '/agent/invoke' and method == 'POST':
            return invoke_bedrock_agent(body, headers)

        # Route: POST /claim/start - Start new claim session
        elif path == '/claim/start' and method == 'POST':
            return start_claim_session(headers)

        # Route: GET /claim/{claimId} - Get claim status
        elif path.startswith('/claim/') and method == 'GET':
            # Extract claim_id from path
            path_params = event.get('pathParameters', {})
            if path_params:
                claim_id = path_params.get('claimId')
            else:
                # Function URL format - extract from path
                claim_id = path.split('/')[-1]
            return get_claim_status(claim_id, headers)

        # Route: GET /claims - List all claims
        elif path == '/claims' and method == 'GET':
            limit = int(event.get('queryStringParameters', {}).get('limit', 50))
            return list_claims(limit, headers)

        else:
            return {
                'statusCode': 404,
                'headers': headers,
                'body': json.dumps({'error': 'Not Found'})
            }

    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }


def invoke_bedrock_agent(body, headers):
    """Invoke Bedrock Agent with user input"""

    input_text = body.get('inputText', '')
    session_id = body.get('sessionId', str(uuid.uuid4()))
    enable_trace = body.get('enableTrace', False)

    if not input_text:
        return {
            'statusCode': 400,
            'headers': headers,
            'body': json.dumps({'error': 'inputText is required'})
        }

    try:
        print(f"Invoking Bedrock Agent - Session: {session_id}, Input: {input_text[:100]}...")

        # Invoke Bedrock Agent
        response = bedrock_agent_runtime.invoke_agent(
            agentId=BEDROCK_AGENT_ID,
            agentAliasId=BEDROCK_AGENT_ALIAS_ID,
            sessionId=session_id,
            inputText=input_text,
            enableTrace=enable_trace
        )

        print("Agent invoked, processing stream...")

        # Process streaming response
        output_text = ""
        trace_data = []
        chunk_count = 0

        event_stream = response['completion']
        for event in event_stream:
            if 'chunk' in event:
                chunk = event['chunk']
                if 'bytes' in chunk:
                    output_text += chunk['bytes'].decode('utf-8')
                    chunk_count += 1
                    if chunk_count % 10 == 0:
                        print(f"Processed {chunk_count} chunks, output length: {len(output_text)}")

            if enable_trace and 'trace' in event:
                trace_data.append(event['trace'])

        print(f"Stream complete. Total chunks: {chunk_count}, Total output: {len(output_text)} chars")

        result = {
            'sessionId': session_id,
            'output': output_text,
            'completion': 'COMPLETE'
        }

        if enable_trace:
            result['trace'] = trace_data

        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps(result)
        }

    except Exception as e:
        print(f"Error invoking Bedrock Agent: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': f'Failed to invoke agent: {str(e)}'})
        }


def start_claim_session(headers):
    """Start a new claim session"""

    session_id = str(uuid.uuid4())

    # Create claim record in DynamoDB
    try:
        table = dynamodb.Table(CLAIMS_TABLE)
        table.put_item(
            Item={
                'claim_id': session_id,
                'status': 'IN_PROGRESS',
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
        )
    except Exception as e:
        print(f"Error creating claim record: {str(e)}")
        # Continue even if DynamoDB fails

    return {
        'statusCode': 200,
        'headers': headers,
        'body': json.dumps({'sessionId': session_id})
    }


def get_claim_status(claim_id, headers):
    """Get claim status and details"""

    try:
        table = dynamodb.Table(CLAIMS_TABLE)
        response = table.get_item(Key={'claim_id': claim_id})

        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': headers,
                'body': json.dumps({'error': 'Claim not found'})
            }

        claim_data = response['Item']

        # Map DynamoDB field names to frontend expected format
        formatted_data = {
            'customer': claim_data.get('customer_data'),
            'policy': claim_data.get('policy_data'),
            'damageAnalysis': claim_data.get('damage_analysis'),
            'documentAnalysis': claim_data.get('document_analysis'),
            'settlement': claim_data.get('decision', {})
        }

        # Add pdf_url to settlement if it exists
        if claim_data.get('pdf_url'):
            if formatted_data['settlement']:
                formatted_data['settlement']['pdf_url'] = claim_data.get('pdf_url')
            else:
                formatted_data['settlement'] = {'pdf_url': claim_data.get('pdf_url')}

        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps(formatted_data, default=str)
        }

    except Exception as e:
        print(f"Error getting claim: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }


def list_claims(limit, headers):
    """List all claims"""

    try:
        table = dynamodb.Table(CLAIMS_TABLE)
        response = table.scan(Limit=limit)

        claims = response.get('Items', [])

        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps(claims, default=str)
        }

    except Exception as e:
        print(f"Error listing claims: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }
