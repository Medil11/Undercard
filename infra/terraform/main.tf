terraform {
  required_version = ">= 1.6"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

resource "aws_iam_role" "ingestion" {
  name = "esport-live-ingestion-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "logs" {
  role       = aws_iam_role.ingestion.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_lambda_function" "ingestion" {
  function_name    = "esport-live-ingestion-${var.environment}"
  role             = aws_iam_role.ingestion.arn
  runtime          = "python3.12"
  handler          = "ingestion.handler.lambda_handler"
  filename         = var.lambda_zip_path
  source_code_hash = filebase64sha256(var.lambda_zip_path)
  timeout          = 60

  environment {
    variables = {
      DATABASE_URL     = var.database_url
      PANDASCORE_TOKEN = var.pandascore_token
    }
  }
}

resource "aws_cloudwatch_event_rule" "schedule" {
  name                = "esport-live-ingestion-${var.environment}"
  schedule_expression = var.schedule_expression
}

resource "aws_cloudwatch_event_target" "ingestion" {
  rule = aws_cloudwatch_event_rule.schedule.name
  arn  = aws_lambda_function.ingestion.arn
}

resource "aws_lambda_permission" "events" {
  statement_id  = "AllowEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ingestion.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.schedule.arn
}
