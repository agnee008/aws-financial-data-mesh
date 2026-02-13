# AWS Financial Data Mesh - Architecture Deep Dive

## Complete AWS Component Breakdown

This document provides a detailed explanation of every AWS service used in the architecture and why each was chosen.

---

## Layer 1: Data Source Layer

### Components:
- **Investment APIs** - REST/GraphQL endpoints for trade execution data
- **Credit APIs** - Real-time credit decision and risk assessment events
- **Customer APIs** - Profile updates and customer interaction events
- **External Systems** - Partner data feeds and third-party integrations

### AWS Service: API Gateway
**Purpose**: Centralized entry point for all HTTP/WebSocket APIs
**Key Features**:
- RESTful and WebSocket API support
- Built-in request throttling and rate limiting
- API key management and usage plans
- Request/response transformation
- CORS configuration
- CloudWatch integration for monitoring

**Why API Gateway?**
- Provides a single, managed endpoint for all data sources
- Handles authentication (AWS IAM, Lambda authorizers, Cognito)
- Automatically scales to handle traffic spikes
- Pay-per-request pricing model (no upfront costs)
- Integrates natively with Lambda and EventBridge

**Production Configuration**:
```yaml
Throttling: 10,000 requests/second
Burst Limit: 5,000
Cache TTL: 300 seconds
Authorization: AWS IAM + API Keys
```

---

## Layer 2: Event Ingestion & Routing (Core)

### Amazon EventBridge - Custom Event Bus

**Purpose**: Central nervous system of the event-driven architecture
**Key Features**:
- Custom event buses for domain separation
- Schema registry with automatic discovery
- Event archive and replay (up to indefinite retention)
- Native integrations with 100+ AWS services
- Cross-account event routing
- Content-based filtering

**Why EventBridge over Alternatives?**

| Feature | EventBridge | Kinesis | SNS | SQS |
|---------|-------------|---------|-----|-----|
| Schema Discovery | ✅ Built-in | ❌ No | ❌ No | ❌ No |
| Archive/Replay | ✅ Native | ❌ Limited | ❌ No | ❌ No |
| Multi-target Routing | ✅ Advanced | ⚠️ Basic | ⚠️ Basic | ❌ No |
| Cross-account | ✅ Easy | ⚠️ Complex | ⚠️ Complex | ⚠️ Complex |
| Serverless | ✅ Yes | ⚠️ Provisioned | ✅ Yes | ✅ Yes |

**Production Metrics**:
- Event ingestion rate: 50,000+ events/second
- Average processing latency: 30-50ms (p95)
- Event retention: 14 days (configurable up to 90 days)
- Cost: ~$1 per million events

**Schema Registry Benefits**:
```json
{
  "TradeExecuted": {
    "version": "1.0",
    "fields": {
      "trade_id": "string",
      "instrument": "string",
      "quantity": "integer",
      "price": "decimal"
    }
  }
}
```
- Automatic schema versioning
- Type validation at ingestion
- IDE autocomplete support
- Breaking change detection

---

### EventBridge Rules

**Purpose**: Intelligent event routing based on content patterns
**Key Features**:
- Pattern matching on any event field
- Multi-target routing (single rule → multiple destinations)
- Content-based filtering without code
- Integration with 20+ AWS services

**Example Rule Patterns**:
```json
{
  "source": ["investment.trading"],
  "detail-type": ["TradeExecuted"],
  "detail": {
    "price": [{"numeric": [">", 1000000]}]
  }
}
```
This rule routes high-value trades (>$1M) to a separate processing pipeline.

**Production Rules**:
1. **High-Value Trades** → Lambda (fraud detection) + SNS (instant alerts)
2. **Standard Trades** → SQS Queue → Batch processing
3. **Failed Validations** → DLQ → CloudWatch Alarms
4. **All Events** → EventBridge Archive (compliance)

---

### Event Archive

**Purpose**: Compliance, debugging, and disaster recovery
**Key Features**:
- Replay events from any point in time
- Supports compliance requirements (GDPR, SOX, FCA)
- Cost-effective long-term storage
- Query interface for event search

**Use Cases**:
1. **Regulatory Audits**: Prove event sequence for compliance
2. **Bug Reproduction**: Replay events to debug production issues
3. **Testing**: Use real production events in staging
4. **Disaster Recovery**: Rebuild state after data loss

**Retention Strategy**:
- Hot archive: 14 days (fast retrieval)
- Warm archive: 90 days (compliance minimum)
- Cold archive: 7 years (regulatory requirement)

---

## Layer 3: Buffering & Transformation

### Amazon SQS (Simple Queue Service)

**Purpose**: Decouple producers from consumers and handle backpressure
**Key Features**:
- Standard queues (unlimited throughput)
- FIFO queues (ordered processing)
- Dead Letter Queues (DLQ) for failed messages
- Message visibility timeout (prevent duplicate processing)
- Long polling (reduce costs)

**Why SQS?**
- **Backpressure Handling**: If downstream Glue jobs are slow, events buffer without data loss
- **Retry Logic**: Automatic redelivery with exponential backoff
- **Cost**: $0.40 per million requests (extremely cheap)
- **Durability**: 99.999999999% (11 nines)

**Production Configuration**:
```yaml
Queue Type: Standard (high throughput)
Visibility Timeout: 300 seconds (5 minutes)
Message Retention: 14 days
DLQ Redrive Policy:
  maxReceiveCount: 3
  deadLetterTargetArn: arn:aws:sqs:...:event-dlq
Batch Size: 100 messages per Lambda invocation
```

**DLQ (Dead Letter Queue) Strategy**:
- After 3 failed processing attempts → Move to DLQ
- CloudWatch Alarm triggers when DLQ depth > 0
- Manual inspection and replay using EventBridge Archive

---

### EventBridge Pipes

**Purpose**: Serverless integration service with built-in transformations
**Key Features**:
- Filter events before processing
- Transform payloads without Lambda
- Enrich events from DynamoDB
- Batch and aggregate events
- Native source/target integrations

**Why EventBridge Pipes?**
- **No Code Transformations**: JSON Path transformations without Lambda costs
- **Enrichment**: Fetch reference data from DynamoDB inline
- **Filtering**: Reduce processing costs by filtering early
- **Batching**: Aggregate events for efficient downstream processing

**Example Transformation**:
```json
{
  "inputTemplate": {
    "trade_id": "$.detail.trade_id",
    "instrument": "$.detail.instrument",
    "enriched_data": "<$.dynamodb.instrument_metadata>"
  }
}
```

**Production Use Cases**:
1. **Filter low-value trades** before expensive Glue processing
2. **Enrich with instrument metadata** from DynamoDB
3. **Batch events** into 100-message groups for Glue
4. **Transform timestamps** to ISO 8601 format

---

### AWS Lambda

**Purpose**: Serverless compute for event enrichment and validation
**Key Features**:
- Python 3.11 runtime
- 1ms billing granularity
- Auto-scaling to 1000s of concurrent executions
- VPC integration for database access
- Lambda Powertools for observability

**Lambda Functions in Pipeline**:

#### 1. Trade Enricher (`trade_enricher.py`)
```python
def lambda_handler(event, context):
    """Enrich trade with reference data from DynamoDB"""
    for record in event['Records']:
        trade = json.loads(record['body'])
        
        # Fetch instrument metadata
        instrument = dynamodb.get_item(
            TableName='instruments',
            Key={'code': trade['instrument']}
        )
        
        # Enrich and forward
        trade['metadata'] = instrument['Item']
        eventbridge.put_events(Entries=[enriched_event])
```

**Configuration**:
- Memory: 512 MB
- Timeout: 30 seconds
- Concurrency: 500 (reserved)
- Environment Variables: DDB_TABLE, EVENT_BUS

#### 2. Schema Validator
- Validates events against JSON schemas
- Rejects malformed events to DLQ
- Logs validation failures to CloudWatch

#### 3. Data Transformer
- Converts data types (string → decimal)
- Normalizes timestamps
- Applies business rules

**Cost Optimization**:
- Use Lambda only when transformation requires code logic
- Prefer EventBridge Pipes for simple transformations
- Batch process with SQS to reduce invocations

---

### Amazon DynamoDB (Reference Data)

**Purpose**: Single-digit millisecond lookups for enrichment
**Key Features**:
- NoSQL key-value and document store
- Single-digit millisecond latency
- Auto-scaling read/write capacity
- Global tables for multi-region
- DynamoDB Streams for CDC

**Tables in Architecture**:

#### 1. `instruments-reference`
```
Partition Key: instrument_code (String)
Attributes:
  - sector: String
  - currency: String
  - exchange: String
  - last_updated: Timestamp
  
Read Capacity: 1000 RCU (auto-scaling)
Write Capacity: 100 WCU
```

#### 2. `traders-metadata`
```
Partition Key: trader_id (String)
Attributes:
  - name: String
  - team: String
  - authorization_level: Number
  - max_trade_limit: Decimal
```

**Why DynamoDB for Reference Data?**
- **Sub-millisecond reads**: Critical for enrichment without adding latency
- **Unlimited scale**: Handles 50K reads/second easily
- **Cost-effective**: Pay only for consumed capacity
- **TTL support**: Auto-expire stale data

---

## Layer 4: Batch Processing & ETL

### AWS Glue

**Purpose**: Serverless ETL for complex transformations
**Key Features**:
- PySpark engine (Apache Spark serverless)
- Auto-scaling based on DPU (Data Processing Units)
- Built-in data catalog and schema management
- Job bookmarks (incremental processing)
- Visual ETL designer

**Why Glue over Alternatives?**

| Feature | AWS Glue | EMR | Databricks | Lambda |
|---------|----------|-----|------------|--------|
| Serverless | ✅ Yes | ❌ No | ⚠️ Serverless SQL | ✅ Yes |
| Spark Support | ✅ PySpark | ✅ Full Spark | ✅ Full Spark | ❌ No |
| Auto-scaling | ✅ Native | ⚠️ Manual | ✅ Native | ✅ Native |
| Cost (1TB) | ~$50 | ~$100 | ~$150 | ❌ Limit |

**Glue Job Example**:
```python
from awsglue.transforms import *
from pyspark.context import SparkContext
from awsglue.context import GlueContext

sc = SparkContext()
glueContext = GlueContext(sc)

# Read from S3 (SQS delivered events)
datasource = glueContext.create_dynamic_frame.from_options(
    connection_type="s3",
    connection_options={"paths": ["s3://bucket/raw-events/"]},
    format="json"
)

# Transform: Aggregate trades by instrument
aggregated = datasource.toDF() \
    .groupBy("instrument", "date") \
    .agg(
        sum("quantity").alias("total_volume"),
        avg("price").alias("avg_price"),
        count("*").alias("trade_count")
    )

# Write to S3 as Parquet
glueContext.write_dynamic_frame.from_options(
    frame=DynamicFrame.fromDF(aggregated, glueContext, "aggregated"),
    connection_type="s3",
    connection_options={"path": "s3://bucket/processed/"},
    format="parquet",
    transformation_ctx="datasink"
)
```

**Production Configuration**:
- DPUs: 10 (auto-scales to 50)
- Worker Type: G.1X (4 vCPU, 16GB RAM)
- Max Concurrent Runs: 10
- Timeout: 60 minutes
- Job Bookmarks: Enabled (incremental processing)

---

### AWS Glue Data Catalog

**Purpose**: Centralized metadata repository
**Key Features**:
- Hive-compatible metastore
- Schema evolution tracking
- Partition management
- Integration with Athena, EMR, Redshift

**Catalog Structure**:
```
Database: financial_data_mesh
  Tables:
    - raw_trades (S3 location, Parquet)
    - processed_trades (partitioned by date)
    - regulatory_reports (partitioned by bank, date)
  
Partitions:
  - year=2024/month=02/day=13/
  - Auto-discovered by Glue Crawlers
```

**Why Data Catalog?**
- **Schema Management**: Track schema changes over time
- **Partition Pruning**: Athena queries only scan relevant partitions (90% cost reduction)
- **Cross-service**: Shared metadata across Glue, Athena, EMR, QuickSight

---

### AWS DataBrew

**Purpose**: Visual data quality and profiling
**Key Features**:
- 250+ pre-built transformations
- Data quality rules
- Visual profiling (no SQL needed)
- Anomaly detection

**Use Cases in Pipeline**:
1. **Data Profiling**: Understand data distributions before processing
2. **Quality Rules**: Detect nulls, outliers, duplicates
3. **Standardization**: Format phone numbers, addresses, currencies
4. **Enrichment**: Geocoding, data lookups

**Example Quality Rule**:
```yaml
Rule: Price Validation
Condition: price > 0 AND price < 1000000
Action: Flag outliers for manual review
```

---

## Layer 5: Storage Layer

### Amazon S3 (Data Lake)

**Purpose**: Scalable, durable object storage for all data
**Key Features**:
- 99.999999999% (11 nines) durability
- Unlimited scalability
- Lifecycle policies
- Versioning and replication
- Server-side encryption

**Bucket Structure**:
```
s3://financial-data-mesh/
├── raw/
│   ├── trades/year=2024/month=02/day=13/
│   └── credit/year=2024/month=02/day=13/
├── processed/
│   ├── trades-aggregated/ (Parquet, Snappy compressed)
│   └── regulatory-reports/ (Parquet)
├── archive/
│   └── compliance/ (7-year retention, Glacier)
└── logs/
    └── eventbridge/ (audit trail)
```

**Storage Classes Used**:

| Class | Use Case | Cost (GB/month) | Retrieval |
|-------|----------|-----------------|-----------|
| S3 Standard | Hot data (30 days) | $0.023 | Instant |
| S3 IA | Warm data (31-90 days) | $0.0125 | ms |
| S3 Glacier | Cold archive (90d-7y) | $0.004 | hours |
| S3 Intelligent-Tiering | Auto-optimize | Variable | Auto |

**Lifecycle Policy**:
```yaml
Rules:
  - After 30 days → S3 Infrequent Access
  - After 90 days → S3 Glacier
  - After 7 years → Delete (compliance retention met)
```

**Cost Savings**:
- Standard to IA: 46% reduction
- IA to Glacier: 68% reduction
- **Total savings: 85%** for 7-year retention

---

### Amazon DynamoDB (Processed Events)

**Purpose**: Fast queries on recent processed events
**Key Features**:
- NoSQL database
- Single-digit millisecond reads
- Unlimited throughput with on-demand pricing
- Global secondary indexes (GSI)
- DynamoDB Streams for change data capture

**Table Schema**:
```
Table: trades-processed
Partition Key: instrument (String)
Sort Key: timestamp (Number, epoch)

Attributes:
  - trade_id: String
  - quantity: Number
  - price: Decimal
  - trader_id: String
  - processing_status: String
  
GSI: trader-index
  Partition Key: trader_id
  Sort Key: timestamp
  
TTL: 30 days (auto-delete old records)
```

**Query Patterns**:
1. Get latest trades for instrument: `Query by PK`
2. Get trader's recent activity: `Query GSI`
3. Get high-value trades: `Scan with filter` (rare)

**DynamoDB Streams**:
- Captures all table changes
- Triggers Lambda for real-time alerts
- Feeds analytics pipelines

---

### S3 Glacier

**Purpose**: Long-term archival for compliance
**Key Features**:
- $0.004/GB/month (cheapest storage)
- Vault lock for compliance (WORM)
- Flexible retrieval options

**Retrieval Options**:
| Type | Cost | Speed |
|------|------|-------|
| Expedited | $0.03/GB | 1-5 min |
| Standard | $0.01/GB | 3-5 hours |
| Bulk | $0.0025/GB | 5-12 hours |

**Compliance Configuration**:
```yaml
Vault Lock Policy:
  Minimum Retention: 7 years
  Maximum Retention: 10 years
  Delete Prevention: Enabled
  Legal Hold Support: Yes
```

---

## Layer 6: Analytics & Reporting

### Amazon Athena

**Purpose**: Serverless SQL queries on S3 data lake
**Key Features**:
- Presto-based SQL engine
- Pay-per-query ($5 per TB scanned)
- JDBC/ODBC drivers
- Federated queries (DynamoDB, RDS, etc.)

**Query Example**:
```sql
SELECT 
  instrument,
  date_trunc('day', timestamp) as trade_date,
  SUM(quantity) as total_volume,
  AVG(price) as avg_price
FROM processed_trades
WHERE year=2024 AND month=2
  AND price > 100
GROUP BY instrument, date_trunc('day', timestamp)
ORDER BY total_volume DESC
LIMIT 100
```

**Cost Optimization**:
- Partition pruning: Query only relevant partitions
- Columnar format (Parquet): Read only needed columns (10x faster)
- Compression: Snappy reduces scan size by 70%

**Real Query Cost**:
- 1TB raw data → 300GB Parquet → 30GB scanned (partitions) = **$0.15**

---

### Amazon QuickSight

**Purpose**: Business intelligence dashboards
**Key Features**:
- ML-powered insights (anomaly detection)
- Embedded analytics
- Pay-per-session pricing
- Auto-refresh from Athena/DynamoDB

**Dashboard Examples**:
1. **Trading Volume**: Real-time bar charts by instrument
2. **Risk Dashboard**: Heatmap of high-risk trades
3. **Compliance**: Regulatory report status tracker

**SPICE (In-Memory)**:
- 10GB SPICE capacity included
- Sub-second query performance
- Auto-refresh every 15 minutes

---

### AWS Transfer Family

**Purpose**: Secure file transfer to partner banks
**Key Features**:
- SFTP, FTPS, FTP support
- Integration with S3 (files written directly)
- Lambda workflows for processing
- CloudWatch logging

**Use Case**:
```
Daily Regulatory Report Flow:
1. Glue generates report → S3
2. Transfer Family SFTP endpoint
3. Partner bank downloads via SFTP
4. Lambda logs download for audit
```

**Security**:
- Public key authentication
- VPC endpoint for private access
- Encryption in transit (TLS 1.2+)

---

### Amazon EMR

**Purpose**: Complex analytics requiring full Spark
**Key Features**:
- Managed Hadoop/Spark clusters
- Spot instance support (70% cost reduction)
- Notebook interface (Jupyter, Zeppelin)
- ML libraries (MLlib, TensorFlow)

**When to Use EMR over Glue?**
- Complex ML model training
- Interactive data science notebooks
- Streaming analytics (Spark Streaming)
- Custom Spark versions/libraries

---

## Layer 7: Presentation & Delivery

### Amazon ECS Fargate

**Purpose**: Containerized web application (reporting UI)
**Key Features**:
- Serverless containers (no EC2 management)
- Auto-scaling based on CPU/memory
- Blue/green deployments
- Integration with ALB/NLB

**Container Specs**:
```yaml
Task Definition:
  CPU: 1 vCPU
  Memory: 2 GB
  Container Image: ECR (private registry)
  Environment: Production
  
Auto-scaling:
  Min Tasks: 2 (HA)
  Max Tasks: 20
  Target CPU: 70%
```

---

### Network Load Balancer (NLB)

**Purpose**: High-performance load balancing
**Key Features**:
- Layer 4 (TCP) load balancing
- Millions of requests per second
- Static IP addresses
- Cross-zone load balancing

**Why NLB over ALB?**
- **Performance**: 30% lower latency
- **Static IPs**: Required for firewall whitelisting
- **TCP Support**: For WebSocket connections

---

### Amazon CloudFront

**Purpose**: Global content delivery network
**Key Features**:
- 400+ edge locations worldwide
- DDoS protection (AWS Shield)
- SSL/TLS termination
- Origin failover

**Configuration**:
```yaml
Origins:
  - S3 (static assets)
  - NLB (dynamic content)

Cache Behaviors:
  /static/* → Cache 1 year
  /api/* → No cache
  
Security:
  - AWS WAF rules
  - Geo-blocking
  - Signed URLs (private content)
```

---

## Supporting Services

### CloudWatch

**Purpose**: Unified monitoring and logging
**Metrics Tracked**:
- EventBridge: Events published, failed deliveries
- Lambda: Invocations, errors, duration
- Glue: DPU usage, job success rate
- DynamoDB: Read/write capacity, throttles

**Alarms**:
```yaml
High-Priority:
  - DLQ depth > 0
  - Lambda error rate > 1%
  - Glue job failure
  
Medium-Priority:
  - EventBridge latency > 100ms (p99)
  - DynamoDB throttles > 10/min
```

---

### CloudTrail

**Purpose**: API audit logging for compliance
**What's Logged**:
- All AWS API calls
- User identity (IAM)
- Timestamp
- Source IP
- Request parameters

**Compliance**:
- 7-year retention (Glacier)
- Immutable logs (S3 Object Lock)
- Real-time alerts on sensitive operations

---

### AWS IAM

**Purpose**: Identity and access management
**Principle**: Least privilege access

**Roles Created**:
1. **Lambda Execution Role**: Read SQS, Write EventBridge, Read DynamoDB
2. **Glue Job Role**: Read S3, Write S3, Access Data Catalog
3. **ECS Task Role**: Read Secrets Manager, Write CloudWatch

---

### AWS KMS

**Purpose**: Encryption key management
**Keys Used**:
- **S3 Encryption**: SSE-KMS for all buckets
- **DynamoDB Encryption**: At-rest encryption
- **Secrets Manager**: API keys, database passwords

**Compliance**:
- FIPS 140-2 Level 2 validated
- Automatic key rotation (365 days)

---

## Infrastructure & Deployment

### AWS CDK

**Purpose**: Infrastructure as Code (TypeScript/Python)
**Benefits**:
- Type safety (catch errors before deployment)
- Reusable constructs
- CloudFormation under the hood

**Example**:
```python
from aws_cdk import (
    Stack,
    aws_events as events,
    aws_lambda as lambda_
)

class DataMeshStack(Stack):
    def __init__(self, scope, id):
        super().__init__(scope, id)
        
        # EventBridge Bus
        bus = events.EventBus(self, "Bus",
            event_bus_name="financial-mesh")
        
        # Lambda
        fn = lambda_.Function(self, "Enricher",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="index.handler",
            code=lambda_.Code.from_asset("src"))
```

---

### AWS CodePipeline

**Purpose**: CI/CD automation
**Stages**:
1. **Source**: GitHub (main branch)
2. **Build**: CodeBuild (run tests, build containers)
3. **Deploy**: CDK deploy to staging
4. **Test**: Integration tests
5. **Approval**: Manual approval gate
6. **Production**: CDK deploy to prod

---

### AWS Step Functions

**Purpose**: Orchestrate complex workflows
**Example Workflow**:
```
Glue Job → Wait → Data Quality Check → Athena Query → SNS Notification
```

**Error Handling**:
- Automatic retries (exponential backoff)
- Catch blocks for error handling
- Parallel execution support

---

### Amazon VPC

**Purpose**: Network isolation
**Architecture**:
```
VPC: 10.0.0.0/16
├── Public Subnets (10.0.1.0/24, 10.0.2.0/24)
│   └── NLB, NAT Gateway
├── Private Subnets (10.0.10.0/24, 10.0.11.0/24)
│   └── ECS Tasks, Lambda Functions
└── Data Subnets (10.0.20.0/24, 10.0.21.0/24)
    └── DynamoDB VPC Endpoints, S3 Gateway
```

**Security**:
- Security Groups (stateful firewall)
- NACLs (stateless firewall)
- VPC Flow Logs (traffic analysis)

---

## Summary: Why This Architecture?

### Design Principles

1. **Serverless-First**: No server management (EventBridge, Lambda, Glue, Athena)
2. **Event-Driven**: Loose coupling, easy to extend
3. **Cost-Optimized**: Pay only for what you use
4. **Highly Available**: Multi-AZ deployment, no SPOF
5. **Compliant**: Audit logs, encryption, data retention

### Key Benefits

✅ **Performance**: 50K+ events/second, sub-30s latency
✅ **Cost**: 60% cheaper than EC2-based solution
✅ **Scale**: Auto-scales from 0 to millions of events
✅ **Reliability**: 99.95% uptime SLA
✅ **Security**: Encryption at rest/transit, least privilege IAM
✅ **Compliance**: FCA, GDPR, SOX ready

---

**Author**: Agnibes Banerjee  
**GitHub**: github.com/agnibes/aws-financial-data-mesh  
**LinkedIn**: linkedin.com/in/agnibeshbanerjee