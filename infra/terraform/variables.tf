variable "aws_region" {
  type    = string
  default = "eu-west-3"
}

variable "environment" {
  type    = string
  default = "dev"
}

variable "lambda_zip_path" {
  type    = string
  default = "../../lambda.zip"
}

variable "schedule_expression" {
  type    = string
  default = "rate(1 minute)"
}

variable "database_url" {
  type      = string
  sensitive = true
}

variable "pandascore_token" {
  type      = string
  sensitive = true
}
