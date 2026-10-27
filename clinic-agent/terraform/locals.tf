data "aws_partition" "current" {}
data "aws_region" "current" {}
data "aws_caller_identity" "current" {}

locals {
  region     = data.aws_region.current.region
  partition  = data.aws_partition.current.partition
  dns_suffix = data.aws_partition.current.dns_suffix
  account_id = data.aws_caller_identity.current.account_id

  name_prefix = var.name_prefix

  common_tags = merge(var.tags, {
    ManagedBy   = "terraform"
    Environment = var.environment
    Workspace   = var.workspace_name
  })
}
