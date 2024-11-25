locals {
  landing_bucket = "dv-landing-bucket"
  metadata_bucket = "dv-metadata-bucket"
}

##################################################
# LANDING Bucket
##################################################
resource "aws_s3_bucket" "landing_bucket" {
  bucket = local.landing_bucket
  tags = var.bucket_tags
}

resource "aws_s3_bucket_policy" "landing_bucket_policy" {
  bucket = aws_s3_bucket.landing_bucket.id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Sid       = "AllowSpecificAccess",
        Effect    = "Allow",
        Principal = {
          AWS = var.user_arn
        },
        Action    = var.policy_actions,
        Resource  = "${aws_s3_bucket.landing_bucket.arn}/*"
      }
    ]
  })
}

##################################################
# METADATA Bucket
##################################################
resource "aws_s3_bucket" "metadata_bucket" {
  bucket = local.metadata_bucket
  tags = var.bucket_tags
}

resource "aws_s3_bucket_policy" "metadata_bucket_policy" {
  bucket = aws_s3_bucket.metadata_bucket.id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Sid       = "AllowSpecificAccess",
        Effect    = "Allow",
        Principal = {
          AWS = var.user_arn
        },
        Action    = var.policy_actions,
        Resource  = "${aws_s3_bucket.metadata_bucket.arn}/*"
      }
    ]
  })
}