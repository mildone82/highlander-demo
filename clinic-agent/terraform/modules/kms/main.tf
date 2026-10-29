resource "aws_kms_key" "app" {
  description             = "Shared application CMK for ${var.name_prefix}"
  deletion_window_in_days = 30
  enable_key_rotation     = true
  tags                    = merge(var.tags, { Name = "${var.name_prefix}-app-cmk" })
}

resource "aws_kms_alias" "app" {
  name          = "alias/${var.name_prefix}-app"
  target_key_id = aws_kms_key.app.key_id
}

# Per-tenant CMKs implement the "one CMK per clinic" isolation requirement.
resource "aws_kms_key" "tenant" {
  for_each                = var.tenants
  description             = "Tenant CMK for ${each.value} (${each.key})"
  deletion_window_in_days = 30
  enable_key_rotation     = true
  tags                    = merge(var.tags, { Name = "${var.name_prefix}-${each.key}-cmk", Tenant = each.key })
}

resource "aws_kms_alias" "tenant" {
  for_each      = var.tenants
  name          = "alias/${var.name_prefix}-${each.key}"
  target_key_id = aws_kms_key.tenant[each.key].key_id
}
