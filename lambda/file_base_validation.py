import os
import json
import csv
import boto3
from io import StringIO
from botocore.exceptions import ClientError

# Get bucket names from environment variables
landing_bucket_name = os.getenv('LANDING_BUCKET_NAME')
metadata_bucket_name = os.getenv('METADATA_BUCKET_NAME')

# Create S3 client
s3_client = boto3.client('s3')

def get_metadata(metadata_bucket, metadata_file):
    """Fetch metadata from the metadata bucket."""
    try:
        response = s3_client.get_object(Bucket=metadata_bucket, Key=metadata_file)
        metadata = json.loads(response['Body'].read().decode('utf-8'))
        return metadata
    except ClientError as e:
        print(f"Error fetching metadata from S3: {e}")
        return None

def validate_file_type(metadata, file_name, file_type):
    """Validate the file type against metadata."""
    file_type_metadata = metadata.get('file_validation').get('file_type')

    if file_type_metadata in file_type:
        return True
    elif 'application/octet-stream' in file_type and file_type_metadata in file_name:
        return True
    else:
        print(f"File type mismatch: expected {file_type_metadata}, got {file_type}")
        return False

def validate_csv_content(metadata, file_content):
    """Validate the content of the CSV file."""
    csv_content = csv.reader(StringIO(file_content), delimiter=metadata.get("separator"))
    rows = list(csv_content)

    # Validate the number of columns
    for i, row in enumerate(rows):
        if len(row) != metadata.get("column_quantity"):
            print(f"Row {i+1} has incorrect column count. Expected {metadata.get('column_quantity')}, got {len(row)}")
            return False
    return True

def process_file(record):
    """Process an individual file and validate its content."""
    file_name = record.get("file_name")
    metadata_file = record.get("metadata")

    # Fetch metadata
    metadata = get_metadata(metadata_bucket_name, metadata_file)

    if not metadata or record.get("status") != "exists":
        return {
            "file_name": file_name,
            "status": "error",
            "message": "Metadata fetch failed or file status is not 'exists'."
        }

    try:
        # Fetch the file content from S3
        response = s3_client.get_object(Bucket=landing_bucket_name, Key=file_name)
        file_content = response["Body"].read().decode("utf-8-sig")
        file_type = response.get('ContentType')

        # Perform validations
        is_type_valid = validate_file_type(metadata, file_name, file_type)
        is_content_valid = validate_csv_content(metadata.get("file_validation"), file_content)

        if is_type_valid and is_content_valid:
            return {
                "status": "exists",
                "file_name": file_name,
                "file_type": file_type,
                "metadata": metadata_file,
                "message": "File type and CSV content validated successfully."
            }
        else:
            return {
                "file_name": file_name,
                "status": "error",
                "message": "Validation failed. File type or content did not match expectations."
            }

    except ClientError as e:
        print(f"Error accessing file in S3: {e}")
        return {
            "file_name": file_name,
            "status": "error",
            "message": f"Error accessing file in S3: {e}"
        }
    except ValueError as ve:
        print(f"Validation error: {ve}")
        return {
            "file_name": file_name,
            "status": "error",
            "message": f"Validation error: {ve}"
        }
    except Exception as e:
        print(f"Unexpected error: {e}")
        return {
            "file_name": file_name,
            "status": "error",
            "message": f"Unexpected error: {e}"
        }

def lambda_handler(event, context):
    """Main Lambda handler."""
    # Parse the body to get the list of records
    results = []

    # Process each record
    result = process_file(event)
    results.append(result)

    return {
        "statusCode": 200,
        "body": json.dumps(results)
    }
