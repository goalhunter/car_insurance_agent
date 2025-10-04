"""
Bedrock Agent Setup Script
Creates Bedrock Agent with action groups
"""

import boto3
import sys
import os
import json
import time
from botocore.exceptions import ClientError

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import BEDROCK_AGENT, ACTION_GROUPS, AWS_REGION, IAM_ROLES


def create_agent_role(iam_client):
    """Create IAM role for Bedrock Agent"""
    role_name = IAM_ROLES['agent_role_name']

    print(f"\n[IAM] Checking Bedrock Agent role: {role_name}")

    try:
        role = iam_client.get_role(RoleName=role_name)
        print(f"  [EXISTS] Role already exists")
        return role['Role']['Arn']
    except ClientError as e:
        if e.response['Error']['Code'] != 'NoSuchEntity':
            raise

    # Create role
    print(f"  [CREATE] Creating role...")
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "bedrock.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }]
    }

    role = iam_client.create_role(
        RoleName=role_name,
        AssumeRolePolicyDocument=json.dumps(trust_policy),
        Description='Execution role for Claims Processing Bedrock Agent'
    )

    role_arn = role['Role']['Arn']
    print(f"  [CREATED] Role ARN: {role_arn}")

    # Attach Bedrock policy
    bedrock_policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Action": ["bedrock:InvokeModel"],
            "Resource": "*"
        }]
    }

    iam_client.put_role_policy(
        RoleName=role_name,
        PolicyName='BedrockInvokePolicy',
        PolicyDocument=json.dumps(bedrock_policy)
    )
    print(f"  [ATTACHED] BedrockInvokePolicy")

    # Wait for role to propagate
    print(f"  [WAITING] Waiting for role to propagate...")
    time.sleep(10)

    return role_arn


def create_bedrock_agent(bedrock_agent_client, role_arn):
    """Create or update Bedrock Agent"""
    print("\n" + "=" * 60)
    print("CREATING BEDROCK AGENT")
    print("=" * 60)

    agent_name = BEDROCK_AGENT['agent_name']

    # Check if agent exists
    try:
        agents = bedrock_agent_client.list_agents()
        existing_agent = next(
            (a for a in agents.get('agentSummaries', []) if a['agentName'] == agent_name),
            None
        )

        if existing_agent:
            print(f"\n[EXISTS] Agent '{agent_name}' already exists")
            print(f"  Agent ID: {existing_agent['agentId']}")
            return existing_agent['agentId']

    except Exception as e:
        print(f"[ERROR] Error checking existing agents: {e}")

    # Create agent
    print(f"\n[CREATE] Creating agent '{agent_name}'...")

    try:
        response = bedrock_agent_client.create_agent(
            agentName=agent_name,
            description=BEDROCK_AGENT['description'],
            foundationModel=BEDROCK_AGENT['foundation_model'],
            instruction=BEDROCK_AGENT['instruction'],
            agentResourceRoleArn=role_arn,
            idleSessionTTLInSeconds=600
        )

        agent_id = response['agent']['agentId']
        print(f"  [CREATED] Agent ID: {agent_id}")
        return agent_id

    except Exception as e:
        print(f"  [ERROR] Failed to create agent: {e}")
        return None


def create_action_groups(bedrock_agent_client, agent_id):
    """Create action groups for the agent"""
    print("\n" + "=" * 60)
    print("CREATING ACTION GROUPS")
    print("=" * 60)

    lambda_client = boto3.client('lambda', region_name=AWS_REGION)
    created = []
    failed = []

    for action_key, action_config in ACTION_GROUPS.items():
        action_group_name = action_config['action_group_name']
        lambda_function_name = action_config['lambda_function']

        print(f"\nProcessing: {action_group_name}")

        try:
            # Get Lambda ARN
            lambda_info = lambda_client.get_function(FunctionName=lambda_function_name)
            lambda_arn = lambda_info['Configuration']['FunctionArn']

            # Grant Bedrock permission to invoke Lambda
            try:
                lambda_client.add_permission(
                    FunctionName=lambda_function_name,
                    StatementId=f'AllowBedrockAgent-{agent_id}',
                    Action='lambda:InvokeFunction',
                    Principal='bedrock.amazonaws.com',
                    SourceArn=f'arn:aws:bedrock:{AWS_REGION}:*:agent/*'
                )
                print(f"  [PERMISSION] Added Bedrock invoke permission")
            except ClientError as e:
                if e.response['Error']['Code'] != 'ResourceConflictException':
                    raise
                print(f"  [PERMISSION] Permission already exists")

            # Create function schema
            function_schema = {
                'functions': [{
                    'name': action_config['function_schema']['name'],
                    'description': action_config['function_schema']['description'],
                    'parameters': {}
                }]
            }

            # Add parameters
            for param_name, param_config in action_config['function_schema']['parameters'].items():
                function_schema['functions'][0]['parameters'][param_name] = {
                    'description': param_config['description'],
                    'type': param_config['type'],
                    'required': param_config.get('required', False)
                }

            # Create action group
            bedrock_agent_client.create_agent_action_group(
                agentId=agent_id,
                agentVersion='DRAFT',
                actionGroupName=action_group_name,
                description=action_config['description'],
                actionGroupExecutor={
                    'lambda': lambda_arn
                },
                functionSchema={
                    'functions': function_schema['functions']
                },
                actionGroupState='ENABLED'
            )

            print(f"  [CREATED] Action group created")
            created.append(action_group_name)

        except Exception as e:
            print(f"  [ERROR] {str(e)}")
            failed.append(action_group_name)

    # Summary
    print("\n" + "=" * 60)
    print("ACTION GROUPS SUMMARY")
    print("=" * 60)
    print(f"Created: {len(created)}/{len(ACTION_GROUPS)}")
    for ag in created:
        print(f"  - {ag}")

    if failed:
        print(f"\nFailed: {len(failed)}")
        for ag in failed:
            print(f"  - {ag}")
        return False

    print("=" * 60)
    return True


def prepare_agent(bedrock_agent_client, agent_id):
    """Prepare the agent for use"""
    print("\n[PREPARE] Preparing agent...")

    try:
        bedrock_agent_client.prepare_agent(agentId=agent_id)
        print("  [SUCCESS] Agent prepared successfully")
        print(f"\nAgent ID: {agent_id}")
        print(f"Test your agent in the AWS Bedrock console!")
        return True
    except Exception as e:
        print(f"  [ERROR] Failed to prepare agent: {e}")
        return False


def main():
    """Main setup function"""
    print("=" * 60)
    print("BEDROCK AGENT SETUP")
    print("=" * 60)

    # Create IAM role for agent
    iam_client = boto3.client('iam', region_name=AWS_REGION)
    role_arn = create_agent_role(iam_client)

    # Create Bedrock Agent
    bedrock_agent_client = boto3.client('bedrock-agent', region_name=AWS_REGION)
    agent_id = create_bedrock_agent(bedrock_agent_client, role_arn)

    if not agent_id:
        print("\n[FAILED] Could not create agent")
        return False

    # Create action groups
    action_groups_success = create_action_groups(bedrock_agent_client, agent_id)

    if not action_groups_success:
        print("\n[WARNING] Some action groups failed to create")

    # Prepare agent
    prepare_success = prepare_agent(bedrock_agent_client, agent_id)

    return prepare_success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
