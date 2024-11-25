import os
import json
import csv
import boto3
import pandas as pd
from io import StringIO
from botocore.exceptions import ClientError

# Get bucket names from environment variables
landing_bucket_name = os.getenv('LANDING_BUCKET_NAME')
metadata_bucket_name = os.getenv('METADATA_BUCKET_NAME')
output_bucket_name = os.getenv('OUTPUT_BUCKET_NAME')

# Create S3 client
s3_client = boto3.client('s3')

def get_metadata(metadata_bucket, metadata_file):
    try:
        response = s3_client.get_object(Bucket=metadata_bucket, Key=metadata_file)
        metadata = json.loads(response['Body'].read().decode('utf-8'))
        return metadata
    except ClientError as e:
        print(f"Error fetching metadata from S3: {e}")
        return None

def validate_header(metadata, rows):
    if metadata.get("header") and rows[0] != metadata.get("column_names"):
        print(f"CSV header mismatch. {rows[0]} has incorrect column values.")

def validate_primary_keys(metadata, rows):
    """Validate for duplicate primary key values."""
    primary_keys = metadata.get("primary_key")

    if not primary_keys:
        print("No primary keys defined in metadata.")
        return False

    pk_indexes = [rows[0].index(pk) for pk in primary_keys if pk in rows[0]]

    if len(pk_indexes) != len(primary_keys):
        print("Primary key not found in CSV header.")
        return False

    seen_keys = set()
    duplicates = []

    for i, row in enumerate(rows[1:], start=2):
        pk_values = tuple(row[index] for index in pk_indexes)
        if pk_values in seen_keys:
            duplicates.append((i, pk_values))
        else:
            seen_keys.add(pk_values)

    if duplicates:
        if metadata.get("duplicates") == "fail":
            return False
        elif metadata.get("duplicates") == "warn":
            duplicate_details = "; ".join([f"Row {idx}: {values}" for idx, values in duplicates])
            print(f"Duplicate primary keys found: {duplicate_details}")
        elif metadata.get("duplicates") == "ignore":
            print("Duplicate primary keys found but ignoring.")
        else:
            print("Invalid 'duplicates' value in metadata.")
            return False

    return True

def convert_csv_to_parquet(rows, output_s3_key):
    """Convert CSV rows to Parquet and upload it to S3."""
    # Convert the CSV rows to a Pandas DataFrame
    df = pd.DataFrame(rows[1:], columns=rows[0])  # rows[0] is the header

    # Write DataFrame to Parquet (using pyarrow for parquet support)
    parquet_buffer = StringIO()
    df.to_parquet(parquet_buffer, engine='pyarrow')

    # Reset buffer position
    parquet_buffer.seek(0)

    # Upload the Parquet file to S3
    try:
        s3_client.put_object(
            Bucket=output_bucket_name,
            Key=output_s3_key,
            Body=parquet_buffer.getvalue()
        )
        print(f"Parquet file successfully uploaded to s3://{output_bucket_name}/{output_s3_key}")
    except ClientError as e:
        print(f"Error uploading Parquet file to S3: {e}")
        return False
    return True


def lambda_handler(event, context):
    status = "exists"
    file_name = "data_visualization/DataVisualization.csv"

    metadata = get_metadata(metadata_bucket_name, 'metadata.json')

    try:
        if metadata and status == "exists":
            response = s3_client.get_object(Bucket=landing_bucket_name, Key=file_name)
            file_content = response["Body"].read().decode("utf-8-sig")

            csv_content = csv.reader(StringIO(file_content), delimiter=metadata.get("file_validation").get("separator"))
            rows = list(csv_content)

            validate_header(metadata.get("record_validation"), rows)

            if not validate_primary_keys(metadata.get("record_validation"), rows):
                return {
                    "status": "error",
                    "message": "Primary key validation failed."
                }

            if convert_csv_to_parquet(rows, file_name.replace(".csv", ".parquet")):
                return {
                    "status": "success",
                    "message": "CSV file validated and converted to Parquet successfully."
                }
            else:
                return {
                    "status": "error",
                    "message": "Failed to upload Parquet file to S3."
                }
    except ClientError as e:
        print(f"Error accessing file in S3: {e}")
        return {
            "status": "error",
            "message": f"Error accessing file in S3: {e}"
        }
    except ValueError as ve:
        print(f"Validation error: {ve}")
        return {
            "status": "error",
            "message": f"Validation error: {ve}"
        }
    except Exception as e:
        print(f"Unexpected error: {e}")
        return {
            "status": "error",
            "message": f"Unexpected error: {e}"
        }
