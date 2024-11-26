locals {
  step_function_map = {
    "Comment" : "Step Function to check if a file exists in S3 and validate files",
    "StartAt" : "CheckFile",
    "States" : {
      "CheckFile" : {
        "Next" : "File Treatment Mapper",
        "Resource" : aws_lambda_function.check_file_lambda.arn,
        "ResultPath" : "$.checkFileResult",
        "Type" : "Task"
      },
      "File Treatment Mapper" : {
        "Type" : "Map",
        "ItemsPath" : "$.checkFileResult.body",
        "Iterator" : {
          "StartAt" : "File Base Validation",
          "States" : {
            "File Base Validation" : {
              "Resource" : aws_lambda_function.fbv_lambda.arn,
              "ResultPath" : "$.validationResult",
              "Type" : "Task",
              "Next" : "Choice"
            },
            "Choice" : {
              "Type" : "Choice",
              "Choices" : [
                {
                  "Not" : {
                    "Variable" : "$.validationResult.statusCode",
                    "NumericEquals" : 200
                  },
                  "Next" : "Fail"
                }
              ],
              "Default" : "Record Base Validation"
            },
            "Record Base Validation" : {
              "Resource" : aws_lambda_function.rbv_lambda.arn,
              "ResultPath" : "$.recordValidationResult",
              "Type" : "Task",
              "Next" : "Success"
            },
            "Fail" : {
              "Type" : "Fail",
              "Error" : "ValidationFailed",
              "Cause" : "Validation of the file failed in File Base Validation."
            },
            "Success" : {
              "Type" : "Succeed"
            }
          }
        },
        "MaxConcurrency" : 1,
        "End" : true
      }
    }
  }
}