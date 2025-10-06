import json
import boto3
import os
import uuid
import base64
from datetime import datetime

s3 = boto3.client('s3')

BUCKET_NAME = os.environ['S3_BUCKET_NAME']

def lambda_handler(event, context):
    """
    Handle file uploads to S3
    Supports multipart form data and base64 encoded files
    """

    # Headers (CORS needed for API Gateway)
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
        'Access-Control-Allow-Methods': 'POST,OPTIONS'
    }

    # Normalize event format (support both API Gateway and Function URL)
    request_context = event.get('requestContext', {})

    # Lambda Function URL format
    if 'http' in request_context:
        method = request_context['http']['method']
    # API Gateway format
    else:
        method = event.get('httpMethod', '')

    # Handle OPTIONS request for CORS
    if method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({'message': 'OK'})
        }

    try:
        # Parse request body
        if event.get('isBase64Encoded'):
            body = base64.b64decode(event['body'])
        else:
            body = event.get('body', '')

        # For simplicity, expecting JSON with file data and metadata
        # In production, use multipart/form-data parser
        data = json.loads(body) if isinstance(body, str) else json.loads(body.decode('utf-8'))

        file_content = data.get('fileContent')  # Base64 encoded file content
        file_name = data.get('fileName', f'file_{uuid.uuid4()}')
        folder = data.get('folder', 'uploads')
        content_type = data.get('contentType', 'application/octet-stream')

        if not file_content:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'fileContent is required'})
            }

        # Decode base64 file content
        file_bytes = base64.b64decode(file_content)

        # Generate S3 key
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        s3_key = f"{folder}/{timestamp}_{file_name}"

        # Upload to S3
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=s3_key,
            Body=file_bytes,
            ContentType=content_type
        )

        # Generate S3 URI
        s3_uri = f"s3://{BUCKET_NAME}/{s3_key}"

        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'uri': s3_uri,
                'bucket': BUCKET_NAME,
                'key': s3_key,
                'message': 'File uploaded successfully'
            })
        }

    except Exception as e:
        print(f"Error uploading file: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }
