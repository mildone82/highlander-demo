output "document_bucket_name" {
  value = aws_s3_bucket.documents.id
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

output "ingestion_dlq_name" {
  value = aws_sqs_queue.ingestion_dlq.name
}

output "memory_dlq_name" {
  value = aws_sqs_queue.memory_dlq.name
}

output "ingestion_state_table_name" {
  value = aws_dynamodb_table.ingestion_state.name
}

output "session_table_name" {
  value = aws_dynamodb_table.session.name
}

output "model_api_key_secret_arn" {
  value = aws_secretsmanager_secret.model_api_key.arn
}
