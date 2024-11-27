import os
import json
import csv
import re
import boto3
import pandas as pd
from io import StringIO, BytesIO
from botocore.exceptions import ClientError

# S3 bucket names
landing_bucket_name = os.getenv('LANDING_BUCKET_NAME')
metadata_bucket_name = os.getenv('METADATA_BUCKET_NAME')
output_bucket_name = os.getenv('OUTPUT_BUCKET_NAME')

# S3 client
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

def validate_header(metadata, rows):
    """Validate CSV header."""
    if metadata.get("header") and rows[0] != metadata.get("column_names"):
        print(f"CSV header mismatch. {rows[0]} has incorrect column values.")

def validate_primary_keys(metadata, rows):
    """Validate primary keys for duplicates."""
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
            print(f"Found duplicated primary keys but policy is {policy}")
        else:
            print("Invalid 'duplicates' value in metadata.")
            return False

    return True

def convert_csv_to_parquet(rows, output_s3_key, output_bucket_name, metadata, remove_duplicates):
    """Convert CSV rows to Parquet and upload to S3."""
    print(f"Converting CSV to Parquet: {output_s3_key}")
    primary_keys = metadata.get("record_validation").get("primary_key")
    columns = rows[0]
    data = rows[1:]

    df = pd.DataFrame(data, columns=columns)

    # Clean non-numeric columns (remove unwanted characters)
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].apply(lambda x: re.sub('[^a-zA-Z0-9 ,.-]', '', str(x)))

    # Drop duplicates if specified
    if remove_duplicates:
        df = df.drop_duplicates(subset=primary_keys, keep='first')

    # Apply read schema rules
    df = check_read_schema(metadata, df)

    parquet_buffer = BytesIO()

    try:
        print("check read rules done")
        df.to_parquet(parquet_buffer, engine='pyarrow')
        parquet_buffer.seek(0)
    except Exception as e:
        print(f"Error writing DataFrame to Parquet: {e}")
        return False

    try:
        s3_client.put_object(
            Bucket=output_bucket_name,
            Key=output_s3_key,
            Body=parquet_buffer.getvalue()
        )
        print(f"Parquet file successfully uploaded to s3://{output_bucket_name}/parquet/{output_s3_key}")
    except ClientError as e:
        print(f"Error uploading Parquet file to S3: {e}")
        return False

    return True

def check_read_schema(metadata, df):
    """Apply read schema rules from metadata to the DataFrame."""
    fields = metadata.get("read_schema", {}).get("fields", [])

    for field in fields:
        column_name = field.get("name")
        column_type = field.get("type")
        column_metadata = field.get("metadata", {})

        # Remove sensitive information columns
        if column_metadata.get("sensitive_information", False) and column_name in df.columns:
            print(f"Removing sensitive column: {column_name}")
            df = df.drop(columns=[column_name])
            continue

        # Apply value mappings if specified
        if "values" in column_metadata and column_name in df.columns:
            value_mapping = column_metadata["values"][0]
            df[column_name] = df[column_name].map(value_mapping).fillna(df[column_name])

        # Handle 'double' type (replace commas with dots and convert to float)
        if column_type == "double" and column_name in df.columns:
            print(f"Processing numeric column (double): {column_name}")
            df[column_name] = df[column_name].str.replace(",", ".").astype(float)

        # Handle 'monetary' type (remove currency symbol and convert to float)
        if column_type == "monetary" and column_name in df.columns:
            print(f"Processing monetary column: {column_name}")
            df[column_name] = df[column_name].str.replace("EUR", "").str.replace(",", "").astype(float)

        # Handle boolean values transformations
        if column_type == "string" and column_metadata.get("transform_values") and column_name in df.columns:
            for transform in column_metadata["transform_values"]:
                df[column_name] = df[column_name].map(transform).fillna(df[column_name])

    return df

def lambda_handler(event, context):
    """Main Lambda handler."""
    try:
        records = json.loads(event.get("validationResult").get("body", "[]"))

        results = []

        for record in records:
            status = record.get("status")
            file_name = record.get("file_name")
            metadata_file = record.get("metadata")

            metadata = get_metadata(metadata_bucket_name, metadata_file)

            if not metadata:
                results.append({
                    "status": "error",
                    "file_name": file_name,
                    "message": f"Metadata fetch failed for {metadata_file}."
                })
                continue

            if status != "exists":
                results.append({
                    "status": "error",
                    "file_name": file_name,
                    "message": "File does not exist."
                })
                continue

            try:
                # Fetch the file content from S3
                response = s3_client.get_object(Bucket=landing_bucket_name, Key=file_name)
                file_content = response["Body"].read().decode("utf-8-sig")
                file_type = response.get('ContentType')

                # Parse the CSV content
                csv_content = csv.reader(StringIO(file_content), delimiter=metadata.get("file_validation", {}).get("separator", ";"))
                rows = list(csv_content)

                # Perform validations
                validate_header(metadata.get("record_validation"), rows)

                if not validate_primary_keys(metadata.get("record_validation"), rows):
                    results.append({
                        "status": "error",
                        "file_name": file_name,
                        "message": "Primary key validation failed."
                    })
                    continue

                # Handle duplicate policies
                remove_duplicates = metadata.get("record_validation", {}).get("duplicates") == "remove"

                # Convert to Parquet and upload to S3
                if convert_csv_to_parquet(
                        rows,
                        file_name.replace(".csv", ".parquet"),
                        output_bucket_name,
                        metadata,
                        remove_duplicates
                ):
                    results.append({
                        "status": "success",
                        "file_name": file_name,
                        "file_type": file_type,
                        "message": "CSV file validated and converted to Parquet successfully."
                    })
                else:
                    results.append({
                        "status": "error",
                        "file_name": file_name,
                        "message": "Failed to upload Parquet file to S3."
                    })

            except ClientError as e:
                results.append({
                    "status": "error",
                    "file_name": file_name,
                    "message": f"Error accessing file in S3: {e}"
                })
            except ValueError as ve:
                results.append({
                    "status": "error",
                    "file_name": file_name,
                    "message": f"Validation error: {ve}"
                })
            except Exception as e:
                results.append({
                    "status": "error",
                    "file_name": file_name,
                    "message": f"Unexpected error: {e}"
                })

        return {
            "statusCode": 200,
            "body": json.dumps(results)
        }

    except Exception as e:
        print(f"Unexpected error in Lambda handler: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({
                "status": "error",
                "message": f"Unexpected error: {e}"
            })
        }
