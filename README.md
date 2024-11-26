# Data Visualization and ETL Automation via Terraform

Welcome to the **Data Visualization and ETL Automation** project! This repository provides a Terraform-based framework to create a metadata-driven ETL (Extract, Transform, Load) pipeline, enabling fully automated data ingestion, validation, and transformation processes. By defining metadata, users can configure a scalable and reusable pipeline with minimal effort.

Tested on:

![AWS](https://img.shields.io/badge/AWS-%23FF9900.svg?style=for-the-badge&logo=amazon-aws&logoColor=white)
![Postgres](https://img.shields.io/badge/postgres-%23316192.svg?style=for-the-badge&logo=postgresql&logoColor=white)
![Terraform](https://img.shields.io/badge/Terraform-%235835CC.svg?style=for-the-badge&logo=terraform&logoColor=white)
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)

---

## 🚀 Project Overview

This project is designed to allow users to implement an automated ETL pipeline that performs the following tasks:

- **File Existence Validation**: Check if files exist in the configured source location.

- **File Type and Content Validation**: Ensure files meet the expected structure, type, and data integrity requirements.
 
- **Data Transformation**: Convert validated CSV data into Parquet format with support for schema enforcement and handling sensitive information.

The infrastructure uses AWS services such as Lambda, S3, and Step Functions to orchestrate the ETL pipeline.

---

## 🛠 Features

- **Metadata-Driven Configuration**: Users can define pipeline behavior through JSON metadata files.

- **Automated File Validation**:
    - Checks file existence and type.
    - Validates CSV header, column count, and data content.
    - Handles duplicate records based on configurable policies.

- **Data Transformation**: Converts validated CSV files into optimized Parquet format, with optional column transformations.

- **AWS-Powered Architecture**: Uses serverless services (Lambda, S3, Step Functions) for scalability and cost efficiency.

- **Dynamic Schema Enforcement**: Supports schema validation and transformation rules.

---

## 🌟 Architecture

The pipeline consists of the following AWS resources:

- **Lambda Functions**:
    - **`file_checker`**: Validates file existence in S3.
    - **`file_base_validation`**: Checks the file type and validates its content.
    - **`record_base_validation`**: Enforces record-level validations and converts CSV files to Parquet.
- **S3 Buckets**:
    - **Landing Bucket**: Stores incoming files.
    - **Metadata Bucket**: Stores the metadata configuration file.
- **Step Functions**:
    - Orchestrates the ETL workflow by invoking Lambda functions in sequence.

---

## 📂 Repository Structure

```plaintext
├── main.tf                       # Terraform configuration for AWS resources
├── variables.tf                  # Variables for Terraform setup
├── outputs.tf                    # Outputs for Terraform-managed resources
├── lambda/
│   ├── file_checker.py           # Validates file existence in S3
│   ├── file_base_validation.py   # Validates file type and basic structure
│   ├── record_base_validation.py # Validates record-level rules and converts CSV to Parquet
│   ├── requirements.txt          # Python dependencies for Lambda functions
├── metadata/
│   ├── metadata.json             # Metadata configuration for the ETL pipeline
├── src/
│   ├── lambda.tf                 # Lambda function setup
│   ├── lambda_s3_policies.tf     # IAM policies for Lambda functions
│   ├── s3.tf                     # S3 bucket setup
│   ├── s3_upload.tf              # S3 bucket upload setup
│   ├── step_functions.tf         # Step Functions setup
│   ├── step_functions_policy.tf  # IAM policy for Step Functions
│   ├── variables.tf              # Variables for Terraform setup
└── README.md                  # Project documentation (You Are Here!)
```

## 📜 Metadata Configuration

The **metadata.json** file defines the rules for the ETL process. Below is an overview of its structure:

### Key Sections:

- **`file_path`**: Path of the source files in the S3 landing bucket.  
- **`file_pattern`**: Pattern to identify target files.  
- **`file_validation`**:
  - **`file_type`**: Expected file type (e.g., `csv`).  
  - **`separator`**: CSV delimiter (e.g., `;`, `,`).  
  - **`column_quantity`**: Expected number of columns.  
- **`record_validation`**:
  - **`header`**: Whether the CSV file includes a header row.  
  - **`duplicates`**: Policy for handling duplicate records (`fail`, `warn`, `ignore`, `remove`).  
  - **`primary_key`**: Columns to check for uniqueness.  
  - **`column_names`**: Expected column headers.  
- **`read_schema`**:
  - Defines the schema for columns, including data types, nullable constraints, and transformations.
- **`metadata`**:
  - Metadata for the pipeline, such as sensitive information and schema rules. 
  - This section is optional and can be customized based on requirements.
  
### Schema Fields:
Converts Monetary data types to Parquet format.
```json
"metadata": {
  "currency": "EUR"
}
```
Obscures complete column in parquet.
```json
"metadata": {
  "sensitive_information": true
}
``` 
Converts column values to boolean.
```json
"metadata": {
  "transform_values": [
    {
      "Ja": true,
      "Nein": false
    }]
}
```

### Example:
```json
{
  "file_path": "data_visualization",
  "file_pattern": "DataVisualization",
  "file_validation": {
    "file_type": "csv",
    "separator": ";",
    "column_quantity": 5
  },
  "record_validation": {
    "header": true,
    "duplicates": "remove",
    "primary_key": ["Typ", "Produktname"],
    "column_names": [
      "Typ",
      "Produktname",
      "Preis",
      "Kapazität",
      "Rabattfähig"
    ]
  },
  "read_schema": {
    "fields": [
      {
        "name": "Typ",
        "type": "string"
      },
      {
        "name": "Preis",
        "type": "monetary",
        "metadata": {
          "sensitive_information": true
        }
      }
    ]
  }
}
```

## 🛠️ Lambda Functions

### **File Checker**
- **Script**: `file_checker.py`
- **Purpose**: Checks if the file exists in the landing bucket based on metadata configuration.
- **Key Methods**:
  - `check_file_exists_in_bucket(bucket_name, file_path, file_name)`
- **Triggered by**: Step Function to ensure the presence of required files before further processing.

### **File Base Validation**
- **Script**: `file_base_validation.py`
- **Purpose**: Validates the file type and basic structure (e.g., separator and column count). Ensures the file adheres to the defined format.
- **Key Methods**:
  - `validate_file_type(metadata, file_name, file_type)`
  - `validate_csv_content(metadata, file_content)`
- **Triggered by**: Step Function after file existence check.

### **Record Base Validation**
- **Script**: `record_base_validation.py`
- **Purpose**: Validates record-level rules such as primary key integrity, duplicate handling, and converts valid CSV files to Parquet format.
- **Key Methods**:
  - `validate_primary_keys(metadata, rows)`
  - `convert_csv_to_parquet(rows, output_s3_key, metadata, remove_duplicates)`
- **Triggered by**: Step Function after file and format validation.

---

## 🔄 Step Function Workflow

The ETL process is orchestrated using AWS Step Functions, which manage the flow of Lambda invocations based on the metadata configuration.

### Workflow Steps:

- **File Existence Check**:  
   The `file_checker.py` Lambda is triggered first to verify if the file exists in the landing bucket based on the `file_path` and `file_pattern` defined in the metadata.

- **File Validation**:  
   Once the file is confirmed to exist, the `file_base_validation.py` Lambda is invoked to check if the file is of the correct type (e.g., CSV) and if it adheres to the format (e.g., correct column count, separator).

- **Record Validation and Transformation**:  
   If the file passes basic validation, the `record_base_validation.py` Lambda performs the following:
  - Validates primary keys and duplicates based on the `record_validation` section of the metadata.
  - Converts the CSV file into a Parquet file using the defined schema and removes duplicates if the metadata dictates so.

- **File Output**:  
   The final Parquet file is then uploaded to the designated output bucket.

---

## ⚙️ Configuration

### AWS Services Used:

- **AWS Lambda**: For running the validation and transformation scripts.
- **Amazon S3**: For storing the landing files, metadata, and processed output (Parquet files).
- **AWS Step Functions**: To manage the flow between the different Lambda functions.

### Environment Variables:

The Lambda functions rely on several environment variables that should be set when deploying:

- `LANDING_BUCKET_NAME`: The name of the S3 bucket where incoming files are stored.
- `METADATA_BUCKET_NAME`: The name of the S3 bucket where metadata files are stored.
- `OUTPUT_BUCKET_NAME`: The name of the S3 bucket where the transformed Parquet files will be stored.

---

## 🔐 Security

To ensure secure access to the S3 buckets, the Lambda functions are granted minimal required permissions via AWS IAM roles. Additionally, sensitive data handling is governed by metadata settings, including sensitive field management (e.g., `Preis` marked as sensitive).

---

## 📦 Requirements

The Lambda functions use the following Python packages, which should be included in the `requirements.txt` file for deployment:

- `boto3`: AWS SDK for Python (used to interact with S3).
- `pandas`: For data manipulation and CSV/Parquet conversions.
- `pyarrow`: For reading and writing Parquet files.

Example `requirements.txt`:
