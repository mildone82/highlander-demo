locals {
  name_prefix = "${var.project}-${var.environment}"
}

resource "aws_cloudwatch_metric_alarm" "ingestion_dlq_depth" {
  alarm_name          = "${local.name_prefix}-ingestion-dlq-depth"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  period              = 300
  threshold           = 0
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  statistic           = "Maximum"
  dimensions = {
    QueueName = var.ingestion_dlq_name
  }
  alarm_description = "Ingestion DLQ is non-empty"
  alarm_actions     = []
  tags              = var.tags
}

resource "aws_cloudwatch_metric_alarm" "memory_dlq_depth" {
  alarm_name          = "${local.name_prefix}-memory-dlq-depth"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  period              = 300
  threshold           = 0
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  statistic           = "Maximum"
  dimensions = {
    QueueName = var.memory_dlq_name
  }
  alarm_description = "Memory write DLQ is non-empty"
  alarm_actions     = []
  tags              = var.tags
}
