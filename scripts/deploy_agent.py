import boto3
import json
import time
import sys
from datetime import datetime

# Initialize AWS clients
bedrock_agent = boto3.client('bedrock-agent', region_name='us-east-1')
iam_client = boto3.client('iam', region_name='us-east-1')
sts_client = boto3.client('sts', region_name='us-east-1')

def get_account_id():
    """Get AWS account ID"""
    return sts_client.get_caller_identity()['Account']

def create_agent_role(agent_name, account_id):
    """Create IAM role for the Bedrock Agent"""
    print("\n🔐 Creating IAM role for agent...")
    
    role_name = f"{agent_name.replace(' ', '-')}-BedrockAgentRole"
    
    # Trust policy - allows Bedrock to assume this role
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "bedrock.amazonaws.com"
                },
                "Action": "sts:AssumeRole",
                "Condition": {
                    "StringEquals": {
                        "aws:SourceAccount": account_id
                    },
                    "ArnLike": {
                        "aws:SourceArn": f"arn:aws:bedrock:us-east-1:{account_id}:agent/*"
                    }
                }
            }
        ]
    }
    
    try:
        # Check if role already exists
        role_response = iam_client.get_role(RoleName=role_name)
        role_arn = role_response['Role']['Arn']
        print(f"   ✅ Using existing role: {role_name}")
        return role_arn
    except iam_client.exceptions.NoSuchEntityException:
        pass
    
    # Create new role
    print(f"   📝 Creating new role: {role_name}")
    role_response = iam_client.create_role(
        RoleName=role_name,
        AssumeRolePolicyDocument=json.dumps(trust_policy),
        Description=f"Execution role for {agent_name} Bedrock Agent"
    )
    role_arn = role_response['Role']['Arn']
    
    # Permissions policy - what the agent can do
    permissions_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "BedrockInvokeModelPolicy",
                "Effect": "Allow",
                "Action": [
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream"
                ],
                "Resource": [
                    "arn:aws:bedrock:*::foundation-model/*",
                    f"arn:aws:bedrock:us-east-1:{account_id}:inference-profile/*"
                ]
            },
            {
                "Sid": "BedrockRetrieveKnowledgeBasePolicy",
                "Effect": "Allow",
                "Action": [
                    "bedrock:Retrieve",
                    "bedrock:RetrieveAndGenerate"
                ],
                "Resource": [
                    f"arn:aws:bedrock:us-east-1:{account_id}:knowledge-base/*"
                ]
            }
        ]
    }
    
    # Attach inline policy
    iam_client.put_role_policy(
        RoleName=role_name,
        PolicyName=f"{agent_name.replace(' ', '-')}-BedrockPolicy",
        PolicyDocument=json.dumps(permissions_policy)
    )
    
    print(f"   ✅ Role created: {role_arn}")
    print("   ⏳ Waiting 15 seconds for IAM propagation...")
    time.sleep(15)
    
    return role_arn

def create_agent(config, role_arn):
    """Create the Bedrock Agent"""
    print("\n🤖 Creating Bedrock Agent...")
    
    agent_config = config['agent']
    
    print(f"   Name: {agent_config['agentName']}")
    print(f"   Model: {agent_config['foundationModel']}")
    
    try:
        response = bedrock_agent.create_agent(
            agentName=agent_config['agentName'],
            description=agent_config.get('description', ''),
            instruction=agent_config['instruction'],
            foundationModel=agent_config['foundationModel'],
            agentResourceRoleArn=role_arn,
            idleSessionTTLInSeconds=agent_config.get('idleSessionTTLInSeconds', 600)
        )
        
        agent_id = response['agent']['agentId']
        print(f"   ✅ Agent created with ID: {agent_id}")
        return agent_id
        
    except Exception as e:
        print(f"   ❌ Error creating agent: {e}")
        sys.exit(1)

def add_lambda_permissions(lambda_arn, agent_id, account_id):
    """Add permission for agent to invoke Lambda function"""
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    
    # Extract function name from ARN
    function_name = lambda_arn.split(':')[-1]
    
    try:
        lambda_client.add_permission(
            FunctionName=function_name,
            StatementId=f'bedrock-agent-{agent_id}',
            Action='lambda:InvokeFunction',
            Principal='bedrock.amazonaws.com',
            SourceArn=f'arn:aws:bedrock:us-east-1:{account_id}:agent/{agent_id}'
        )
        print(f"      ✅ Lambda permission added for: {function_name}")
    except lambda_client.exceptions.ResourceConflictException:
        print(f"      ℹ️  Permission already exists for: {function_name}")
    except Exception as e:
        print(f"      ⚠️  Warning: Could not add permission for {function_name}: {e}")

def create_action_groups(agent_id, action_groups, account_id):
    """Create action groups for the agent"""
    print(f"\n📋 Creating {len(action_groups)} action groups...")
    
    created_count = 0
    
    for ag in action_groups:
        # Skip built-in action groups
        if ag.get('parentActionGroupSignature') == 'AMAZON.UserInput':
            continue
        
        action_group_name = ag['actionGroupName']
        print(f"\n   📌 Creating: {action_group_name}")
        
        # Prepare action group parameters
        ag_params = {
            'agentId': agent_id,
            'agentVersion': 'DRAFT',
            'actionGroupName': action_group_name,
            'actionGroupState': 'ENABLED'
        }
        
        # Add description if present
        if 'description' in ag and ag['description']:
            ag_params['description'] = ag['description']
        
        # Add Lambda executor
        if 'actionGroupExecutor' in ag and 'lambda' in ag['actionGroupExecutor']:
            lambda_arn = ag['actionGroupExecutor']['lambda']
            ag_params['actionGroupExecutor'] = {
                'lambda': lambda_arn
            }
            print(f"      Lambda: {lambda_arn}")
            
            # Add Lambda permission
            add_lambda_permissions(lambda_arn, agent_id, account_id)
        
        # Add function schema
        if 'functionSchema' in ag:
            ag_params['functionSchema'] = ag['functionSchema']
            functions = ag['functionSchema'].get('functions', [])
            print(f"      Functions: {len(functions)}")
            for func in functions:
                print(f"        - {func['name']}")
        
        # Add API schema (if present)
        if 'apiSchema' in ag:
            ag_params['apiSchema'] = ag['apiSchema']
        
        try:
            bedrock_agent.create_agent_action_group(**ag_params)
            print(f"      ✅ Created successfully")
            created_count += 1
        except Exception as e:
            print(f"      ❌ Error: {e}")
    
    print(f"\n   ✅ Created {created_count}/{len(action_groups)} action groups")
    return created_count

def prepare_agent(agent_id):
    """Prepare the agent (compile it)"""
    print("\n🔄 Preparing agent...")
    
    try:
        bedrock_agent.prepare_agent(agentId=agent_id)
        print("   ✅ Agent prepared successfully")
        
        # Wait for preparation to complete
        print("   ⏳ Waiting for agent to be ready...")
        time.sleep(5)
        
        return True
    except Exception as e:
        print(f"   ⚠️  Warning: {e}")
        return False

def create_alias(agent_id, alias_name='prod'):
    """Create an alias for the agent"""
    print(f"\n🏷️  Creating alias: {alias_name}")
    
    try:
        response = bedrock_agent.create_agent_alias(
            agentId=agent_id,
            agentAliasName=alias_name,
            description=f'{alias_name.capitalize()} environment alias'
        )
        alias_id = response['agentAlias']['agentAliasId']
        print(f"   ✅ Alias created: {alias_id}")
        return alias_id
    except Exception as e:
        print(f"   ⚠️  Error creating alias: {e}")
        return None

def load_config(filename='../infrastructure/bedrock/agent_config.json'):
    """Load agent configuration from JSON file"""
    print(f"📂 Loading configuration from: {filename}")

    try:
        with open(filename, 'r') as f:
            config = json.load(f)
        print("   ✅ Configuration loaded")
        return config
    except FileNotFoundError:
        print(f"   ❌ Error: {filename} not found!")
        print("\n   Please ensure agent_config.json is in infrastructure/bedrock/ directory.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"   ❌ Error: Invalid JSON in {filename}")
        print(f"   {e}")
        sys.exit(1)

def print_summary(agent_id, alias_id, agent_name):
    """Print deployment summary"""
    print("\n" + "="*60)
    print("✅ DEPLOYMENT COMPLETED SUCCESSFULLY!")
    print("="*60)
    print(f"\n🤖 Agent Details:")
    print(f"   Name: {agent_name}")
    print(f"   Agent ID: {agent_id}")
    if alias_id:
        print(f"   Alias ID: {alias_id}")
    
    print(f"\n🔗 AWS Console Links:")
    print(f"   Agent: https://console.aws.amazon.com/bedrock/home?region=us-east-1#/agents/{agent_id}")
    
    print(f"\n📝 Next Steps:")
    print(f"   1. Test your agent in the AWS Console")
    print(f"   2. Update your application with the new Agent ID:")
    print(f"      BEDROCK_AGENT_ID={agent_id}")
    if alias_id:
        print(f"      BEDROCK_AGENT_ALIAS_ID={alias_id}")
    print(f"\n   3. Invoke the agent using AWS SDK:")
    print(f"""
      import boto3
      
      bedrock_runtime = boto3.client('bedrock-agent-runtime')
      response = bedrock_runtime.invoke_agent(
          agentId='{agent_id}',
          agentAliasId='{alias_id or "TSTALIASID"}',
          sessionId='unique-session-id',
          inputText='Hello!'
      )
    """)

def main():
    print("="*60)
    print("🚀 BEDROCK AGENT DEPLOYMENT SCRIPT")
    print("="*60)
    
    # Get AWS account ID
    try:
        account_id = get_account_id()
        print(f"\n📊 AWS Account ID: {account_id}")
    except Exception as e:
        print(f"\n❌ Error: Could not get AWS credentials")
        print(f"   {e}")
        print("\n   Please run 'aws configure' to set up your credentials")
        sys.exit(1)
    
    # Load configuration
    config = load_config()
    
    # Display configuration summary
    agent_config = config['agent']
    print(f"\n📋 Configuration Summary:")
    print(f"   Agent Name: {agent_config['agentName']}")
    print(f"   Model: {agent_config['foundationModel']}")
    print(f"   Action Groups: {len(config['action_groups'])}")
    print(f"   Knowledge Bases: {len(config.get('knowledge_bases', []))}")
    
    # Confirm deployment
    print("\n" + "-"*60)
    confirm = input("📢 Proceed with deployment? (yes/no): ").strip().lower()
    if confirm not in ['yes', 'y']:
        print("❌ Deployment cancelled")
        sys.exit(0)
    
    # Step 1: Create IAM role
    role_arn = create_agent_role(agent_config['agentName'], account_id)
    
    # Step 2: Create agent
    agent_id = create_agent(config, role_arn)
    
    # Step 3: Create action groups
    create_action_groups(agent_id, config['action_groups'], account_id)
    
    # Step 4: Prepare agent
    prepare_agent(agent_id)
    
    # Step 5: Create alias
    create_alias_prompt = input("\n📢 Create production alias? (yes/no): ").strip().lower()
    alias_id = None
    if create_alias_prompt in ['yes', 'y']:
        alias_name = input("   Enter alias name (default: prod): ").strip() or 'prod'
        alias_id = create_alias(agent_id, alias_name)
    
    # Print summary
    print_summary(agent_id, alias_id, agent_config['agentName'])

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Deployment interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)