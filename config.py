"""
Configuration file for Car Insurance Claims Processing Agent
Customize these settings for your AWS environment
"""

# AWS Configuration
AWS_REGION = 'us-east-1'

# DynamoDB Table Names
DYNAMODB_TABLES = {
    'customers': {
        'table_name': 'customers',
        'partition_key': 'customer_id',
        'billing_mode': 'PAY_PER_REQUEST'  # or 'PROVISIONED'
    },
    'policies': {
        'table_name': 'policies',
        'partition_key': 'policy_id',
        'billing_mode': 'PAY_PER_REQUEST'
    },
    'vehicles': {
        'table_name': 'vehicles',
        'partition_key': 'vehicle_id',
        'billing_mode': 'PAY_PER_REQUEST'
    },
    'claims-records': {
        'table_name': 'claims-records',
        'partition_key': 'claim_id',
        'billing_mode': 'PAY_PER_REQUEST'
    }
}

# Lambda Function Configuration
LAMBDA_FUNCTIONS = {
    'customerVerification': {
        'handler': 'lambda_function.lambda_handler',
        'runtime': 'python3.10',
        'timeout': 30,
        'memory': 256,
        'description': 'Verifies customer identity from DynamoDB'
    },
    'policyVerification': {
        'handler': 'lambda_function.lambda_handler',
        'runtime': 'python3.10',
        'timeout': 30,
        'memory': 256,
        'description': 'Verifies policy status and customer ownership'
    },
    'analyzeDamageImages': {
        'handler': 'lambda_function.lambda_handler',
        'runtime': 'python3.10',
        'timeout': 60,
        'memory': 512,
        'description': 'Analyzes car damage images using Claude vision'
    },
    'analyzeDocuments': {
        'handler': 'lambda_function.lambda_handler',
        'runtime': 'python3.10',
        'timeout': 60,
        'memory': 512,
        'description': 'Analyzes police reports and repair estimates'
    },
    'generateSettlementDecision': {
        'handler': 'lambda_function.lambda_handler',
        'runtime': 'python3.10',
        'timeout': 60,
        'memory': 512,
        'description': 'Generates comprehensive claim settlement decision'
    }
}

# Bedrock Agent Configuration
BEDROCK_AGENT = {
    'agent_name': 'ClaimsProcessingAgent',
    'description': 'Automatic car insurance claim processing agent',
    'foundation_model': 'anthropic.claude-3-7-sonnet-20250219-v1:0',
    'instruction': """You are a car insurance claims processing agent. Guide users through a 5-step claims process:

Step 1: Verify customer identity - Ask for first name, last name, and email. Use verifyCustomer function.

Step 2: Verify policy - Ask for policy ID. Use verifyPolicy function with the customer_id from step 1.

Step 3: Analyze damage - Ask user to provide image S3 URIs and vehicle_id. Use analyzeDamageImages function.

Step 4: Analyze documents - Ask for police report and repair estimate S3 URIs. Use analyzeDocuments function.

Step 5: Generate settlement - Use all collected data to call generateSettlement function. Present the final decision and PDF report link.

Be professional, empathetic, and guide users step-by-step. Don't skip steps."""
}

# Action Groups Configuration
ACTION_GROUPS = {
    'verifyCustomer': {
        'action_group_name': 'verifyCustomer',
        'description': 'Verifies customer identity',
        'lambda_function': 'customerVerification',
        'function_schema': {
            'name': 'claims-customer-verification',
            'description': 'Verify customer using name and email',
            'parameters': {
                'first_name': {
                    'description': 'Customer first name',
                    'type': 'string',
                    'required': True
                },
                'last_name': {
                    'description': 'Customer last name',
                    'type': 'string',
                    'required': True
                },
                'email': {
                    'description': 'Customer email address',
                    'type': 'string',
                    'required': True
                }
            }
        }
    },
    'verifyPolicy': {
        'action_group_name': 'verifyPolicy',
        'description': 'Verifies policy details',
        'lambda_function': 'policyVerification',
        'function_schema': {
            'name': 'claims-policy-verification',
            'description': 'Verify policy and customer ownership',
            'parameters': {
                'policy_id': {
                    'description': 'Policy ID',
                    'type': 'string',
                    'required': True
                },
                'customer_id': {
                    'description': 'Customer ID from verification',
                    'type': 'string',
                    'required': True
                }
            }
        }
    },
    'analyzeDamageImages': {
        'action_group_name': 'analyzeDamageImages',
        'description': 'Analyzes car damage from images',
        'lambda_function': 'analyzeDamageImages',
        'function_schema': {
            'name': 'claims-damage-analysis',
            'description': 'Analyze damage images and verify vehicle',
            'parameters': {
                'image_uris': {
                    'description': 'List of S3 URIs for damage images',
                    'type': 'array',
                    'required': True
                },
                'vehicle_id': {
                    'description': 'Vehicle ID',
                    'type': 'string',
                    'required': True
                }
            }
        }
    },
    'analyzeDocuments': {
        'action_group_name': 'analyzeDocuments',
        'description': 'Analyzes police report and repair estimates',
        'lambda_function': 'analyzeDocuments',
        'function_schema': {
            'name': 'claims-document-analysis',
            'description': 'Analyze police report and repair estimate',
            'parameters': {
                'police_report_uri': {
                    'description': 'S3 URI for police report',
                    'type': 'string',
                    'required': True
                },
                'repair_estimate_uri': {
                    'description': 'S3 URI for repair estimate',
                    'type': 'string',
                    'required': True
                }
            }
        }
    },
    'generateSettlement': {
        'action_group_name': 'generateSettlement',
        'description': 'Generates final settlement decision',
        'lambda_function': 'generateSettlementDecision',
        'function_schema': {
            'name': 'claims-settlement-decision',
            'description': 'Generate comprehensive settlement decision',
            'parameters': {
                'customer_data': {
                    'description': 'Customer data from verification',
                    'type': 'object',
                    'required': True
                },
                'policy_data': {
                    'description': 'Policy data from verification',
                    'type': 'object',
                    'required': True
                },
                'damage_analysis': {
                    'description': 'Damage analysis results',
                    'type': 'object',
                    'required': True
                },
                'document_analysis': {
                    'description': 'Document analysis results',
                    'type': 'object',
                    'required': True
                }
            }
        }
    }
}

# Synthetic Data Configuration
SYNTHETIC_DATA = {
    'num_records': 5,  # Number of records to generate per table
    'bedrock_model': 'us.anthropic.claude-3-7-sonnet-20250219-v1:0'
}

# IAM Role Names (will be created if don't exist)
IAM_ROLES = {
    'lambda_role_name': 'ClaimsProcessingLambdaRole',
    'agent_role_name': 'ClaimsProcessingAgentRole'
}
