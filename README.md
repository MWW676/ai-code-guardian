# 🤖 CodeGuardian: Multi-Platform AI Code Reviewer

CodeGuardian is a production-ready, **Serverless AI** tool designed to automate code reviews for **GitHub** and **GitLab**. Built on **AWS**, it listens to Pull/Merge Request events, analyzes code diffs using **Google Gemini AI**, and posts insightful feedback directly back to your git platform.

## 🏗️ Architecture Design

This project follows the **Event-Driven Architecture (EDA)** pattern to ensure high scalability and decoupling:

1.  **Ingestion (Producer)**: A Lambda function validates incoming Webhooks from GitHub/GitLab (HMAC/Token verification).
2.  **Asynchronous Buffering (SQS)**: Decouples the ingestion layer from the analysis layer, preventing timeout issues and handling traffic spikes.
3.  **State Management (DynamoDB)**: Implements **Idempotency** by tracking `commit_sha`. It ensures each commit is analyzed only once, saving AI API quota.
4.  **Intelligence Engine (Gemini AI)**: Leverages Gemini Pro/Flash to perform multi-dimensional code scans (Maintainability, Security, Performance).
5.  **Persistence (S3)**: Archives every analysis report for future auditing and historical tracking.

## ✨ Key Features

* **🧩 Dual-Platform Support**: Seamlessly handles both GitHub and GitLab API "dialects" (e.g., `number` vs `iid`, `Pull Request` vs `Merge Request`).
* **🛡️ Robust Idempotency**: Powered by DynamoDB `ConditionExpression`, preventing duplicate comments on the same commit version.
* **🔒 Enterprise Security**: Zero hardcoded secrets. All API keys and Webhook secrets are fetched dynamically from **AWS SSM Parameter Store**.
* **📈 Smart Retries**: Integrated SQS visibility timeouts to handle transient AI API failures or rate limits.

## 🛠️ Tech Stack

* **Runtime**: Python 3.12
* **Cloud Infrastructure**: AWS (Lambda, SQS, DynamoDB, S3, SSM)
* **AI Model**: Google Gemini API
* **SDKs**: Boto3, Requests

## 🚀 Setup & Deployment

### 1. AWS SSM Configuration
Store the following parameters in **Parameter Store**:
* `/CodeGuardian/Gemini/ApiKey`
* `/CodeGuardian/GitHub/ApiKey`
* `/CodeGuardian/GitLab/ApiKey`
* `/CodeGuardian/GitLab/WebSecret`

### 2. DynamoDB Setup
Create a table named `CodeGuardian-Logs` with:
* **Partition Key**: `request_id` (String)

### 3. Lambda Deployment
Deploy `producer.py` and `consumer.py` as separate Lambda functions. Set up an SQS queue as the trigger for the consumer.

## 🎓 SAA Exam Context (Mapping)

This project is a perfect hands-on lab for **AWS Certified Solutions Architect - Associate** candidates:
* **Decoupling**: SQS for asynchronous processing.
* **Idempotency**: DynamoDB to handle duplicate message delivery.
* **Security**: SSM Parameter Store for secure secret management.