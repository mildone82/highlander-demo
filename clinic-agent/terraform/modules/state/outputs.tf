output "table_names" {
  value = {
    sessions        = aws_dynamodb_table.sessions.name
    client_metadata = aws_dynamodb_table.client_metadata.name
    report_tasks    = aws_dynamodb_table.report_tasks.name
    longterm_memory = aws_dynamodb_table.longterm_memory.name
  }
}

output "table_arns" {
  value = {
    sessions        = aws_dynamodb_table.sessions.arn
    client_metadata = aws_dynamodb_table.client_metadata.arn
    report_tasks    = aws_dynamodb_table.report_tasks.arn
    longterm_memory = aws_dynamodb_table.longterm_memory.arn
  }
}

output "cache_endpoint" {
  value = aws_elasticache_serverless_cache.main.endpoint
}

output "cache_arn" {
  value = aws_elasticache_serverless_cache.main.arn
}
