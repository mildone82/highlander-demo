resource "aws_sqs_queue" "report_dlq" {
  name                      = "${var.name_prefix}-report-dlq"
  message_retention_seconds = 1209600
  tags                      = merge(var.tags, { Name = "${var.name_prefix}-report-dlq" })
}

resource "aws_sqs_queue" "report" {
  name                       = "${var.name_prefix}-report-jobs"
  visibility_timeout_seconds = 600
  message_retention_seconds  = 86400
  delay_seconds              = 0

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.report_dlq.arn
    maxReceiveCount     = 3
  })

  tags = merge(var.tags, { Name = "${var.name_prefix}-report-jobs" })
}

data "aws_iam_policy_document" "sfn_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["states.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "sfn" {
  name               = "${var.name_prefix}-report-workflow"
  assume_role_policy = data.aws_iam_policy_document.sfn_assume.json
  tags               = merge(var.tags, { Name = "${var.name_prefix}-report-workflow" })
}

data "aws_iam_policy_document" "sfn" {
  statement {
    actions   = ["lambda:InvokeFunction"]
    resources = [var.report_generator_arn]
  }
  statement {
    actions   = ["sqs:SendMessage", "sqs:GetQueueAttributes"]
    resources = [aws_sqs_queue.report.arn, aws_sqs_queue.report_dlq.arn]
  }
}

resource "aws_iam_role_policy" "sfn" {
  name   = "${var.name_prefix}-report-workflow-policy"
  role   = aws_iam_role.sfn.id
  policy = data.aws_iam_policy_document.sfn.json
}

resource "aws_sfn_state_machine" "report" {
  name     = "${var.name_prefix}-report-workflow"
  role_arn = aws_iam_role.sfn.arn

  definition = jsonencode({
    Comment = "Async HTML report rendering workflow"
    StartAt = "RenderReport"
    States = {
      RenderReport = {
        Type     = "Task"
        Resource = "arn:aws:states:::lambda:invoke"
        Parameters = {
          FunctionName = var.report_generator_name
          "Payload.$"  = "$"
        }
        Retry = [
          {
            ErrorEquals     = ["States.ALL"]
            IntervalSeconds = 5
            MaxAttempts     = 3
            BackoffRate     = 2
          }
        ]
        Catch = [
          {
            ErrorEquals = ["States.ALL"]
            Next        = "NotifyFailure"
          }
        ]
        End = true
      }
      NotifyFailure = {
        Type  = "Fail"
        Error = "ReportRenderFailed"
      }
    }
  })

  tags = merge(var.tags, { Name = "${var.name_prefix}-report-workflow" })
}

resource "aws_cloudwatch_event_rule" "report_ingest" {
  name        = "${var.name_prefix}-report-jobs"
  description = "Routes report jobs from SQS events to Step Functions"

  event_pattern = jsonencode({
    source      = ["aws.sqs"]
    detail-type = ["SQS Receive Message"]
  })

  tags = merge(var.tags, { Name = "${var.name_prefix}-report-jobs-rule" })
}
