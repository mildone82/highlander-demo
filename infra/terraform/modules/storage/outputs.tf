output "document_bucket_name" {
  value = aws_s3_bucket.documents.id
}

output "document_bucket_arn" {
  value = aws_s3_bucket.documents.arn
}

output "ingestion_queue_url" {
  value = aws_sqs_queue.ingestion.id
}

output "ingestion_queue_arn" {
  value = aws_sqs_queue.ingestion.arn
}

output "memory_queue_url" {
  value = aws_sqs_queue.memory.id
}

output "memory_queue_arn" {
  value = aws_sqs_queue.memory.arn
}

output "ingestion_dlq_name" {
  value = aws_sqs_queue.ingestion_dlq.name
}

output "memory_dlq_name" {
  value = aws_sqs_queue.memory_dlq.name
}

output "ingestion_state_table_name" {
  value = aws_dynamodb_table.ingestion_state.name
}

output "ingestion_state_table_arn" {
  value = aws_dynamodb_table.ingestion_state.arn
}

output "session_table_name" {
  value = aws_dynamodb_table.session.name
}

output "memory_write_state_table_name" {
  value = aws_dynamodb_table.memory_write_state.name
}

output "memory_write_state_table_arn" {
  value = aws_dynamodb_table.memory_write_state.arn
}

output "model_api_key_primary_arn" {
  value = aws_secretsmanager_secret.model_api_key_primary.arn
}

output "model_api_key_fallback_arn" {
  value = aws_secretsmanager_secret.model_api_key_fallback.arn
}
