AuraStream System Design Document (SDD)

| Section | Key Content to Include |
| :---- | :---- |
| **1\. Overview & Goals** | **Primary Goal:** To provide a single, highly scalable, and cost-optimized API endpoint for real-time and bulk sentiment analysis of customer feedback data. **Business Value:** Instantaneous feedback for chat/live agents and overnight batch analysis for product teams. |
| **2\. High-Level Architecture** | **Diagram:** Must show two distinct paths connected by the API Gateway front-end: 1\. **Synchronous Path** (Real-Time) 2\. **Asynchronous Path** (Batch/Large Payload) **Core Services:** AWS Lambda, Amazon API Gateway, Amazon Comprehend, Amazon S3, AWS Step Functions, Amazon DynamoDB, Amazon SQS. |
| **3\. Technical Decisions** | **Platform:** AWS Serverless First. **Language:** Python (for robust ML library support and faster Lambda cold starts). **IaC:** AWS Serverless Application Model (SAM) or Terraform. |
| **4\. Synchronous (Real-Time) Path** | **Purpose:** Low-latency requests ($\\leq$ 1 second) for short text (e.g., chat messages, titles). **Flow:** API Gateway $\\rightarrow$ Lambda (Direct Invocation) $\\rightarrow$ Comprehend (DetectSentiment) $\\rightarrow$ Response. **Resilience:** Configure Lambda **OnFailure Destination** (e.g., an SQS Dead Letter Queue) to capture failed events for re-processing. |
| **5\. Asynchronous (Batch/Bulk) Path** | **Purpose:** High-volume or large payloads (e.g., documents, CSV files, large log batches). **Flow:** API Gateway $\\rightarrow$ Lambda (writes $\\text{JSON}$ body/payload to S3) $\\rightarrow$ S3 Event Trigger $\\rightarrow$ **AWS Step Functions** $\\rightarrow$ Comprehend (Batch APIs) $\\rightarrow$ DynamoDB (Result Storage). **Tracking:** The initial API response must return a unique $\\text{job\\\_ID}$ for the client to track the result. |
| **6\. Data Model** | **Input Payload:** $\\text{{"text": "string (the content to analyze)", "mode": "SYNC" |
| **7\. Security & Compliance** | **API Gateway:** Require IAM Authorization or API Key authentication. **Lambda IAM:** Strict *Least Privilege* policies (e.g., Lambda Role can *only* call $\\text{comprehend:DetectSentiment}$ and write to the specified $\\text{DynamoDB}$ table). |

