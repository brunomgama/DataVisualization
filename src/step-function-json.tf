locals {
  step_function_map = {
    "Comment": "Step Function to check if a file exists in S3",
    "StartAt": "CheckFile",
    "States": {
      "CheckFile": {
        "Resource": "arn:aws:lambda:eu-west-1:${var.account_id}:function:dv_check_file_in_s3:$LATEST",
        "Type": "Task",
        "Next": "File Base Validation",
        "ResultPath": "$.checkFileResult"
      },
      "File Base Validation": {
        "Resource": "arn:aws:lambda:eu-west-1:${var.account_id}:function:dv_file_base_validation:$LATEST",
        "Type": "Task",
        "InputPath": "$.checkFileResult",
        "ResultPath": "$.checkFileResult"
        "Next": "Record Base Validation",
      }
      "Record Base Validation": {
        "Resource": "arn:aws:lambda:eu-west-1:${var.account_id}:function:dv_record_base_validation:$LATEST",
        "Type": "Task",
        "InputPath": "$.checkFileResult",
        "End": true
      }
    }
  }
}