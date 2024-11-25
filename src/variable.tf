variable "user_arn" {
  description = "User ARN"
  type        = string
}

variable "bucket_tags" {
  description = "Tags to assign to the bucket"
  type        = map(string)
  default     = {}
}

variable "policy_actions" {
  description = "Actions to allow in the bucket policy"
  type        = list(string)
  default     = ["s3:GetObject"]
}

variable "account_id" {
  description = "AWS Account ID"
  type        = string
}