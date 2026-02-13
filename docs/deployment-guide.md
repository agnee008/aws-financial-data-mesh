# Deployment Guide

This guide walks you through deploying the AWS Financial Data Mesh architecture.

## Prerequisites

Before you begin, ensure you have:

- **AWS Account** with appropriate permissions
- **AWS CLI** configured with credentials
- **Python 3.11+** installed
- **Node.js 18+** installed (for CDK)
- **Docker** installed (for local testing)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/aws-financial-data-mesh.git
cd aws-financial-data-mesh
```

### 2. Set Up Python Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 3. Set Up CDK Environment

```bash
cd infrastructure

# Install Node dependencies
npm install

# Build TypeScript
npm run build
```

## AWS Configuration

### 1. Configure AWS CLI

```bash
aws configure
# Enter your AWS Access Key ID
# Enter your AWS Secret Access Key
# Default region: eu-west-2 (or your preferred region)
# Default output format: json
```

### 2. Bootstrap CDK (First Time Only)

```bash
cd infrastructure

# Bootstrap CDK in your account/region
cdk bootstrap aws://ACCOUNT-ID/REGION

# Example:
cdk bootstrap aws://123456789012/eu-west-2
```

## Deployment

### Option 1: Deploy Everything (Recommended for First Time)

```bash
cd infrastructure

# Review what will be deployed
cdk diff

# Deploy the stack
cdk deploy

# Approve the changes when prompted
```

### Option 2: Deploy Specific Environment

```bash
# Deploy to development
cdk deploy DataMeshStack-dev

# Deploy to production
cdk deploy DataMeshStack-prod --context environment=prod
```

## Post-Deployment Configuration

### 1. Populate Reference Data

After deployment, populate the DynamoDB instruments table:

```python
import boto3
from decimal import Decimal

dynamodb = boto3.resource('dynamodb', region_name='eu-west-2')
table = dynamodb.Table('dev-instruments-reference')

# Add sample instruments
instruments = [
    {
        'instrument_code': 'AAPL',
        'sector': 'Technology',
        'currency': 'USD',
        'exchange': 'NASDAQ',
        'industry': 'Consumer Electronics'
    },
    {
        'instrument_code': 'GOOGL',
        'sector': 'Technology',
        'currency': 'USD',
        'exchange': 'NASDAQ',
        'industry': 'Internet Services'
    }
]

for instrument in instruments:
    table.put_item(Item=instrument)

print("✅ Reference data populated")
```

### 2. Test Event Publishing

```bash
# Run example script
python examples/publish_events.py
```

### 3. Verify in AWS Console

1. **EventBridge**: Check that events are being published
   - Go to EventBridge > Event buses > financial-data-mesh-bus
   - View metrics and events

2. **SQS**: Verify messages in queue
   - Go to SQS > Queues > dev-trade-queue
   - Check message count

3. **Lambda**: Check enrichment function logs
   - Go to Lambda > Functions > dev-trade-enricher
   - View CloudWatch logs

4. **DynamoDB**: Verify reference data
   - Go to DynamoDB > Tables > dev-instruments-reference
   - Explore items

## Monitoring

### CloudWatch Dashboards

The deployment creates CloudWatch alarms for:
- Dead Letter Queue messages
- Lambda function errors
- EventBridge failed invocations

Access them at:
```
https://console.aws.amazon.com/cloudwatch/home?region=eu-west-2#alarmsV2:
```

### Logs

View logs for each component:

```bash
# Lambda logs
aws logs tail /aws/lambda/dev-trade-enricher --follow

# EventBridge archive
aws events list-archives
```

## Teardown

To remove all deployed resources:

```bash
cd infrastructure

# Destroy the stack
cdk destroy

# Confirm when prompted
```

**Warning**: This will delete all resources including:
- S3 buckets (if empty)
- DynamoDB tables
- Lambda functions
- EventBridge rules

## Troubleshooting

### Issue: CDK Bootstrap Fails

**Solution**: Ensure you have AdministratorAccess or these permissions:
- cloudformation:*
- s3:*
- iam:*
- ecr:*

### Issue: Lambda Function Timeout

**Solution**: Increase timeout in CDK:
```typescript
timeout: cdk.Duration.seconds(60)
```

### Issue: Events Not Appearing in Queue

**Solution**: Check EventBridge rule:
```bash
aws events list-rules --event-bus-name financial-data-mesh-bus
```

### Issue: DynamoDB Access Denied

**Solution**: Verify Lambda execution role has DynamoDB permissions:
```bash
aws iam get-role-policy --role-name LAMBDA_ROLE --policy-name POLICY_NAME
```

## Cost Estimation

### Monthly Costs (1M events/day)

- **EventBridge**: ~$10
- **Lambda**: ~$25 (500k invocations)
- **SQS**: ~$5
- **DynamoDB**: ~$50 (on-demand)
- **S3**: ~$20 (100GB)
- **CloudWatch**: ~$5

**Total**: ~$115/month

See [cost-analysis.md](cost-analysis.md) for detailed breakdown.

## Next Steps

1. ✅ Deploy infrastructure
2. ✅ Populate reference data
3. ✅ Test event publishing
4. 📊 Set up monitoring dashboards
5. 🔒 Configure security policies
6. 📈 Scale based on load

For more information:
- [Architecture Documentation](architecture.md)
- [Security Best Practices](security.md)
- [Troubleshooting Guide](troubleshooting.md)
