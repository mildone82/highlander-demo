output "web_acl_arn" {
  value = var.enable ? aws_wafv2_web_acl.main[0].arn : ""
}
