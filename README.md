# AWS Financial Data Mesh - Event-Driven Architecture

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![AWS](https://img.shields.io/badge/AWS-EventBridge-orange)](https://aws.amazon.com/eventbridge/)
[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://www.python.org/)
[![CDK](https://img.shields.io/badge/IaC-AWS_CDK-green)](https://aws.amazon.com/cdk/)

A production-ready reference architecture for building real-time, event-driven data pipelines using AWS services and Data Mesh principles. Built for FinTech and regulated industries requiring low-latency, compliant data processing.

**Based on production implementations at Barclays and Dyson, handling 50,000+ events/second.**

## 🎯 Project Overview

This repository demonstrates a complete implementation of an event-driven data architecture that:
- Processes financial events in real-time (sub-second latency)
- Implements Data Mesh principles for domain ownership
- Provides serverless scalability and cost optimization
- Ensures regulatory compliance with audit trails
- Deploys via Infrastructure as Code (AWS CDK)

## 📐 Architecture

```
Data Sources → EventBridge → Transformation → Processing → Storage → Analytics
    (APIs)      (Routing)      (Lambda/Pipes)    (Glue)      (S3/DDB)  (Athena/QS)
```

### Key Components

| Component | Purpose | AWS Service |
|-----------|---------|-------------|
| Event Ingestion | Capture domain events | EventBridge Custom Bus |
| Event Routing | Filter and route events | EventBridge Rules |
| Buffering | Handle backpressure | SQS Queues |
| Enrichment | Add reference data | Lambda + DynamoDB |
| Transformation | Data quality & cleaning | EventBridge Pipes + Lambda |
| Batch Processing | Complex transformations | AWS Glue (PySpark) |
| Data Lake | Long-term storage | S3 |
| Fast Queries | Real-time lookups | DynamoDB |
| Ad-hoc Analysis | SQL queries | Athena |
| Dashboards | Business intelligence | QuickSight |

## 🚀 Quick Start

### Prerequisites

- AWS Account with appropriate permissions
- AWS CLI configured
- Python 3.11+
- Node.js 18+ (for CDK)
- Docker (for local testing)

### Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/aws-financial-data-mesh.git
cd aws-financial-data-mesh

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install CDK dependencies
cd infrastructure
npm install
cd ..
```

### Deployment

```bash
# Bootstrap CDK (first time only)
cd infrastructure
cdk bootstrap aws://ACCOUNT-ID/REGION

# Deploy the stack
cdk deploy DataMeshStack

# Output will include:
# - EventBridge Bus ARN
# - SQS Queue URLs
# - Lambda Function ARNs
# - S3 Bucket names
```

## 📁 Project Structure

```
aws-financial-data-mesh/
├── src/
│   ├── publishers/              # Event publishing code
│   │   ├── trade_publisher.py
│   │   ├── credit_publisher.py
│   │   └── customer_publisher.py
│   ├── processors/              # Lambda functions
│   │   ├── enrichment/
│   │   │   └── trade_enricher.py
│   │   ├── validation/
│   │   │   └── schema_validator.py
│   │   └── transformation/
│   │       └── data_transformer.py
│   ├── glue_jobs/              # PySpark ETL jobs
│   │   ├── trade_aggregation.py
│   │   └── regulatory_reporting.py
│   └── schemas/                # Event schemas
│       ├── trade_executed.json
│       └── credit_decision.json
├── infrastructure/             # AWS CDK code
│   ├── lib/
│   │   ├── event-bus-stack.ts
│   │   ├── processing-stack.ts
│   │   └── storage-stack.ts
│   ├── bin/
│   │   └── app.ts
│   └── cdk.json
├── tests/                     # Unit and integration tests
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── docs/                      # Documentation
│   ├── architecture.md
│   ├── deployment-guide.md
│   └── cost-analysis.md
├── examples/                  # Usage examples
│   └── publish_events.py
├── requirements.txt
├── README.md
└── LICENSE
```

## 💻 Usage Examples

### Publishing Events

```python
from src.publishers.trade_publisher import TradeEventPublisher

# Initialize publisher
publisher = TradeEventPublisher()

# Publish a trade execution event
trade_data = {
    'trade_id': 'TRD0000001234',
    'instrument': 'AAPL',
    'quantity': 100,
    'price': 150.25,
    'trader_id': 'TRD001',
    'direction': 'BUY',
    'exchange': 'NASDAQ'
}

event_id = publisher.publish_trade(trade_data)
print(f"Published event: {event_id}")
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test suite
pytest tests/unit/publishers/

# Integration tests (requires AWS credentials)
pytest tests/integration/ --aws
```

## 📊 Performance & Costs

### Performance Metrics (Production)
- **Event Latency**: 30-50ms (p95)
- **Throughput**: 50,000 events/second
- **End-to-end Latency**: <30 seconds for regulatory reports
- **Availability**: 99.95% uptime

### Cost Analysis (Monthly, 1M events/day)
- EventBridge: ~$10
- Lambda: ~$25
- SQS: ~$5
- Glue: ~$100
- S3: ~$20
- DynamoDB: ~$50
- **Total: ~$210/month**

*60% cheaper than equivalent EC2-based solution*

See [docs/cost-analysis.md](docs/cost-analysis.md) for detailed breakdown.

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test suite
pytest tests/unit/publishers/

# Integration tests (requires AWS credentials)
pytest tests/integration/ --aws
```

## 📚 Documentation

- [Architecture Deep Dive](docs/architecture.md)
- [Deployment Guide](docs/deployment-guide.md)
- [Cost Optimization](docs/cost-analysis.md)
- [Security Best Practices](docs/security.md)
- [Troubleshooting](docs/troubleshooting.md)

## 🛠️ Technology Stack

- **AWS Services**: EventBridge, Lambda, SQS, Glue, S3, DynamoDB, Athena, QuickSight
- **Languages**: Python 3.11, SQL, TypeScript
- **Frameworks**: AWS CDK, AWS Lambda Powertools, PySpark
- **Tools**: pytest, boto3, GitLab CI/CD

## 🗺️ Planned Features

- [x] Core event-driven architecture
- [ ] Kinesis Data Streams integration comparison
- [ ] CDC pipeline with DynamoDB Streams
- [ ] Apache Kafka on MSK implementation
- [ ] Delta Lake for ACID transactions
- [ ] dbt integration for data quality
- [ ] SageMaker fraud detection model
- [ ] Multi-region disaster recovery setup
- [ ] Complete production deployment guide

Features will be added based on community feedback and real-world use cases.

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file.

## 👤 Author

**Agnibes Banerjee**
- Lead AWS Data Engineer
- 8 years experience in cloud-native data architectures
- Previously: Dyson (UK), IBM (UK), Barclays (India)

Connect with me:
- LinkedIn: [linkedin.com/in/agnibeshbanerjee](https://linkedin.com/in/agnibeshbanerjee)
- Medium: [@agnibes](https://medium.com/@agnee008)
- Email: agnee008@gmail.com

## 🙏 Acknowledgments

- Inspired by production systems at Barclays and Dyson
- AWS EventBridge team for excellent documentation
- Data Mesh community for architectural patterns
- UK FinTech sector for real-world use cases

## ⭐ Support

If you find this project helpful, please consider:
- Starring the repository
- Sharing it with your network
- Contributing improvements
- Providing feedback via issues

---

**Production-grade data engineering solutions for UK FinTech challenges.**

#DataEngineering #AWS #EventDriven #DataMesh #OpenSource
