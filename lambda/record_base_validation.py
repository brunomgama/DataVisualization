import os
import json
import csv
import re
import boto3
import pandas as pd
from io import StringIO, BytesIO
from botocore.exceptions import ClientError

landing_bucket_name = os.getenv('LANDING_BUCKET_NAME')
metadata_bucket_name = os.getenv('METADATA_BUCKET_NAME')
output_bucket_name = os.getenv('OUTPUT_BUCKET_NAME')

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
        policy = metadata.get("duplicates")
        if policy == "fail":
            return False
        elif policy == "warn":
            duplicate_details = "; ".join([f"Row {idx}: {values}" for idx, values in duplicates])
            print(f"Duplicate primary keys found: {duplicate_details}")
        elif policy == "ignore" or policy == "remove":
            print(f"Founded duplicated primary keys but policy is {policy}")
        else:
            print("Invalid 'duplicates' value in metadata.")
            return False

    return True

def convert_csv_to_parquet(rows, output_s3_key, output_bucket_name, metadata, remove_duplicates):
    primary_keys = metadata.get("record_validation").get("primary_key")

    print("PK", primary_keys)
    columns = rows[0]
    data = rows[1:]

    df = pd.DataFrame(data, columns=columns)

    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].apply(lambda x: re.sub('[^a-zA-Z0-9 ]', '', str(x)))

    if remove_duplicates:
        df = df.drop_duplicates(subset=primary_keys, keep='first')

    df = check_read_schema(metadata, df)

    parquet_buffer = BytesIO()

    try:
        df.to_parquet(parquet_buffer, engine='pyarrow')
        parquet_buffer.seek(0)
    except Exception as e:
        print(f"Error writing DataFrame to Parquet: {e}")
        return False

    try:
        print("Parquet has been done")
        s3_client.put_object(
            Bucket=output_bucket_name,
            Key="parquet/"+output_s3_key,
            Body=parquet_buffer.getvalue()
        )
        print(f"Parquet file successfully uploaded to s3://{output_bucket_name}/{output_s3_key}")
    except ClientError as e:
        print(f"Error uploading Parquet file to S3: {e}")
        return False

    return True

def check_read_schema(metadata, df):
    fields = metadata.get("read_schema", {}).get("fields", [])

    for field in fields:
        column_name = field.get("name")
        column_type = field.get("type")
        column_metadata = field.get("metadata", {})

        if column_metadata.get("sensitive_information", False) and column_name in df.columns:
            print(f"Removing sensitive column: {column_name}")
            df = df.drop(columns=[column_name])
            continue

        if "values" in column_metadata and column_name in df.columns:
            value_mapping = column_metadata["values"][0]
            df[column_name] = df[column_name].map(value_mapping).fillna(df[column_name])

        if column_type == "monetary" and column_name in df.columns:
            df[column_name] = df[column_name].str.replace("EUR", "").str.replace(",", "").astype(float)

    return df

def lambda_handler(event, context):
    status = event.get("status")
    file_name = event.get("file_name")

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

            policy = metadata.get("record_validation").get("duplicates") == "remove"
            print(f"Policy: {policy}")

            if convert_csv_to_parquet(rows, file_name.replace(".csv", ".parquet"), landing_bucket_name, metadata, policy):
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
