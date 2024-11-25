##################################################
# Lambda S3 Policies
##################################################

resource "aws_iam_role_policy_attachment" "lambda_policy_attachment" {
  role       = aws_iam_role.lambda_execution_role.name
  policy_arn = aws_iam_policy.lambda_s3_policy.arn
}

# IAM Role for Lambda
resource "aws_iam_role" "lambda_execution_role" {
  name = "dv_lambda_execution_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action    = "sts:AssumeRole",
        Effect    = "Allow",
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# Attach permissions to Lambda
resource "aws_iam_policy" "lambda_s3_policy" {
  name        = "dv_lambda_s3_policy"
  description = "Policy to allow Lambda to access S3"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action   = [
          "s3:ListBucket",
          "s3:GetObject"
        ],
        Effect   = "Allow",
        Resource = [
          aws_s3_bucket.landing_bucket.arn,
          "${aws_s3_bucket.landing_bucket.arn}/*",
          aws_s3_bucket.metadata_bucket.arn,
          "${aws_s3_bucket.metadata_bucket.arn}/*"
        ]
      }
    ]
  })
}