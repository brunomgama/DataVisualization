##################################################
# Check file existence Lambda Function
##################################################
resource "aws_lambda_function" "check_file_lambda" {
  filename      = "${path.module}/../lambda/file_checker.zip"
  function_name = "dv_check_file_in_s3"
  role          = aws_iam_role.lambda_execution_role.arn
  handler       = "file_checker.lambda_handler"
  runtime       = "python3.9"
  timeout       = 900

  environment {
    variables = {
      LANDING_BUCKET_NAME  = aws_s3_bucket.landing_bucket.bucket
      METADATA_BUCKET_NAME = aws_s3_bucket.metadata_bucket.bucket
    }
  }
}

##################################################
# File Base Validation Lambda Function
##################################################
resource "aws_lambda_function" "fbv_lambda" {
  filename      = "${path.module}/../lambda/file_base_validation.zip"
  function_name = "dv_file_base_validation"
  role          = aws_iam_role.lambda_execution_role.arn
  handler       = "file_base_validation.lambda_handler"
  runtime       = "python3.9"
  timeout       = 900

  environment {
    variables = {
      LANDING_BUCKET_NAME  = aws_s3_bucket.landing_bucket.bucket
      METADATA_BUCKET_NAME = aws_s3_bucket.metadata_bucket.bucket
    }
  }
}

##################################################
# Record Base Validation Lambda Function
##################################################
resource "aws_lambda_function" "rbv_lambda" {
  filename      = "${path.module}/../lambda/record_base_validation.zip"
  function_name = "dv_record_base_validation"
  role          = aws_iam_role.lambda_execution_role.arn
  handler       = "record_base_validation.lambda_handler"
  runtime       = "python3.9"
  timeout       = 900

  layers = ["arn:aws:lambda:eu-west-1:336392948345:layer:AWSSDKPandas-Python39:26"]

  environment {
    variables = {
      LANDING_BUCKET_NAME  = aws_s3_bucket.landing_bucket.bucket
      METADATA_BUCKET_NAME = aws_s3_bucket.metadata_bucket.bucket
      OUTPUT_BUCKET_NAME   = aws_s3_bucket.main_bucket.bucket
    }
  }
}

