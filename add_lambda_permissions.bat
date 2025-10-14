@echo off
echo ==========================================
echo Adding Lambda Permissions for Bedrock Agent
echo ==========================================

set AGENT_ARN=arn:aws:bedrock:us-east-1:986341371998:agent/8F18B4HMDE
set REGION=us-east-1

echo Adding permission for Customer Verification Lambda...
aws lambda add-permission ^
  --function-name autosettled-customer-verification ^
  --statement-id bedrock-agent-invoke ^
  --action lambda:InvokeFunction ^
  --principal bedrock.amazonaws.com ^
  --source-arn %AGENT_ARN% ^
  --region %REGION%

echo.
echo Adding permission for Policy Verification Lambda...
aws lambda add-permission ^
  --function-name autosettled-policy-verification ^
  --statement-id bedrock-agent-invoke ^
  --action lambda:InvokeFunction ^
  --principal bedrock.amazonaws.com ^
  --source-arn %AGENT_ARN% ^
  --region %REGION%

echo.
echo Adding permission for Damage Analysis Lambda...
aws lambda add-permission ^
  --function-name autosettled-damage-analysis ^
  --statement-id bedrock-agent-invoke ^
  --action lambda:InvokeFunction ^
  --principal bedrock.amazonaws.com ^
  --source-arn %AGENT_ARN% ^
  --region %REGION%

echo.
echo Adding permission for Document Analysis Lambda...
aws lambda add-permission ^
  --function-name autosettled-document-analysis ^
  --statement-id bedrock-agent-invoke ^
  --action lambda:InvokeFunction ^
  --principal bedrock.amazonaws.com ^
  --source-arn %AGENT_ARN% ^
  --region %REGION%

echo.
echo Adding permission for Settlement Decision Lambda...
aws lambda add-permission ^
  --function-name autosettled-settlement-decision ^
  --statement-id bedrock-agent-invoke ^
  --action lambda:InvokeFunction ^
  --principal bedrock.amazonaws.com ^
  --source-arn %AGENT_ARN% ^
  --region %REGION%

echo.
echo ==========================================
echo All Lambda permissions added successfully!
echo ==========================================
