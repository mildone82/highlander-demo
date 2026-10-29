data "aws_partition" "current" {}
data "aws_region" "current" {}

locals {
  pkg_root = "${path.module}/../../../lambda_packages"
}

# --- External LLM (DeepSeek) credential ---
resource "aws_secretsmanager_secret" "deepseek" {
  name                    = "${var.name_prefix}/llm/deepseek"
  recovery_window_in_days = 7
  tags                    = merge(var.tags, { Name = "${var.name_prefix}-deepseek" })
}

resource "aws_secretsmanager_secret_version" "deepseek" {
  secret_id     = aws_secretsmanager_secret.deepseek.id
  secret_string = jsonencode({ api_key = "" }) # set via console/CLI after deploy
}

# --- AgentCore Runtime (orchestration layer) ---
resource "aws_ecr_repository" "agent" {
  name                 = "${var.name_prefix}/agent-runtime"
  image_tag_mutability = "MUTABLE"
  force_delete         = true
  tags                 = merge(var.tags, { Name = "${var.name_prefix}-agent-ecr" })
}

data "aws_iam_policy_document" "agentcore_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["bedrock-agentcore.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "agentcore" {
  name               = "${var.name_prefix}-agentcore-runtime"
  assume_role_policy = data.aws_iam_policy_document.agentcore_assume.json
  tags               = merge(var.tags, { Name = "${var.name_prefix}-agentcore-runtime" })
}

data "aws_iam_policy_document" "agentcore" {
  statement {
    actions = [
      "ecr:GetAuthorizationToken",
      "ecr:BatchCheckLayerAvailability",
      "ecr:GetDownloadUrlForLayer",
      "ecr:BatchGetImage",
    ]
    resources = ["*"]
  }
  statement {
    actions   = ["s3:GetObject", "s3:ListBucket"]
    resources = [var.data_bucket_arn, "${var.data_bucket_arn}/*"]
  }
  statement {
    actions = [
      "s3vectors:GetVectors",
      "s3vectors:QueryVectors",
      "s3vectors:PutVectors",
    ]
    resources = [for arn in var.vector_index_arns : arn]
  }
  statement {
    actions   = ["sagemaker:InvokeEndpoint"]
    resources = [aws_sagemaker_endpoint.embedding.arn]
  }
  statement {
    actions   = ["secretsmanager:GetSecretValue"]
    resources = [aws_secretsmanager_secret.deepseek.arn]
  }
}

resource "aws_iam_role_policy" "agentcore" {
  name   = "${var.name_prefix}-agentcore-runtime-policy"
  role   = aws_iam_role.agentcore.id
  policy = data.aws_iam_policy_document.agentcore.json
}

resource "aws_bedrockagentcore_agent_runtime" "main" {
  agent_runtime_name = "${var.name_prefix}-agent-runtime"
  role_arn           = aws_iam_role.agentcore.arn

  agent_runtime_artifact {
    container_configuration {
      container_uri = "${aws_ecr_repository.agent.repository_url}:latest"
    }
  }

  environment_variables = {
    S3_VECTORS_BUCKET  = var.vector_index_arns != {} ? element(keys(var.vector_index_arns), 0) : ""
    DATA_BUCKET        = var.data_bucket_name
    EMBEDDING_ENDPOINT = aws_sagemaker_endpoint.embedding.name
    MODEL_GATEWAY_URL  = "https://example.invalid/gateway"
  }

  network_configuration {
    network_mode = "PUBLIC"
  }

  protocol_configuration {
    server_protocol = "AGUI"
  }

  tags = merge(var.tags, { Name = "${var.name_prefix}-agent-runtime" })
}

# --- SageMaker self-hosted embedding (TEI + BGE-M3) ---
data "aws_iam_policy_document" "sagemaker_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["sagemaker.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "sagemaker" {
  name               = "${var.name_prefix}-sagemaker-embedding"
  assume_role_policy = data.aws_iam_policy_document.sagemaker_assume.json
  tags               = merge(var.tags, { Name = "${var.name_prefix}-sagemaker-embedding" })
}

data "aws_iam_policy_document" "sagemaker" {
  statement {
    actions = [
      "ecr:GetAuthorizationToken",
      "ecr:BatchCheckLayerAvailability",
      "ecr:GetDownloadUrlForLayer",
      "ecr:BatchGetImage",
    ]
    resources = ["*"]
  }
  statement {
    actions   = ["s3:GetObject", "s3:ListBucket"]
    resources = ["arn:${data.aws_partition.current.partition}:s3:::${var.name_prefix}*", "arn:${data.aws_partition.current.partition}:s3:::${var.name_prefix}*/*"]
  }
}

resource "aws_iam_role_policy" "sagemaker" {
  name   = "${var.name_prefix}-sagemaker-embedding-policy"
  role   = aws_iam_role.sagemaker.id
  policy = data.aws_iam_policy_document.sagemaker.json
}

resource "aws_sagemaker_model" "embedding" {
  name               = "${var.name_prefix}-embedding-model"
  execution_role_arn = aws_iam_role.sagemaker.arn

  primary_container {
    image          = var.embedding_model_image
    mode           = "SingleModel"
    model_data_url = var.embedding_model_data_url
  }

  tags = merge(var.tags, { Name = "${var.name_prefix}-embedding-model" })
}

resource "aws_sagemaker_endpoint_configuration" "embedding" {
  name = "${var.name_prefix}-embedding-endpoint-config"

  production_variants {
    variant_name = "AllTraffic"
    model_name   = aws_sagemaker_model.embedding.name
    serverless_config {
      max_concurrency   = 20
      memory_size_in_mb = 6144
    }
  }

  tags = merge(var.tags, { Name = "${var.name_prefix}-embedding-endpoint-config" })
}

resource "aws_sagemaker_endpoint" "embedding" {
  name                 = "${var.name_prefix}-embedding-endpoint"
  endpoint_config_name = aws_sagemaker_endpoint_configuration.embedding.name
  tags                 = merge(var.tags, { Name = "${var.name_prefix}-embedding-endpoint" })
}

# --- Lambda functions ---
data "aws_iam_policy_document" "lambda_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "api_handler" {
  name               = "${var.name_prefix}-api-handler"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
  tags               = merge(var.tags, { Name = "${var.name_prefix}-api-handler" })
}

data "aws_iam_policy_document" "api_handler" {
  statement {
    actions   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
    resources = ["arn:${data.aws_partition.current.partition}:logs:${data.aws_region.current.region}:*:log-group:/aws/lambda/*"]
  }
  statement {
    actions   = ["bedrock-agentcore:InvokeAgentRuntime", "bedrock-agentcore:StartAgentRuntimeSession"]
    resources = [aws_bedrockagentcore_agent_runtime.main.agent_runtime_arn]
  }
  statement {
    actions   = ["dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:Query"]
    resources = ["arn:${data.aws_partition.current.partition}:dynamodb:${data.aws_region.current.region}:*:table/*"]
  }
  statement {
    actions   = ["sqs:SendMessage"]
    resources = ["arn:${data.aws_partition.current.partition}:sqs:${data.aws_region.current.region}:*:*"]
  }
}

resource "aws_iam_role_policy" "api_handler" {
  name   = "${var.name_prefix}-api-handler-policy"
  role   = aws_iam_role.api_handler.id
  policy = data.aws_iam_policy_document.api_handler.json
}

resource "aws_lambda_function" "api_handler" {
  function_name = "${var.name_prefix}-api-handler"
  role          = aws_iam_role.api_handler.arn
  runtime       = var.python_runtime
  handler       = "index.handler"
  filename      = "${local.pkg_root}/api_handler.zip"
  memory_size   = var.memory_size
  timeout       = var.timeout
  architectures = ["arm64"]
  tags          = merge(var.tags, { Name = "${var.name_prefix}-api-handler" })
}

resource "aws_iam_role" "model_gateway" {
  name               = "${var.name_prefix}-model-gateway"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
  tags               = merge(var.tags, { Name = "${var.name_prefix}-model-gateway" })
}

data "aws_iam_policy_document" "model_gateway" {
  statement {
    actions   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
    resources = ["arn:${data.aws_partition.current.partition}:logs:${data.aws_region.current.region}:*:log-group:/aws/lambda/*"]
  }
  statement {
    actions   = ["secretsmanager:GetSecretValue"]
    resources = [aws_secretsmanager_secret.deepseek.arn]
  }
  statement {
    actions   = ["dynamodb:PutItem"]
    resources = ["arn:${data.aws_partition.current.partition}:dynamodb:${data.aws_region.current.region}:*:table/*"]
  }
}

resource "aws_iam_role_policy" "model_gateway" {
  name   = "${var.name_prefix}-model-gateway-policy"
  role   = aws_iam_role.model_gateway.id
  policy = data.aws_iam_policy_document.model_gateway.json
}

resource "aws_lambda_function" "model_gateway" {
  function_name = "${var.name_prefix}-model-gateway"
  role          = aws_iam_role.model_gateway.arn
  runtime       = var.python_runtime
  handler       = "index.handler"
  filename      = "${local.pkg_root}/model_gateway.zip"
  memory_size   = var.memory_size
  timeout       = var.timeout
  architectures = ["arm64"]

  environment {
    variables = {
      DEEPSEEK_BASE_URL    = var.deepseek_base_url
      DEEPSEEK_MODEL_PRO   = var.deepseek_model_pro
      DEEPSEEK_MODEL_FLASH = var.deepseek_model_flash
      DEEPSEEK_SECRET_ARN  = aws_secretsmanager_secret.deepseek.arn
    }
  }

  tags = merge(var.tags, { Name = "${var.name_prefix}-model-gateway" })
}

resource "aws_iam_role" "report_generator" {
  name               = "${var.name_prefix}-report-generator"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
  tags               = merge(var.tags, { Name = "${var.name_prefix}-report-generator" })
}

data "aws_iam_policy_document" "report_generator" {
  statement {
    actions   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
    resources = ["arn:${data.aws_partition.current.partition}:logs:${data.aws_region.current.region}:*:log-group:/aws/lambda/*"]
  }
  statement {
    actions   = ["s3:GetObject", "s3:PutObject"]
    resources = [var.data_bucket_arn, "${var.data_bucket_arn}/*", var.report_bucket_arn, "${var.report_bucket_arn}/*"]
  }
  statement {
    actions   = ["kms:Encrypt", "kms:Decrypt", "kms:GenerateDataKey"]
    resources = [var.kms_key_arn]
  }
}

resource "aws_iam_role_policy" "report_generator" {
  name   = "${var.name_prefix}-report-generator-policy"
  role   = aws_iam_role.report_generator.id
  policy = data.aws_iam_policy_document.report_generator.json
}

resource "aws_lambda_function" "report_generator" {
  function_name = "${var.name_prefix}-report-generator"
  role          = aws_iam_role.report_generator.arn
  runtime       = var.python_runtime
  handler       = "index.handler"
  filename      = "${local.pkg_root}/report_generator.zip"
  memory_size   = var.memory_size
  timeout       = 300
  architectures = ["arm64"]

  environment {
    variables = {
      REPORT_BUCKET = var.report_bucket_name
    }
  }

  tags = merge(var.tags, { Name = "${var.name_prefix}-report-generator" })
}

resource "aws_iam_role" "ingest" {
  name               = "${var.name_prefix}-ingest"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
  tags               = merge(var.tags, { Name = "${var.name_prefix}-ingest" })
}

data "aws_iam_policy_document" "ingest" {
  statement {
    actions   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
    resources = ["arn:${data.aws_partition.current.partition}:logs:${data.aws_region.current.region}:*:log-group:/aws/lambda/*"]
  }
  statement {
    actions   = ["s3:GetObject"]
    resources = [var.data_bucket_arn, "${var.data_bucket_arn}/*"]
  }
  statement {
    actions   = ["sagemaker:InvokeEndpoint"]
    resources = [aws_sagemaker_endpoint.embedding.arn]
  }
  statement {
    actions   = ["s3vectors:PutVectors"]
    resources = [for arn in var.vector_index_arns : arn]
  }
  statement {
    actions   = ["dynamodb:PutItem"]
    resources = ["arn:${data.aws_partition.current.partition}:dynamodb:${data.aws_region.current.region}:*:table/*"]
  }
}

resource "aws_iam_role_policy" "ingest" {
  name   = "${var.name_prefix}-ingest-policy"
  role   = aws_iam_role.ingest.id
  policy = data.aws_iam_policy_document.ingest.json
}

resource "aws_lambda_function" "ingest" {
  function_name = "${var.name_prefix}-ingest"
  role          = aws_iam_role.ingest.arn
  runtime       = var.python_runtime
  handler       = "index.handler"
  filename      = "${local.pkg_root}/ingest.zip"
  memory_size   = var.memory_size
  timeout       = 300
  architectures = ["arm64"]
  tags          = merge(var.tags, { Name = "${var.name_prefix}-ingest" })
}
