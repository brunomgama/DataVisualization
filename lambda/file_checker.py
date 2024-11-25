import os
import json
import boto3
from botocore.exceptions import ClientError

# Get bucket names from environment variables
landing_bucket_name = os.getenv('LANDING_BUCKET_NAME')
metadata_bucket_name = os.getenv('METADATA_BUCKET_NAME')

# Create S3 client
s3_client = boto3.client('s3')

def check_file_exists_in_bucket(bucket_name, file_path, file_name):
    try:
        source_file = (file_path + "/" + file_name).replace("*", "")

        response = s3_client.list_objects_v2(Bucket=bucket_name)
        files = response.get("Contents")

        for file in files:
            filename = file['Key']

            if source_file in filename:
                return filename
        return ""
    except ClientError as e:
        if e.response['Error']['Code'] == '404':
            return ""
        else:
            raise

def get_metadata(metadata_bucket, metadata_file):
    try:
        response = s3_client.get_object(Bucket=metadata_bucket, Key=metadata_file)

        metadata = json.loads(response['Body'].read().decode('utf-8'))
        return metadata
    except ClientError as e:
        print(f"Error fetching metadata from S3: {e}")
        return None

def lambda_handler(event, context):
    metadata = get_metadata(metadata_bucket_name, 'metadata.json')

    if metadata:
        file_path = metadata.get('file_path')
        file_name = metadata.get('file_pattern')

        if file_path and file_name:
            file_exists = check_file_exists_in_bucket(landing_bucket_name, file_path, file_name)
            if file_exists:
                print(f"The file '{file_name}' exists in the landing bucket '{landing_bucket_name}'.")
                return {
                    "status": "exists",
                    "file_name": file_exists
                }
            else:
                print(f"The file '{file_name}' does not exist in the landing bucket '{landing_bucket_name}'.")
                return {
                    "status": "not_exists",
                    "file_name": (file_path + "/" + file_name).replace("*", "")
                }
        else:
            print("The 'file_name' key was not found in the metadata.")
            return {
                "status": "error",
                "message": "file_path or file_name not found in metadata"
            }
    else:
        print("Failed to fetch metadata.")
        return {
            "status": "error",
            "message": "Failed to fetch metadata"
        }