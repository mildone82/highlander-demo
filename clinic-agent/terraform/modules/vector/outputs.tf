output "vector_bucket_name" {
  value = aws_s3vectors_vector_bucket.main.vector_bucket_name
}

output "vector_bucket_arn" {
  value = aws_s3vectors_vector_bucket.main.vector_bucket_arn
}

output "index_names" {
  value = { for k, v in aws_s3vectors_index.tenant : k => v.index_name }
}

output "index_arns" {
  value = { for k, v in aws_s3vectors_index.tenant : k => v.index_arn }
}
