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
        Action    = "sts:AssumeRole",
        Effect    = "Allow",
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
  policy      = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Sid     = "InvokeLambdaPermission"
        Effect  = "Allow"
        Action  = "lambda:InvokeFunction"
        Resource = [
          "arn:aws:lambda:eu-west-1:${var.account_id}:function:dv_check_file_in_s3:$LATEST",
          "arn:aws:lambda:eu-west-1:${var.account_id}:function:dv_file_base_validation:$LATEST",
          "arn:aws:lambda:eu-west-1:${var.account_id}:function:dv_record_base_validation:$LATEST"
          ],
      },
      {
        Sid     = "S3Permission"
        Effect  = "Allow"
        Action  = "s3:ListBucket"
        Resource = [
          "arn:aws:s3:::dv-landing-bucket",
          "arn:aws:s3:::dv-metadata-bucket"
        ]
      },
      {
        Sid     = "S3ObjectPermission"
        Effect  = "Allow"
        Action  = "s3:GetObject"
        Resource = [
          "arn:aws:s3:::dv-landing-bucket/*",
          "arn:aws:s3:::dv-metadata-bucket/*"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "step_function_policy_attachment" {
  policy_arn = aws_iam_policy.step_function_policy.arn
  role       = aws_iam_role.step_function_role.name
}
