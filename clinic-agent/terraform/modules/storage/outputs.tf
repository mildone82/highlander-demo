output "data_bucket_name" {
  value = aws_s3_bucket.data.bucket
}

output "data_bucket_arn" {
  value = aws_s3_bucket.data.arn
}

output "report_bucket_name" {
  value = aws_s3_bucket.report.bucket
}

output "report_bucket_arn" {
  value = aws_s3_bucket.report.arn
}

output "spa_bucket_name" {
  value = aws_s3_bucket.spa.bucket
}

output "spa_bucket_arn" {
  value = aws_s3_bucket.spa.arn
}

output "log_bucket_name" {
  value = aws_s3_bucket.log.bucket
}

output "log_bucket_arn" {
  value = aws_s3_bucket.log.arn
}
