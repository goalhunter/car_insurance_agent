import boto3
import subprocess
import sys
import os

def run_command(command, cwd=None, shell=False):
    """Run a shell command and handle errors"""
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            shell=shell,
            check=True,
            capture_output=True,
            text=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running command: {' '.join(command) if isinstance(command, list) else command}")
        print(f"   {e.stderr}")
        sys.exit(1)

def get_stack_outputs(stack_name):
    """Get CloudFormation stack outputs"""
    print("Fetching CloudFormation stack outputs...")

    cf_client = boto3.client('cloudformation')

    try:
        response = cf_client.describe_stacks(StackName=stack_name)
        outputs = response['Stacks'][0]['Outputs']

        # Convert to dictionary
        output_dict = {}
        for output in outputs:
            output_dict[output['OutputKey']] = output['OutputValue']

        return output_dict

    except Exception as e:
        print(f"❌ Error fetching stack outputs: {e}")
        print(f"   Make sure the stack '{stack_name}' is deployed.")
        sys.exit(1)

def create_env_file(api_url, upload_url):
    """Create .env.production file"""
    print("Updating environment variables...")

    env_content = f"""VITE_API_BASE_URL={api_url}
VITE_UPLOAD_API_URL={upload_url}
"""

    env_path = os.path.join('..', 'frontend', '.env.production')

    try:
        with open(env_path, 'w') as f:
            f.write(env_content)
        print(f"   ✅ Created {env_path}")
    except Exception as e:
        print(f"❌ Error creating .env.production: {e}")
        sys.exit(1)

def main():
    print("=" * 50)
    print("Frontend Deployment Script")
    print("=" * 50)
    print()

    # Configuration
    STACK_NAME = "autosettled-stack"

    # Step 1: Get stack outputs
    outputs = get_stack_outputs(STACK_NAME)

    frontend_bucket = outputs.get('FrontendBucketName')
    cloudfront_distribution_id = outputs.get('CloudFrontDistributionId')
    cloudfront_url = outputs.get('CloudFrontURL')
    api_url = outputs.get('ApiGatewayUrl')

    # Display configuration
    print(f"Frontend Bucket: {frontend_bucket}")
    print(f"CloudFront Distribution ID: {cloudfront_distribution_id}")
    print(f"CloudFront URL: {cloudfront_url}")
    print(f"API URL: {api_url}")
    print()

    # Validate outputs
    if not all([frontend_bucket, cloudfront_distribution_id, cloudfront_url]):
        print("❌ Error: Missing required stack outputs")
        sys.exit(1)

    # Step 2: Create environment file
    # Use the API Gateway URL from stack outputs for both endpoints
    create_env_file(
        api_url=api_url,
        upload_url=api_url
    )

    # Step 3: Install dependencies
    print("Installing dependencies...")
    run_command(['npm', 'install'], cwd='../frontend')
    print("   ✅ Dependencies installed")
    print()

    # Step 4: Build the frontend
    print("Building frontend...")
    run_command(['npm', 'run', 'build'], cwd='../frontend')
    print("   ✅ Build complete")
    print()

    # Step 5: Upload to S3
    print("Uploading frontend to S3...")
    dist_path = os.path.join('..', 'frontend', 'dist') + os.sep
    s3_path = f's3://{frontend_bucket}/'

    run_command([
        'aws', 's3', 'sync',
        dist_path,
        s3_path,
        '--delete'
    ])
    print("   ✅ Upload complete")
    print()

    # Step 6: Invalidate CloudFront cache
    print("Invalidating CloudFront cache...")
    run_command([
        'aws', 'cloudfront', 'create-invalidation',
        '--distribution-id', cloudfront_distribution_id,
        '--paths', '/*'
    ])
    print("   ✅ Cache invalidated")
    print()

    # Success message
    print("=" * 50)
    print("✅ Deployment Complete!")
    print("=" * 50)
    print(f"Frontend URL: https://{cloudfront_url}")
    print()
    print("Note: CloudFront invalidation may take a few minutes to complete.")

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
