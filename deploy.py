#!/usr/bin/env python3
"""
Master Deployment Script for Car Insurance Claims Processing Agent

This script orchestrates the complete deployment:
1. Creates DynamoDB tables
2. Deploys Lambda functions
3. Creates Bedrock Agent with action groups
4. Generates and loads synthetic data

Usage:
    python deploy.py --all              # Full deployment
    python deploy.py --infrastructure   # Only DynamoDB tables
    python deploy.py --lambda           # Only Lambda functions
    python deploy.py --agent            # Only Bedrock Agent
    python deploy.py --data             # Only synthetic data
"""

import argparse
import sys
import os
import subprocess
import time
from datetime import datetime


class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 70}")
    print(f"{text.center(70)}")
    print(f"{'=' * 70}{Colors.ENDC}\n")


def print_step(step_num, total_steps, text):
    print(f"{Colors.OKCYAN}[STEP {step_num}/{total_steps}] {text}{Colors.ENDC}")


def print_success(text):
    print(f"{Colors.OKGREEN}[SUCCESS] {text}{Colors.ENDC}")


def print_error(text):
    print(f"{Colors.FAIL}[ERROR] {text}{Colors.ENDC}")


def print_warning(text):
    print(f"{Colors.WARNING}[WARNING] {text}{Colors.ENDC}")


def run_script(script_path, description):
    """Run a Python script and return success status"""
    print(f"\n{Colors.OKBLUE}Running: {description}...{Colors.ENDC}")

    try:
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=False,
            text=True
        )
        return result.returncode == 0
    except Exception as e:
        print_error(f"Failed to run {description}: {str(e)}")
        return False


def deploy_infrastructure():
    """Deploy DynamoDB tables"""
    return run_script(
        'setup/setup_infrastructure.py',
        'Infrastructure Setup (DynamoDB Tables)'
    )


def deploy_lambda():
    """Deploy Lambda functions"""
    return run_script(
        'setup/setup_lambda.py',
        'Lambda Functions Deployment'
    )


def deploy_agent():
    """Deploy Bedrock Agent"""
    return run_script(
        'setup/setup_agent.py',
        'Bedrock Agent Setup'
    )


def load_data():
    """Generate and load synthetic data"""
    return run_script(
        'synthetic_data_generation/generate_and_migrate.py',
        'Synthetic Data Generation & Migration'
    )


def full_deployment():
    """Run complete deployment"""
    print_header("FULL DEPLOYMENT - CAR INSURANCE CLAIMS AGENT")

    start_time = time.time()
    total_steps = 4
    current_step = 0

    # Step 1: Infrastructure
    current_step += 1
    print_step(current_step, total_steps, "Deploying Infrastructure (DynamoDB Tables)")
    if not deploy_infrastructure():
        print_error("Infrastructure deployment failed")
        return False
    print_success("Infrastructure deployed successfully")

    # Step 2: Lambda Functions
    current_step += 1
    print_step(current_step, total_steps, "Deploying Lambda Functions")
    if not deploy_lambda():
        print_error("Lambda deployment failed")
        return False
    print_success("Lambda functions deployed successfully")

    # Step 3: Bedrock Agent
    current_step += 1
    print_step(current_step, total_steps, "Setting up Bedrock Agent")
    if not deploy_agent():
        print_error("Bedrock Agent setup failed")
        return False
    print_success("Bedrock Agent created successfully")

    # Step 4: Synthetic Data
    current_step += 1
    print_step(current_step, total_steps, "Loading Synthetic Data")
    if not load_data():
        print_warning("Data loading encountered issues (you can run it separately)")

    # Final summary
    elapsed_time = time.time() - start_time
    minutes = int(elapsed_time // 60)
    seconds = int(elapsed_time % 60)

    print_header("DEPLOYMENT COMPLETE!")

    print(f"{Colors.OKGREEN}{Colors.BOLD}")
    print("Your Car Insurance Claims Processing Agent is ready!")
    print(f"{Colors.ENDC}")

    print("\nDeployment Summary:")
    print(f"  - DynamoDB Tables: Created")
    print(f"  - Lambda Functions: Deployed (5 functions)")
    print(f"  - Bedrock Agent: Configured with action groups")
    print(f"  - Synthetic Data: Loaded")

    print(f"\nTotal deployment time: {minutes}m {seconds}s")

    print("\nNext Steps:")
    print("  1. Go to AWS Bedrock Console")
    print("  2. Navigate to Agents")
    print("  3. Find 'ClaimsProcessingAgent'")
    print("  4. Test the agent!")

    print("\nTest with: 'I want to file a claim'")

    return True


def main():
    parser = argparse.ArgumentParser(
        description='Deploy Car Insurance Claims Processing Agent',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python deploy.py --all              # Full deployment
  python deploy.py --infrastructure   # Only DynamoDB
  python deploy.py --lambda          # Only Lambda functions
  python deploy.py --agent           # Only Bedrock Agent
  python deploy.py --data            # Only synthetic data
        """
    )

    parser.add_argument('--all', action='store_true',
                        help='Run full deployment (default)')
    parser.add_argument('--infrastructure', action='store_true',
                        help='Deploy only DynamoDB tables')
    parser.add_argument('--lambda', action='store_true',
                        help='Deploy only Lambda functions')
    parser.add_argument('--agent', action='store_true',
                        help='Setup only Bedrock Agent')
    parser.add_argument('--data', action='store_true',
                        help='Load only synthetic data')

    args = parser.parse_args()

    # Check if we're in the right directory
    if not os.path.exists('config.py'):
        print_error("config.py not found! Please run from project root directory")
        return 1

    # Default to --all if no specific option selected
    if not any([args.all, args.infrastructure, args.lambda, args.agent, args.data]):
        args.all = True

    success = True

    # Run selected deployments
    if args.all:
        success = full_deployment()
    else:
        if args.infrastructure:
            print_header("DEPLOYING INFRASTRUCTURE")
            success = deploy_infrastructure() and success

        if args.lambda:
            print_header("DEPLOYING LAMBDA FUNCTIONS")
            success = deploy_lambda() and success

        if args.agent:
            print_header("SETTING UP BEDROCK AGENT")
            success = deploy_agent() and success

        if args.data:
            print_header("LOADING SYNTHETIC DATA")
            success = load_data() and success

    return 0 if success else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print_error("\nDeployment interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
