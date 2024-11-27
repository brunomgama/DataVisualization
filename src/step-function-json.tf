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
        "ItemsPath" : "$.checkFileResult.body",
        "Iterator" : {
          "StartAt" : "File Base Validation",
          "States" : {
            "Error Checker" : {
              "Choices" : [
                {
                  "Next" : "Fail",
                  "Not" : {
                    "NumericEquals" : 200,
                    "Variable" : "$.validationResult.statusCode"
                  }
                }
              ],
              "Default" : "Record Base Validation",
              "Type" : "Choice"
            },
            "Fail" : {
              "Cause" : "Validation of the file failed in File Base Validation.",
              "Error" : "ValidationFailed",
              "Type" : "Fail"
            },
            "File Base Validation" : {
              "Next" : "Error Checker",
              "Resource" : aws_lambda_function.fbv_lambda.arn,
              "ResultPath" : "$.validationResult",
              "Type" : "Task"
            },
            "Record Base Validation" : {
              "Next" : "Success",
              "Resource" : aws_lambda_function.rbv_lambda.arn,
              "ResultPath" : "$.recordValidationResult",
              "Type" : "Task"
            },
            "Success" : {
              "Type" : "Succeed"
            }
          }
        },
        "MaxConcurrency" : 1,
        "Type" : "Map",
        "Next" : "StartCrawler"
      },
      "StartCrawler" : {
        "Type" : "Task",
        "Parameters" : {
          "Name" : aws_glue_crawler.crawler.name
        },
        "Resource" : "arn:aws:states:::aws-sdk:glue:startCrawler",
        "Next" : "WaitForCrawler"
      },
      "WaitForCrawler" : {
        "Type" : "Wait",
        "Seconds" : 30,
        "Next" : "CheckCrawlerStatus"
      },
      "CheckCrawlerStatus" : {
        "Type" : "Task",
        "Parameters" : {
          "Name" : aws_glue_crawler.crawler.name
        },
        "Resource" : "arn:aws:states:::aws-sdk:glue:getCrawler",
        "ResultPath" : "$.crawlerStatus",
        "Next" : "IsCrawlerStopped"
      },
      "IsCrawlerStopped" : {
        "Type" : "Choice",
        "Choices" : [
          {
            "Variable" : "$.crawlerStatus.Crawler.State",
            "StringEquals" : "READY",
            "Next" : "NextState"
          }
        ],
        "Default" : "WaitForCrawler"
      },
      "NextState" : {
        "Type" : "Succeed"
      }
    }
  }
}