locals {
  bucket_suffix = random_id.bucket_suffix.hex
}

resource "random_id" "bucket_suffix" {
  byte_length = 4
}

resource "aws_s3_bucket" "log" {
  bucket        = "${var.name_prefix}-logs-${local.bucket_suffix}"
  force_destroy = var.force_destroy
  tags          = merge(var.tags, { Name = "${var.name_prefix}-logs" })
}

resource "aws_s3_bucket_public_access_block" "log" {
  bucket = aws_s3_bucket.log.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "log" {
  bucket = aws_s3_bucket.log.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_policy" "log" {
  bucket = aws_s3_bucket.log.id
  policy = data.aws_iam_policy_document.log_bucket.json
}

data "aws_iam_policy_document" "log_bucket" {
  statement {
    effect    = "Allow"
    actions   = ["s3:PutObject"]
    resources = ["${aws_s3_bucket.log.arn}/*"]
    principals {
      type = "Service"
      identifiers = [
        "logging.s3.amazonaws.com",
      ]
    }
  }

  statement {
    effect    = "Allow"
    actions   = ["s3:PutObject"]
    resources = ["${aws_s3_bucket.log.arn}/*"]
    principals {
      type        = "Service"
      identifiers = ["cloudtrail.amazonaws.com"]
    }
  }
}

# --- Client data bucket (photos / X-ray / medical records, time-series) ---
resource "aws_s3_bucket" "data" {
  bucket        = "${var.name_prefix}-data-${local.bucket_suffix}"
  force_destroy = var.force_destroy
  tags          = merge(var.tags, { Name = "${var.name_prefix}-client-data" })
}

resource "aws_s3_bucket_public_access_block" "data" {
  bucket = aws_s3_bucket.data.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_ownership_controls" "data" {
  bucket = aws_s3_bucket.data.id
  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_versioning" "data" {
  bucket = aws_s3_bucket.data.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "data" {
  bucket = aws_s3_bucket.data.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = var.app_key_arn
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "data" {
  bucket = aws_s3_bucket.data.id

  rule {
    id     = "expire-delete-markers"
    status = "Enabled"

    noncurrent_version_expiration {
      noncurrent_days = 365
    }

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }
}

# --- HTML report bucket ---
resource "aws_s3_bucket" "report" {
  bucket        = "${var.name_prefix}-reports-${local.bucket_suffix}"
  force_destroy = var.force_destroy
  tags          = merge(var.tags, { Name = "${var.name_prefix}-reports" })
}

resource "aws_s3_bucket_public_access_block" "report" {
  bucket = aws_s3_bucket.report.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "report" {
  bucket = aws_s3_bucket.report.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "report" {
  bucket = aws_s3_bucket.report.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = var.app_key_arn
    }
  }
}

# --- SPA static asset bucket ---
resource "aws_s3_bucket" "spa" {
  bucket        = "${var.name_prefix}-spa-${local.bucket_suffix}"
  force_destroy = var.force_destroy
  tags          = merge(var.tags, { Name = "${var.name_prefix}-spa" })
}

resource "aws_s3_bucket_public_access_block" "spa" {
  bucket = aws_s3_bucket.spa.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "spa" {
  bucket = aws_s3_bucket.spa.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}
