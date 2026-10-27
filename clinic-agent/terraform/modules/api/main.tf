data "aws_partition" "current" {}

locals {
  pkg_root = "${path.module}/../../../lambda_packages"
}

data "aws_iam_policy_document" "authorizer_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "authorizer" {
  name               = "${var.name_prefix}-authorizer"
  assume_role_policy = data.aws_iam_policy_document.authorizer_assume.json
  tags               = merge(var.tags, { Name = "${var.name_prefix}-authorizer" })
}

data "aws_iam_policy_document" "authorizer" {
  statement {
    actions   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
    resources = ["arn:${data.aws_partition.current.partition}:logs:*:*:log-group:/aws/lambda/*"]
  }
}

resource "aws_iam_role_policy" "authorizer" {
  name   = "${var.name_prefix}-authorizer-policy"
  role   = aws_iam_role.authorizer.id
  policy = data.aws_iam_policy_document.authorizer.json
}

resource "aws_lambda_function" "authorizer" {
  function_name = "${var.name_prefix}-authorizer"
  role          = aws_iam_role.authorizer.arn
  runtime       = var.python_runtime
  handler       = "index.handler"
  filename      = "${local.pkg_root}/authorizer.zip"
  memory_size   = 128
  timeout       = 10
  architectures = ["arm64"]
  tags          = merge(var.tags, { Name = "${var.name_prefix}-authorizer" })
}

resource "aws_api_gateway_rest_api" "main" {
  name        = "${var.name_prefix}-api"
  description = "Clinic service API"
  endpoint_configuration {
    types = ["REGIONAL"]
  }
  tags = merge(var.tags, { Name = "${var.name_prefix}-api" })
}

resource "aws_api_gateway_authorizer" "jwt" {
  name                   = "${var.name_prefix}-jwt-authorizer"
  rest_api_id            = aws_api_gateway_rest_api.main.id
  type                   = "REQUEST"
  authorizer_uri         = aws_lambda_function.authorizer.invoke_arn
  authorizer_credentials = aws_iam_role.api_gateway.arn
  identity_source        = "method.request.header.Authorization"
}

resource "aws_api_gateway_resource" "proxy" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_rest_api.main.root_resource_id
  path_part   = "{proxy+}"
}

resource "aws_api_gateway_method" "proxy" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.proxy.id
  http_method   = "ANY"
  authorization = "CUSTOM"
  authorizer_id = aws_api_gateway_authorizer.jwt.id
}

resource "aws_api_gateway_integration" "proxy" {
  rest_api_id             = aws_api_gateway_rest_api.main.id
  resource_id             = aws_api_gateway_resource.proxy.id
  http_method             = aws_api_gateway_method.proxy.http_method
  type                    = "AWS_PROXY"
  integration_http_method = "POST"
  uri                     = var.api_handler_invoke_arn
}

resource "aws_api_gateway_method" "root" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_rest_api.main.root_resource_id
  http_method   = "ANY"
  authorization = "CUSTOM"
  authorizer_id = aws_api_gateway_authorizer.jwt.id
}

resource "aws_api_gateway_integration" "root" {
  rest_api_id             = aws_api_gateway_rest_api.main.id
  resource_id             = aws_api_gateway_rest_api.main.root_resource_id
  http_method             = aws_api_gateway_method.root.http_method
  type                    = "AWS_PROXY"
  integration_http_method = "POST"
  uri                     = var.api_handler_invoke_arn
}

data "aws_iam_policy_document" "api_gateway_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["apigateway.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "api_gateway" {
  name               = "${var.name_prefix}-api-gateway"
  assume_role_policy = data.aws_iam_policy_document.api_gateway_assume.json
  tags               = merge(var.tags, { Name = "${var.name_prefix}-api-gateway" })
}

data "aws_iam_policy_document" "api_gateway" {
  statement {
    actions   = ["lambda:InvokeFunction"]
    resources = [var.api_handler_arn]
  }
}

resource "aws_iam_role_policy" "api_gateway" {
  name   = "${var.name_prefix}-api-gateway-policy"
  role   = aws_iam_role.api_gateway.id
  policy = data.aws_iam_policy_document.api_gateway.json
}

resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowApiGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = var.api_handler_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.main.execution_arn}/*/*"
}

resource "aws_lambda_permission" "authorizer" {
  statement_id  = "AllowApiGatewayInvokeAuthorizer"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.authorizer.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.main.execution_arn}/authorizers/*"
}

resource "aws_api_gateway_deployment" "main" {
  rest_api_id = aws_api_gateway_rest_api.main.id

  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_method.root,
      aws_api_gateway_method.proxy,
      aws_api_gateway_integration.root,
      aws_api_gateway_integration.proxy,
    ]))
  }

  lifecycle {
    create_before_destroy = true
  }

  depends_on = [
    aws_api_gateway_integration.root,
    aws_api_gateway_integration.proxy,
  ]
}

resource "aws_api_gateway_stage" "main" {
  deployment_id = aws_api_gateway_deployment.main.id
  rest_api_id   = aws_api_gateway_rest_api.main.id
  stage_name    = "api"

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gateway.arn
    format = jsonencode({
      requestId    = "$context.requestId"
      ip           = "$context.identity.sourceIp"
      caller       = "$context.identity.caller"
      user         = "$context.identity.user"
      requestTime  = "$context.requestTime"
      httpMethod   = "$context.httpMethod"
      resourcePath = "$context.resourcePath"
      status       = "$context.status"
    })
  }
}

resource "aws_cloudwatch_log_group" "api_gateway" {
  name              = "API-Gateway-Execution-Logs_${aws_api_gateway_rest_api.main.id}/api"
  retention_in_days = 30
  tags              = merge(var.tags, { Name = "${var.name_prefix}-api-logs" })
}

resource "aws_api_gateway_domain_name" "main" {
  count                    = var.domain_name != "" ? 1 : 0
  domain_name              = var.domain_name
  regional_certificate_arn = var.certificate_arn

  endpoint_configuration {
    types = ["REGIONAL"]
  }
}

resource "aws_api_gateway_base_path_mapping" "main" {
  count       = var.domain_name != "" ? 1 : 0
  api_id      = aws_api_gateway_rest_api.main.id
  stage_name  = aws_api_gateway_stage.main.stage_name
  domain_name = aws_api_gateway_domain_name.main[0].domain_name
}
