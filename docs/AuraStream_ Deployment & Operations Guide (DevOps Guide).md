AuraStream: Deployment & Operations Guide (DevOps Guide)

| Section | Key Content to Include |
| :---- | :---- |
| **1\. Prerequisites** | **Tools:** AWS CLI, AWS SAM CLI (or Terraform CLI), Docker, Python 3.9+. **Permissions:** IAM user with $\\text{AdministratorAccess}$ (or a custom policy allowing $\\text{CloudFormation, Lambda, API Gateway, S3, Step Functions, DynamoDB}$ access). |
| **2\. Infrastructure as Code (IaC) Template Snippet** | *(Example: For the core synchronous Lambda function)* SentimentLambda: Type: AWS::Serverless::Function Properties: Handler: src.handler Runtime: python3.9 MemorySize: 256 Timeout: 20 Policies: \[ComprehendFullAccess\] Events: Api: Type: Api Properties: Path: /analyze/sync Method: POST |
| **3\. Deployment Steps** | 1\. sam build \--use-container (For local package compilation). 2\. sam deploy \--guided (To deploy the stack to AWS). 3\. Verify **CloudFormation** stack status. |
| **4\. Operational Monitoring (MLOps)** | **AWS CloudWatch Dashboards:** 1\. **Synchronous Health:** Monitor p99 Latency (must be $\< 1000$ms), Error Count (API Gateway/Lambda), and Cold Start Duration. 2\. **Asynchronous Health:** Monitor SQS Queue Depth (backlog), Step Function Execution Success/Failure Rate. **Alerts:** Set up SNS alerts for Lambda Error Rate \> 5% or SQS Queue Depth \> 100 messages. |
| **5\. Cost Optimization Strategy** | **Scheduled Shutdown:** **Step Functions** state machines for batch processing should be designed to terminate completely (including any $\\text{DynamoDB}$ throughput configured for burst load) to avoid idle costs. **Lambda Configuration:** Scale down memory of Lambda functions to the minimum needed to save cost per invocation duration. |
| **6\. Disaster Recovery** | **Data:** All critical data (raw documents, final results) must reside in **S3** with cross-region replication enabled. **Code:** The entire infrastructure must be deployable to a secondary region via the IaC templates. |

