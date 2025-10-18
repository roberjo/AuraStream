AuraStream:   API Specification Document (API Spec)

| Section | Key Content to Include |
| :---- | :---- |
| **1\. Base URL** | https://\[your-api-id\].execute-api.\[region\].amazonaws.com/v1 |
| **2\. Endpoint: Synchronous Analysis** | **Method:** POST **Path:** /analyze/sync **Authentication:** Required (API Key/IAM) **Purpose:** Real-time sentiment analysis for single, short text inputs. |
| **3\. Request Body (Synchronous)** | **Format:** $\\text{application/json}$ $\\text{\\{"text": "I am so happy with this new solution."\\}}$ |
| **4\. Success Response (Synchronous)** | **Status:** 200 OK **Body:** $\\text{\\{"sentiment": "POSITIVE", "score": 0.925, "language\\\_code": "en"\\}}$ *(Direct result from Comprehend)* |
| **5\. Endpoint: Asynchronous Analysis** | **Method:** POST **Path:** /analyze/async **Authentication:** Required (API Key/IAM) **Purpose:** Initiate a batch processing job for large or numerous requests. |
| **6\. Request Body (Asynchronous)** | **Format:** $\\text{application/json}$ $\\text{\\{"text": "Please analyze this large document...", "source\\\_id": "user\\\_123\\\_batch\\\_A" \\}}$ |
| **7\. Success Response (Asynchronous)** | **Status:** 202 Accepted **Body:** $\\text{\\{"message": "Analysis initiated. Check status using the job ID.", "job\\\_id": "b78b0d2d-d55a-49a7-8f5a-39c59520c083" \\}}$ |
| **8\. Endpoint: Check Status** | **Method:** GET **Path:** /status/{job\\\_id} **Authentication:** Required (API Key/IAM) **Purpose:** Retrieve the analysis result using the job ID. |
| **9\. Status Response Example** | **Status (Job Incomplete):** 200 OK $\\text{{"status": "PENDING" |
| **10\. Error Responses** | **400 Bad Request:** Missing/malformed $\\text{text}$ body. **504 Gateway Timeout:** Used *only* for synchronous calls that exceed the 29-second limit. |

