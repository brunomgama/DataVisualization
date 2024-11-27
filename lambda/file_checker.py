import os
import json
import boto3
from botocore.exceptions import ClientError

# Get bucket names from environment variables
landing_bucket_name = os.getenv('LANDING_BUCKET_NAME')
metadata_bucket_name = os.getenv('METADATA_BUCKET_NAME')

# Create S3 client
s3_client = boto3.client('s3')

def list_folders_in_bucket(bucket_name):
    """List top-level folders in the S3 bucket."""
    try:
        response = s3_client.list_objects_v2(Bucket=bucket_name, Delimiter='/')
        return [prefix['Prefix'] for prefix in response.get('CommonPrefixes', [])]
    except ClientError as e:
        print(f"Error listing folders in bucket {bucket_name}: {e}")
        return []

def get_metadata(metadata_bucket, metadata_file):
    """Fetch and parse metadata JSON file."""
    try:
        response = s3_client.get_object(Bucket=metadata_bucket, Key=metadata_file)
        metadata = json.loads(response['Body'].read().decode('utf-8'))
        return metadata
    except ClientError as e:
        print(f"Error fetching metadata from S3: {e}")
        return None

def get_matching_files(bucket_name, file_path, file_pattern):
    """Retrieve all matching files in the S3 bucket based on the file pattern."""
    try:
        response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=file_path)
        files = response.get("Contents", [])
        matching_files = [file['Key'] for file in files if file_pattern in file['Key']]
        return matching_files
    except ClientError as e:
        print(f"Error listing files in bucket {bucket_name}: {e}")
        return []

def lambda_handler(event, context):
    """Main Lambda handler."""
    folders = list_folders_in_bucket(metadata_bucket_name)
    result = []

    for folder in folders:
        metadata_file = folder + 'metadata.json'
        metadata = get_metadata(metadata_bucket_name, metadata_file)

        if metadata:
            file_path = metadata.get('file_path')
            file_pattern = metadata.get('file_pattern')

            if file_path and file_pattern:
                matching_files = get_matching_files(landing_bucket_name, file_path, file_pattern)
                for file_name in matching_files:
                    result.append({
                        "status": "exists",
                        "metadata": metadata_file,
                        "file_name": file_name
                    })
            else:
                print(f"Metadata for folder '{folder}' is missing 'file_path' or 'file_pattern'.")
        else:
            print(f"Metadata file '{metadata_file}' could not be retrieved.")

    return {
        "statusCode": 200,
        "body": result
    }
