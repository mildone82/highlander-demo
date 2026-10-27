data "aws_partition" "current" {}
data "aws_region" "current" {}

resource "aws_cloudwatch_log_group" "lambda" {
  for_each = var.lambda_function_names

  name              = "/aws/lambda/${each.value}"
  retention_in_days = 30
  tags              = merge(var.tags, { Name = each.value })
}

resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  for_each = var.lambda_function_names

  alarm_name          = "${each.value}-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Sum"
  threshold           = 1
  alarm_description   = "Lambda error alarm for ${each.value}"

  dimensions = {
    FunctionName = each.value
  }

  tags = merge(var.tags, { Name = "${each.value}-errors-alarm" })
}

resource "aws_cloudwatch_metric_alarm" "report_dlq_depth" {
  alarm_name          = "${var.report_dlq_name}-depth"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = 300
  statistic           = "Sum"
  threshold           = 0
  alarm_description   = "Report DLQ is non-empty"

  dimensions = {
    QueueName = var.report_dlq_name
  }

  tags = merge(var.tags, { Name = "${var.report_dlq_name}-depth-alarm" })
}

resource "aws_cloudtrail" "main" {
  count = var.enable_cloudtrail ? 1 : 0

  name                          = "${var.name_prefix}-trail"
  s3_bucket_name                = var.log_bucket_name
  include_global_service_events = true
  is_multi_region_trail         = false
  enable_log_file_validation    = true

  event_selector {
    read_write_type           = "All"
    include_management_events = true

    data_resource {
      type   = "AWS::S3::Object"
      values = ["arn:${data.aws_partition.current.partition}:s3:::${var.name_prefix}-data-*/"]
    }
  }

  tags = merge(var.tags, { Name = "${var.name_prefix}-trail" })
}
