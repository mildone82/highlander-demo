resource "aws_dynamodb_table" "sessions" {
  name         = "${var.name_prefix}-agent_sessions"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "id"
  range_key    = "updated_at"

  attribute {
    name = "id"
    type = "S"
  }
  attribute {
    name = "updated_at"
    type = "N"
  }

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled     = true
    kms_key_arn = var.kms_key_arn
  }

  tags = merge(var.tags, { Name = "${var.name_prefix}-agent_sessions" })
}

resource "aws_dynamodb_table" "client_metadata" {
  name         = "${var.name_prefix}-client_metadata"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "client_id"
  range_key    = "recorded_at"

  attribute {
    name = "client_id"
    type = "S"
  }
  attribute {
    name = "recorded_at"
    type = "N"
  }

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled     = true
    kms_key_arn = var.kms_key_arn
  }

  tags = merge(var.tags, { Name = "${var.name_prefix}-client_metadata" })
}

resource "aws_dynamodb_table" "report_tasks" {
  name         = "${var.name_prefix}-report_tasks"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "id"

  attribute {
    name = "id"
    type = "S"
  }

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled     = true
    kms_key_arn = var.kms_key_arn
  }

  tags = merge(var.tags, { Name = "${var.name_prefix}-report_tasks" })
}

resource "aws_dynamodb_table" "longterm_memory" {
  name         = "${var.name_prefix}-longterm_memory"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "id"

  attribute {
    name = "id"
    type = "S"
  }

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled     = true
    kms_key_arn = var.kms_key_arn
  }

  tags = merge(var.tags, { Name = "${var.name_prefix}-longterm_memory" })
}

resource "aws_elasticache_subnet_group" "main" {
  name       = "${var.name_prefix}-cache-subnet"
  subnet_ids = var.data_subnet_ids
  tags       = merge(var.tags, { Name = "${var.name_prefix}-cache-subnet" })
}

resource "aws_elasticache_serverless_cache" "main" {
  engine               = "valkey"
  name                 = "${var.name_prefix}-valkey"
  major_engine_version = "8"

  cache_usage_limits {
    data_storage {
      maximum = 10
      unit    = "GB"
    }
    ecpu_per_second {
      maximum = 1000
    }
  }

  subnet_ids = var.data_subnet_ids
  kms_key_id = var.kms_key_arn

  tags = merge(var.tags, { Name = "${var.name_prefix}-valkey" })
}
