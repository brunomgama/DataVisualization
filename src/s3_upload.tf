############################################
# Data Visualization
############################################
resource "aws_s3_object" "metadata_data_visualization" {
  bucket                 = aws_s3_bucket.metadata_bucket.id
  key                    = "data_visualization/metadata.json"
  source                 = "${path.module}/../metadata/data_visualization/metadata.json"

  depends_on = [
    aws_s3_bucket.metadata_bucket
  ]
}

resource "aws_s3_object" "data_visualization" {
  bucket                 = aws_s3_bucket.landing_bucket.id
  key                    = "data_visualization/DataVisualization.csv"
  source                 = "${path.module}/../test_data/data_visualization/DataVisualization.csv"

  depends_on = [
    aws_s3_bucket.landing_bucket
  ]
}

############################################
# Finance Data
############################################
resource "aws_s3_object" "metadata_finance" {
  bucket                 = aws_s3_bucket.metadata_bucket.id
  key                    = "finance/metadata.json"
  source                 = "${path.module}/../metadata/finance/metadata.json"

  depends_on = [
    aws_s3_bucket.metadata_bucket
  ]
}

resource "aws_s3_object" "finance" {
  bucket                 = aws_s3_bucket.landing_bucket.id
  key                    = "finance/Finance.csv"
  source                 = "${path.module}/../test_data/finance/Finance.csv"

  depends_on = [
    aws_s3_bucket.landing_bucket
  ]
}