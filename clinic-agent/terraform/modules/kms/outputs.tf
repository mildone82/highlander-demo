output "app_key_arn" {
  value = aws_kms_key.app.arn
}

output "app_key_id" {
  value = aws_kms_key.app.key_id
}

output "tenant_key_arns" {
  value = { for k, v in aws_kms_key.tenant : k => v.arn }
}

output "tenant_key_ids" {
  value = { for k, v in aws_kms_key.tenant : k => v.key_id }
}
