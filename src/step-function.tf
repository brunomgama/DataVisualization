##################################################
# Step Function
##################################################
resource "aws_sfn_state_machine" "file_check_step_function" {
  name     = "DataVisualizationStepFunction"
  role_arn = aws_iam_role.step_function_role.arn

  definition = jsonencode(local.step_function_map)
}

resource "aws_iam_role" "step_function_role" {
  name = "step_function_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = "sts:AssumeRole",
        Effect = "Allow",
        Principal = {
          Service = "states.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_policy" "step_function_policy" {
  name        = "step_function_policy"
  description = "Policy to allow Step Function to invoke Lambda and interact with S3"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Sid    = "InvokeLambdaPermission"
        Effect = "Allow"
        Action = "lambda:InvokeFunction"
        Resource = [
          aws_lambda_function.check_file_lambda.arn,
          aws_lambda_function.fbv_lambda.arn,
          aws_lambda_function.rbv_lambda.arn
        ],
      },
      {
        Sid    = "S3Permission"
        Effect = "Allow"
        Action = "s3:ListBucket"
        Resource = [
          aws_s3_bucket.landing_bucket.arn,
          aws_s3_bucket.metadata_bucket.arn,
          aws_s3_bucket.main_bucket.arn
        ]
      },
      {
        Sid    = "S3ObjectPermission"
        Effect = "Allow"
        Action = "s3:GetObject"
        Resource = [
          "${aws_s3_bucket.landing_bucket.arn}/*",
          "${aws_s3_bucket.metadata_bucket.arn}/*",
          "${aws_s3_bucket.main_bucket.arn}/*"
        ]
      },
      {
        Sid    = "GlueCrawlerPermission"
        Effect = "Allow"
        Action = [
          "glue:StartCrawler",
          "glue:GetCrawler",
        ],
        Resource = [
          aws_glue_crawler.crawler.arn
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "step_function_policy_attachment" {
  policy_arn = aws_iam_policy.step_function_policy.arn
  role       = aws_iam_role.step_function_role.name
}
