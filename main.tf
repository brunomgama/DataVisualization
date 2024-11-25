provider "aws" {
  region = var.region
}

module "s3_and_step_function" {
  source = "./src"
}
