resource "aws_s3_object" "metadata" {
  bucket                 = aws_s3_bucket.metadata_bucket.id
  key                    = "metadata.json"
  source                 = "${path.module}/../metadata/metadata.json"

  depends_on = [
    aws_s3_bucket.metadata_bucket
  ]
}

resource "aws_s3_object" "data_visualization" {
  bucket                 = aws_s3_bucket.landing_bucket.id
  key                    = "data_visualization/DataVisualization.csv"
  source                 = "${path.module}/../test_data/DataVisualization.csv"

  depends_on = [
    aws_s3_bucket.landing_bucket
  ]
}