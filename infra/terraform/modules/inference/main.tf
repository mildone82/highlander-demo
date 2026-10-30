locals {
  name_prefix = "${var.project}-${var.environment}"
}

resource "aws_iam_role" "sagemaker" {
  name = "${local.name_prefix}-sagemaker"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "sagemaker.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
  tags = var.tags
}

resource "aws_iam_role_policy_attachment" "sagemaker" {
  role       = aws_iam_role.sagemaker.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSageMakerFullAccess"
}

resource "aws_sagemaker_model" "llm" {
  count              = var.create_endpoints ? 1 : 0
  name               = "${local.name_prefix}-llm"
  execution_role_arn = aws_iam_role.sagemaker.arn
  primary_container {
    image          = var.llm_image
    model_data_url = var.llm_model_data
  }
  vpc_config {
    subnets            = var.subnet_ids
    security_group_ids = var.security_group_ids
  }
}

resource "aws_sagemaker_endpoint_configuration" "llm" {
  count = var.create_endpoints ? 1 : 0
  name  = "${local.name_prefix}-llm"
  production_variants {
    variant_name           = "AllTraffic"
    model_name             = aws_sagemaker_model.llm[0].name
    initial_instance_count = 1
    instance_type          = "ml.g5.xlarge"
  }
}

resource "aws_sagemaker_endpoint" "llm" {
  count                = var.create_endpoints ? 1 : 0
  name                 = "${local.name_prefix}-llm"
  endpoint_config_name = aws_sagemaker_endpoint_configuration.llm[0].name
  tags                 = var.tags
}

resource "aws_sagemaker_model" "embed" {
  count              = var.create_endpoints ? 1 : 0
  name               = "${local.name_prefix}-embed"
  execution_role_arn = aws_iam_role.sagemaker.arn
  primary_container {
    image          = var.embed_image
    model_data_url = var.embed_model_data
  }
  vpc_config {
    subnets            = var.subnet_ids
    security_group_ids = var.security_group_ids
  }
}

resource "aws_sagemaker_endpoint_configuration" "embed" {
  count = var.create_endpoints ? 1 : 0
  name  = "${local.name_prefix}-embed"
  production_variants {
    variant_name           = "AllTraffic"
    model_name             = aws_sagemaker_model.embed[0].name
    initial_instance_count = 1
    instance_type          = "ml.g4dn.xlarge"
  }
}

resource "aws_sagemaker_endpoint" "embed" {
  count                = var.create_endpoints ? 1 : 0
  name                 = "${local.name_prefix}-embed"
  endpoint_config_name = aws_sagemaker_endpoint_configuration.embed[0].name
  tags                 = var.tags
}
