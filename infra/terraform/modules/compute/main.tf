locals {
  name_prefix = "${var.project}-${var.environment}"
  alb_dns     = aws_lb.this.dns_name
}

resource "aws_ecs_cluster" "this" {
  name = "${local.name_prefix}-cluster"
  setting {
    name  = "containerInsights"
    value = "enabled"
  }
  tags = var.tags
}

resource "aws_iam_role" "execution" {
  name = "${local.name_prefix}-ecs-execution"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
  tags = var.tags
}

resource "aws_iam_role_policy_attachment" "execution" {
  role       = aws_iam_role.execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role_policy" "execution_secrets" {
  name = "${local.name_prefix}-read-secrets"
  role = aws_iam_role.execution.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["secretsmanager:GetSecretValue"]
      Resource = ["*"]
    }]
  })
}

resource "aws_iam_role" "task" {
  name = "${local.name_prefix}-ecs-task"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
  tags = var.tags
}

# TODO: tighten Resource ARNs once the S3 Vectors ARN format is confirmed in aws-cn.
resource "aws_iam_role_policy" "task_data_access" {
  name = "${local.name_prefix}-task-data-access"
  role = aws_iam_role.task.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3vectors:*"]
        Resource = ["*"]
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem"
        ]
        Resource = ["*"]
      },
      {
        Effect = "Allow"
        Action = [
          "sqs:SendMessage",
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage"
        ]
        Resource = ["*"]
      },
      {
        Effect   = "Allow"
        Action   = ["s3:GetObject"]
        Resource = ["*"]
      }
    ]
  })
}

resource "aws_cloudwatch_log_group" "rag" {
  name              = "/ecs/${local.name_prefix}/rag"
  retention_in_days = 14
  tags              = var.tags
}

resource "aws_cloudwatch_log_group" "memory" {
  name              = "/ecs/${local.name_prefix}/memory"
  retention_in_days = 14
  tags              = var.tags
}

resource "aws_cloudwatch_log_group" "model_gateway" {
  name              = "/ecs/${local.name_prefix}/model-gateway"
  retention_in_days = 14
  tags              = var.tags
}

resource "aws_lb" "this" {
  name               = "${local.name_prefix}-alb"
  internal           = true
  load_balancer_type = "application"
  security_groups    = [var.alb_security_group_id]
  subnets            = var.private_subnet_ids
  tags               = var.tags
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.this.arn
  port              = "80"
  protocol          = "HTTP"
  default_action {
    type = "fixed-response"
    fixed_response {
      content_type = "text/plain"
      message_body = "not found"
      status_code  = "404"
    }
  }
}

resource "aws_lb_target_group" "rag" {
  name        = "${local.name_prefix}-rag"
  port        = 8001
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"
  health_check {
    path                = "/healthz"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 3
    matcher             = "200"
  }
  tags = var.tags
}

resource "aws_lb_target_group" "memory" {
  name        = "${local.name_prefix}-memory"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"
  health_check {
    path                = "/healthz"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 3
    matcher             = "200"
  }
  tags = var.tags
}

resource "aws_lb_target_group" "model_gateway" {
  name        = "${local.name_prefix}-model-gateway"
  port        = 8002
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"
  health_check {
    path                = "/healthz"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 3
    matcher             = "200"
  }
  tags = var.tags
}

resource "aws_lb_listener_rule" "rag" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 10
  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.rag.arn
  }
  condition {
    path_pattern {
      values = ["/retrieve", "/retrieve/*"]
    }
  }
}

resource "aws_lb_listener_rule" "memory" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 20
  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.memory.arn
  }
  condition {
    path_pattern {
      values = ["/memory", "/memory/*"]
    }
  }
}

resource "aws_lb_listener_rule" "model_gateway" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 30
  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.model_gateway.arn
  }
  condition {
    path_pattern {
      values = ["/v1", "/v1/*", "/healthz"]
    }
  }
}

resource "aws_ecs_task_definition" "rag" {
  family                   = "${local.name_prefix}-rag"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = aws_iam_role.execution.arn
  task_role_arn            = aws_iam_role.task.arn
  container_definitions = jsonencode([{
    name  = "rag"
    image = var.container_images.rag
    portMappings = [{ containerPort = 8001, protocol = "tcp" }]
    environment = [
      { name = "EMBEDDER_PROVIDER", value = "openai" },
      { name = "EMBEDDER_BASE_URL", value = "http://${local.alb_dns}/v1" },
      { name = "EMBEDDER_MODEL", value = "bge-m3" },
      { name = "EMBEDDER_DIMS", value = "1024" },
      { name = "VECTOR_STORE_PROVIDER", value = "s3_vectors" },
      { name = "VECTOR_BUCKET", value = "knowledge-assistant-vectors" },
      { name = "VECTOR_INDEX", value = "knowledge" },
      { name = "VECTOR_DIMENSION", value = "1024" },
      { name = "VECTOR_REGION", value = "cn-north-1" }
    ]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.rag.name
        "awslogs-region"        = "cn-north-1"
        "awslogs-stream-prefix" = "rag"
      }
    }
  }])
  tags = var.tags
}

resource "aws_ecs_task_definition" "memory" {
  family                   = "${local.name_prefix}-memory"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "512"
  memory                   = "1024"
  execution_role_arn       = aws_iam_role.execution.arn
  task_role_arn            = aws_iam_role.task.arn
  container_definitions = jsonencode([{
    name  = "memory"
    image = var.container_images.memory
    portMappings = [{ containerPort = 8000, protocol = "tcp" }]
    environment = [
      { name = "MEMORY_PROVIDER", value = "mem0" },
      { name = "MEMORY_LLM_BASE_URL", value = "http://${local.alb_dns}/v1" },
      { name = "MEMORY_EMBEDDER_BASE_URL", value = "http://${local.alb_dns}/v1" },
      { name = "MEMORY_LLM_MODEL", value = "qwen2.5-7b-instruct" },
      { name = "MEMORY_EMBEDDER_MODEL", value = "bge-m3" },
      { name = "MEMORY_VECTOR_BUCKET", value = "knowledge-assistant-vectors" },
      { name = "MEMORY_VECTOR_INDEX", value = "memory" },
      { name = "MEMORY_VECTOR_DIMENSION", value = "1024" },
      { name = "MEMORY_VECTOR_REGION", value = "cn-north-1" },
      { name = "MEMORY_HISTORY_DB", value = "/tmp/history.db" }
    ]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.memory.name
        "awslogs-region"        = "cn-north-1"
        "awslogs-stream-prefix" = "memory"
      }
    }
  }])
  tags = var.tags
}

resource "aws_ecs_task_definition" "model_gateway" {
  family                   = "${local.name_prefix}-model-gateway"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = aws_iam_role.execution.arn
  task_role_arn            = aws_iam_role.task.arn
  container_definitions = jsonencode([{
    name  = "model-gateway"
    image = var.container_images.model_gateway
    portMappings = [{ containerPort = 8002, protocol = "tcp" }]
    environment = [
      { name = "MG_PRIMARY_BASE_URL", value = var.model_gateway_primary_base_url },
      { name = "MG_FALLBACK_BASE_URL", value = var.model_gateway_fallback_base_url },
      { name = "MG_PRIMARY_LLM_MODEL", value = "qwen2.5-7b-instruct" },
      { name = "MG_PRIMARY_EMBED_MODEL", value = "bge-m3" }
    ]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.model_gateway.name
        "awslogs-region"        = "cn-north-1"
        "awslogs-stream-prefix" = "model-gateway"
      }
    }
  }])
  tags = var.tags
}

resource "aws_ecs_service" "rag" {
  name            = "${local.name_prefix}-rag"
  cluster         = aws_ecs_cluster.this.id
  task_definition = aws_ecs_task_definition.rag.arn
  desired_count   = 1
  launch_type     = "FARGATE"
  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [var.service_security_group_id]
    assign_public_ip = false
  }
  load_balancer {
    target_group_arn = aws_lb_target_group.rag.arn
    container_name   = "rag"
    container_port   = 8001
  }
  tags = var.tags
}

resource "aws_ecs_service" "memory" {
  name            = "${local.name_prefix}-memory"
  cluster         = aws_ecs_cluster.this.id
  task_definition = aws_ecs_task_definition.memory.arn
  desired_count   = 1
  launch_type     = "FARGATE"
  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [var.service_security_group_id]
    assign_public_ip = false
  }
  load_balancer {
    target_group_arn = aws_lb_target_group.memory.arn
    container_name   = "memory"
    container_port   = 8000
  }
  tags = var.tags
}

resource "aws_ecs_service" "model_gateway" {
  name            = "${local.name_prefix}-model-gateway"
  cluster         = aws_ecs_cluster.this.id
  task_definition = aws_ecs_task_definition.model_gateway.arn
  desired_count   = 1
  launch_type     = "FARGATE"
  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [var.service_security_group_id]
    assign_public_ip = false
  }
  load_balancer {
    target_group_arn = aws_lb_target_group.model_gateway.arn
    container_name   = "model-gateway"
    container_port   = 8002
  }
  tags = var.tags
}
