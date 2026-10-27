resource "aws_s3vectors_vector_bucket" "main" {
  vector_bucket_name = "${var.name_prefix}-vectors"

  encryption_configuration {
    sse_type    = "aws:kms"
    kms_key_arn = var.app_key_arn
  }

  tags = merge(var.tags, { Name = "${var.name_prefix}-vectors" })
}

# One index per tenant so each clinic's embeddings are isolated and independently
# keyed (SSE-KMS) as required by the Stage 2 security design.
resource "aws_s3vectors_index" "tenant" {
  for_each = var.tenants

  vector_bucket_name = aws_s3vectors_vector_bucket.main.vector_bucket_name
  index_name         = "${each.key}-index"

  data_type       = "float32"
  dimension       = var.index_dimension
  distance_metric = "cosine"

  # Long free-text metadata is stored as non-filterable keys; filterable keys
  # (client_id, recorded_at, s3_path) are defined at write time by the pipeline.
  metadata_configuration {
    non_filterable_metadata_keys = ["chunk_text", "source_note"]
  }

  encryption_configuration {
    sse_type    = "aws:kms"
    kms_key_arn = var.tenant_keys[each.key]
  }

  tags = merge(var.tags, { Name = "${var.name_prefix}-${each.key}-index", Tenant = each.key })
}
