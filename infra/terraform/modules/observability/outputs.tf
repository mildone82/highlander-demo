output "ingestion_dlq_alarm_arn" {
  value = aws_cloudwatch_metric_alarm.ingestion_dlq_depth.arn
}

output "memory_dlq_alarm_arn" {
  value = aws_cloudwatch_metric_alarm.memory_dlq_depth.arn
}
