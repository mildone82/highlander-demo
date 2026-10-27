output "report_queue_url" {
  value = aws_sqs_queue.report.url
}

output "report_queue_arn" {
  value = aws_sqs_queue.report.arn
}

output "report_dlq_name" {
  value = aws_sqs_queue.report_dlq.name
}

output "report_dlq_arn" {
  value = aws_sqs_queue.report_dlq.arn
}

output "state_machine_arn" {
  value = aws_sfn_state_machine.report.arn
}
