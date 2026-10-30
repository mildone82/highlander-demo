locals {
  name_prefix = "${var.project}-${var.environment}"
}

resource "aws_s3_bucket" "documents" {
  bucket        = "${local.name_prefix}-documents"
  force_destroy = false
  tags          = merge(var.tags, { Name = "${local.name_prefix}-documents" })
}

resource "aws_s3_bucket_versioning" "documents" {
  bucket = aws_s3_bucket.documents.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "documents" {
  bucket = aws_s3_bucket.documents.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "documents" {
  bucket                  = aws_s3_bucket.documents.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_sqs_queue" "ingestion" {
  name                       = "${local.name_prefix}-ingestion"
  message_retention_seconds  = 1209600
  visibility_timeout_seconds = 120
  tags                       = merge(var.tags, { Name = "${local.name_prefix}-ingestion" })
}

resource "aws_sqs_queue" "ingestion_dlq" {
  name                      = "${local.name_prefix}-ingestion-dlq"
  message_retention_seconds = 1209600
  tags                      = merge(var.tags, { Name = "${local.name_prefix}-ingestion-dlq" })
}

resource "aws_sqs_queue_redrive_policy" "ingestion" {
  queue_url = aws_sqs_queue.ingestion.id
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.ingestion_dlq.arn
    maxReceiveCount     = 5
  })
}

resource "aws_sqs_queue_policy" "ingestion" {
  queue_url = aws_sqs_queue.ingestion.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "s3.amazonaws.com" }
      Action    = "sqs:SendMessage"
      Resource  = aws_sqs_queue.ingestion.arn
      Condition = {
        ArnLike = { "aws:SourceArn" = aws_s3_bucket.documents.arn }
      }
    }]
  })
}

resource "aws_s3_bucket_notification" "documents" {
  bucket = aws_s3_bucket.documents.id
  queue {
    queue_arn = aws_sqs_queue.ingestion.arn
    events    = ["s3:ObjectCreated:*"]
  }
  depends_on = [aws_sqs_queue_policy.ingestion]
}

resource "aws_sqs_queue" "memory" {
  name                       = "${local.name_prefix}-memory"
  message_retention_seconds  = 1209600
  visibility_timeout_seconds = 120
  tags                       = merge(var.tags, { Name = "${local.name_prefix}-memory" })
}

resource "aws_sqs_queue" "memory_dlq" {
  name                      = "${local.name_prefix}-memory-dlq"
  message_retention_seconds = 1209600
  tags                      = merge(var.tags, { Name = "${local.name_prefix}-memory-dlq" })
}

resource "aws_sqs_queue_redrive_policy" "memory" {
  queue_url = aws_sqs_queue.memory.id
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.memory_dlq.arn
    maxReceiveCount     = 5
  })
}

resource "aws_dynamodb_table" "ingestion_state" {
  name         = "${local.name_prefix}-ingestion-state"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "request_id"
  attribute {
    name = "request_id"
    type = "S"
  }
  tags = merge(var.tags, { Name = "${local.name_prefix}-ingestion-state" })
}

resource "aws_dynamodb_table" "session" {
  name         = "${local.name_prefix}-session"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "session_id"
  attribute {
    name = "session_id"
    type = "S"
  }
  tags = merge(var.tags, { Name = "${local.name_prefix}-session" })
}

resource "aws_dynamodb_table" "memory_write_state" {
  name         = "${local.name_prefix}-memory-write-state"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "request_id"
  attribute {
    name = "request_id"
    type = "S"
  }
  tags = merge(var.tags, { Name = "${local.name_prefix}-memory-write-state" })
}

resource "aws_secretsmanager_secret" "model_api_key_primary" {
  name = "${local.name_prefix}-model-api-key-primary"
  tags = merge(var.tags, { Name = "${local.name_prefix}-model-api-key-primary" })
}

resource "aws_secretsmanager_secret_version" "model_api_key_primary" {
  secret_id     = aws_secretsmanager_secret.model_api_key_primary.id
  secret_string = var.model_api_key_primary
}

resource "aws_secretsmanager_secret" "model_api_key_fallback" {
  name = "${local.name_prefix}-model-api-key-fallback"
  tags = merge(var.tags, { Name = "${local.name_prefix}-model-api-key-fallback" })
}

resource "aws_secretsmanager_secret_version" "model_api_key_fallback" {
  secret_id     = aws_secretsmanager_secret.model_api_key_fallback.id
  secret_string = var.model_api_key_fallback
}
