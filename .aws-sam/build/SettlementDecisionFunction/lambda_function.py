import boto3
import json
from datetime import datetime
import uuid
from decimal import Decimal
import io
import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER, TA_LEFT

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

def generate_settlement_pdf(claim_id, customer_data, policy_data, damage_analysis, document_analysis, decision_json, timestamp):
    """Generate a professional PDF settlement report"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)

    elements = []
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a365d'),
        spaceAfter=30,
        alignment=TA_CENTER
    )

    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#2d3748'),
        spaceAfter=12,
        spaceBefore=12
    )

    # Header
    elements.append(Paragraph("AutoSettled Insurance", title_style))
    elements.append(Paragraph("CLAIM SETTLEMENT DECISION", styles['Heading2']))
    elements.append(Spacer(1, 12))

    # Claim Info Table
    claim_data = [
        ['Claim ID:', claim_id],
        ['Date:', datetime.fromisoformat(timestamp).strftime('%B %d, %Y at %I:%M %p')],
        ['Status:', decision_json.get('recommendation', 'PENDING')]
    ]

    claim_table = Table(claim_data, colWidths=[2*inch, 4*inch])
    claim_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(claim_table)
    elements.append(Spacer(1, 20))

    # Customer Information
    elements.append(Paragraph("Customer Information", heading_style))
    customer_info = [
        ['Name:', f"{customer_data.get('first_name', '')} {customer_data.get('last_name', '')}"],
        ['Email:', customer_data.get('email', 'N/A')],
        ['Phone:', customer_data.get('phone_number', 'N/A')],
    ]
    customer_table = Table(customer_info, colWidths=[2*inch, 4*inch])
    customer_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(customer_table)
    elements.append(Spacer(1, 20))

    # Policy Information
    elements.append(Paragraph("Policy Information", heading_style))
    policy_info = [
        ['Policy Number:', policy_data.get('policy_number', 'N/A')],
        ['Policy Type:', policy_data.get('policy_type', 'N/A')],
        ['Coverage Amount:', f"${policy_data.get('coverage_amount', 0):,.2f}"],
        ['Deductible:', f"${policy_data.get('deductible_amount', 0):,.2f}"],
    ]
    policy_table = Table(policy_info, colWidths=[2*inch, 4*inch])
    policy_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(policy_table)
    elements.append(Spacer(1, 20))

    # Decision Summary - Highlighted Box
    recommendation = decision_json.get('recommendation', 'PENDING')
    if recommendation == 'APPROVE':
        decision_color = colors.HexColor('#48bb78')
    elif recommendation == 'DENY':
        decision_color = colors.HexColor('#f56565')
    else:
        decision_color = colors.HexColor('#ed8936')

    elements.append(Paragraph("Settlement Decision", heading_style))
    decision_data = [
        ['Decision:', recommendation],
        ['Approved Amount:', f"${decision_json.get('approved_amount', 0):,.2f}"],
        ['Deductible Applies:', 'Yes' if decision_json.get('deductible_applies', False) else 'No'],
        ['Customer Pays:', f"${decision_json.get('customer_pays', 0):,.2f}"],
        ['Insurance Pays:', f"${decision_json.get('insurance_pays', 0):,.2f}"],
    ]
    decision_table = Table(decision_data, colWidths=[2*inch, 4*inch])
    decision_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (1, 0), (1, 0), decision_color),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f7fafc')),
    ]))
    elements.append(decision_table)
    elements.append(Spacer(1, 20))

    # Vehicle & Damage Info (if available)
    if damage_analysis and isinstance(damage_analysis, dict):
        vehicle_data = damage_analysis.get('vehicle_data', {})
        if vehicle_data:
            elements.append(Paragraph("Vehicle Information", heading_style))
            vehicle_info = [
                ['VIN:', damage_analysis.get('vehicle_vin', 'N/A')],
                ['Make/Model:', f"{vehicle_data.get('make', '')} {vehicle_data.get('model', '')}"],
                ['Year:', str(vehicle_data.get('year_of_manufacture', 'N/A'))],
            ]
            vehicle_table = Table(vehicle_info, colWidths=[2*inch, 4*inch])
            vehicle_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            elements.append(vehicle_table)
            elements.append(Spacer(1, 20))

    # Incident Information (if available)
    if document_analysis and isinstance(document_analysis, dict):
        elements.append(Paragraph("Incident Information", heading_style))
        incident_info = [
            ['Date:', document_analysis.get('incident_date', 'N/A')],
            ['Location:', document_analysis.get('incident_location', 'N/A')],
            ['Police Case:', document_analysis.get('police_case_number', 'N/A')],
        ]
        incident_table = Table(incident_info, colWidths=[2*inch, 4*inch])
        incident_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(incident_table)
        elements.append(Spacer(1, 20))

    # Detailed Reasoning
    elements.append(Paragraph("Detailed Reasoning", heading_style))
    reasoning_text = decision_json.get('detailed_reasoning', 'No detailed reasoning provided.')
    elements.append(Paragraph(reasoning_text, styles['BodyText']))
    elements.append(Spacer(1, 12))

    # Risk Assessment
    if decision_json.get('risk_assessment'):
        elements.append(Paragraph(f"<b>Risk Assessment:</b> {decision_json.get('risk_assessment', 'N/A').upper()}", styles['BodyText']))
        elements.append(Spacer(1, 12))

    # Next Steps
    if decision_json.get('next_steps'):
        elements.append(Paragraph("Next Steps", heading_style))
        for step in decision_json.get('next_steps', []):
            elements.append(Paragraph(f"• {step}", styles['BodyText']))
        elements.append(Spacer(1, 20))

    # Footer
    elements.append(Spacer(1, 30))
    elements.append(Paragraph("___________________________________________", styles['Normal']))
    elements.append(Paragraph("This is an automated settlement decision generated by AutoSettled AI Claims Processing System.",
                             ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.grey, alignment=TA_CENTER)))
    elements.append(Paragraph(f"Document ID: {claim_id} | Generated on {datetime.now().strftime('%B %d, %Y')}",
                             ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.grey, alignment=TA_CENTER)))

    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer

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
    from datetime import datetime

    try:
        bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')

        # Get current date
        current_date = datetime.now().strftime('%B %d, %Y')

        # Enhanced prompt for comprehensive reasoning
        prompt = f"""Today's date is {current_date}.

You are an expert insurance claims adjuster. Analyze this auto insurance claim comprehensively and provide a detailed settlement decision with full reasoning.

IMPORTANT: Use today's date ({current_date}) for all date comparisons. Do not use your training knowledge cutoff.

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
            modelId='us.anthropic.claude-3-7-sonnet-20250219-v1:0',
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 2000,
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

        # Generate PDF
        pdf_buffer = generate_settlement_pdf(claim_id, customer_data, policy_data, damage_analysis, document_analysis, decision_json, timestamp)

        # Upload PDF to S3
        s3 = boto3.client('s3', region_name='us-east-1')
        bucket_name = os.environ.get('S3_BUCKET_NAME', 'autosettled-documents-986341371998')
        pdf_key = f"settlements/{claim_id}_settlement_decision.pdf"

        s3.put_object(
            Bucket=bucket_name,
            Key=pdf_key,
            Body=pdf_buffer.getvalue(),
            ContentType='application/pdf'
        )

        # Generate signed URL for download (valid for 7 days)
        pdf_url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': pdf_key},
            ExpiresIn=604800  # 7 days
        )

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
            'status': 'processed',
            'pdf_url': pdf_url,
            'pdf_s3_key': pdf_key,
            'customer_data': convert_to_decimal(customer_data),
            'policy_data': convert_to_decimal(policy_data),
            'damage_analysis': convert_to_decimal(damage_analysis),
            'document_analysis': convert_to_decimal(document_analysis),
            'decision': convert_to_decimal(decision_json)
        })

        # Add pdf_url to decision for frontend
        decision_json['pdf_url'] = pdf_url
        decision_json['claim_id'] = claim_id

        return {
            'claim_id': claim_id,
            'timestamp': timestamp,
            'decision': decision_json,
            'pdf_url': pdf_url,
            'pdf_s3_key': pdf_key,
            'message': f'Claim {claim_id} processed successfully',
            'status': 'Settlement decision generated'
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'error': str(e),
            'message': 'Error generating settlement decision'
        }