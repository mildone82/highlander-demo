resource "random_password" "db_password" {
  length  = 32
  special = false
}

resource "random_password" "keycloak_admin" {
  length  = 24
  special = true
}

resource "aws_secretsmanager_secret" "db" {
  name                    = "${var.name_prefix}/keycloak/db"
  recovery_window_in_days = 7
  tags                    = merge(var.tags, { Name = "${var.name_prefix}-keycloak-db" })
}

resource "aws_secretsmanager_secret_version" "db" {
  secret_id = aws_secretsmanager_secret.db.id
  secret_string = jsonencode({
    username = var.db_username
    password = random_password.db_password.result
    host     = aws_db_instance.keycloak.address
    port     = aws_db_instance.keycloak.port
    dbname   = var.db_name
  })
}

resource "aws_secretsmanager_secret" "keycloak_admin" {
  name                    = "${var.name_prefix}/keycloak/admin"
  recovery_window_in_days = 7
  tags                    = merge(var.tags, { Name = "${var.name_prefix}-keycloak-admin" })
}

resource "aws_secretsmanager_secret_version" "keycloak_admin" {
  secret_id = aws_secretsmanager_secret.keycloak_admin.id
  secret_string = jsonencode({
    username = "admin"
    password = random_password.keycloak_admin.result
  })
}

resource "aws_db_subnet_group" "keycloak" {
  name       = "${var.name_prefix}-keycloak-db-subnet"
  subnet_ids = var.data_subnet_ids
  tags       = merge(var.tags, { Name = "${var.name_prefix}-keycloak-db-subnet" })
}

resource "aws_db_instance" "keycloak" {
  identifier     = "${var.name_prefix}-keycloak"
  engine         = "postgres"
  engine_version = "16.4"
  instance_class = var.db_instance_class

  db_name  = var.db_name
  username = var.db_username
  password = random_password.db_password.result

  allocated_storage      = var.db_allocated_storage
  storage_encrypted      = true
  kms_key_id             = var.kms_key_arn
  multi_az               = true
  publicly_accessible    = false
  db_subnet_group_name   = aws_db_subnet_group.keycloak.name
  vpc_security_group_ids = [aws_security_group.db.id]

  backup_retention_period   = 14
  backup_window             = "03:00-04:00"
  maintenance_window        = "sun:04:30-sun:05:30"
  skip_final_snapshot       = false
  final_snapshot_identifier = "${var.name_prefix}-keycloak-final"
  deletion_protection       = true

  tags = merge(var.tags, { Name = "${var.name_prefix}-keycloak-db" })
}

resource "aws_security_group" "db" {
  name        = "${var.name_prefix}-keycloak-db-sg"
  description = "Keycloak RDS"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, { Name = "${var.name_prefix}-keycloak-db-sg" })
}

resource "aws_security_group" "alb" {
  name        = "${var.name_prefix}-keycloak-alb-sg"
  description = "Keycloak ALB"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, { Name = "${var.name_prefix}-keycloak-alb-sg" })
}

resource "aws_security_group" "ecs" {
  name        = "${var.name_prefix}-keycloak-ecs-sg"
  description = "Keycloak ECS tasks"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = 8080
    to_port         = 8080
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, { Name = "${var.name_prefix}-keycloak-ecs-sg" })
}

resource "aws_lb" "keycloak" {
  name               = "${var.name_prefix}-keycloak-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = var.public_subnet_ids
  tags               = merge(var.tags, { Name = "${var.name_prefix}-keycloak-alb" })
}

resource "aws_lb_target_group" "keycloak" {
  name        = "${var.name_prefix}-keycloak-tg"
  port        = 8080
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"

  health_check {
    path                = "/realms/master"
    matcher             = "200,302"
    interval            = 30
    timeout             = 10
    healthy_threshold   = 3
    unhealthy_threshold = 3
  }

  tags = merge(var.tags, { Name = "${var.name_prefix}-keycloak-tg" })
}

resource "aws_lb_listener" "https" {
  count             = var.certificate_arn != "" ? 1 : 0
  load_balancer_arn = aws_lb.keycloak.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  certificate_arn   = var.certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.keycloak.arn
  }
}

resource "aws_lb_listener" "http" {
  count             = var.certificate_arn == "" ? 1 : 0
  load_balancer_arn = aws_lb.keycloak.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.keycloak.arn
  }
}

resource "aws_ecs_cluster" "keycloak" {
  name = "${var.name_prefix}-keycloak"
  setting {
    name  = "containerInsights"
    value = "enabled"
  }
  tags = merge(var.tags, { Name = "${var.name_prefix}-keycloak-cluster" })
}

resource "aws_ecs_task_definition" "keycloak" {
  family                   = "${var.name_prefix}-keycloak"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "1024"
  memory                   = "2048"
  execution_role_arn       = aws_iam_role.execution.arn
  task_role_arn            = aws_iam_role.task.arn

  container_definitions = jsonencode([
    {
      name  = "keycloak"
      image = var.keycloak_image
      portMappings = [
        { containerPort = 8080, protocol = "tcp" }
      ]
      environment = [
        { name = "KC_DB", value = "postgres" },
        { name = "KC_DB_URL_HOST", value = aws_db_instance.keycloak.address },
        { name = "KC_DB_URL_DATABASE", value = var.db_name },
        { name = "KC_PROXY_HEADERS", value = "xforwarded" },
        { name = "KC_HTTP_ENABLED", value = "true" },
        { name = "KC_PROXY", value = "edge" },
        { name = "KC_HOSTNAME", value = var.keycloak_hostname != "" ? var.keycloak_hostname : aws_lb.keycloak.dns_name },
      ]
      secrets = [
        { name = "KC_DB_USERNAME", valueFrom = "${aws_secretsmanager_secret.db.arn}:username::" },
        { name = "KC_DB_PASSWORD", valueFrom = "${aws_secretsmanager_secret.db.arn}:password::" },
        { name = "KEYCLOAK_ADMIN", valueFrom = "${aws_secretsmanager_secret.keycloak_admin.arn}:username::" },
        { name = "KEYCLOAK_ADMIN_PASSWORD", valueFrom = "${aws_secretsmanager_secret.keycloak_admin.arn}:password::" },
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.keycloak.name
          "awslogs-region"        = data.aws_region.current.region
          "awslogs-stream-prefix" = "keycloak"
        }
      }
    }
  ])

  tags = merge(var.tags, { Name = "${var.name_prefix}-keycloak-task" })
}

resource "aws_ecs_service" "keycloak" {
  name            = "${var.name_prefix}-keycloak"
  cluster         = aws_ecs_cluster.keycloak.id
  task_definition = aws_ecs_task_definition.keycloak.arn
  desired_count   = 2
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [aws_security_group.ecs.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.keycloak.arn
    container_name   = "keycloak"
    container_port   = 8080
  }

  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }

  depends_on = [aws_lb_listener.https, aws_lb_listener.http]
}

data "aws_region" "current" {}

resource "aws_cloudwatch_log_group" "keycloak" {
  name              = "/ecs/${var.name_prefix}-keycloak"
  retention_in_days = 30
  tags              = merge(var.tags, { Name = "${var.name_prefix}-keycloak-logs" })
}

data "aws_iam_policy_document" "ecs_execution_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "execution" {
  name               = "${var.name_prefix}-keycloak-execution"
  assume_role_policy = data.aws_iam_policy_document.ecs_execution_assume.json
  tags               = merge(var.tags, { Name = "${var.name_prefix}-keycloak-execution" })
}

data "aws_iam_policy_document" "execution" {
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
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]
    resources = ["${aws_cloudwatch_log_group.keycloak.arn}:*"]
  }
  statement {
    actions   = ["secretsmanager:GetSecretValue"]
    resources = [aws_secretsmanager_secret.db.arn, aws_secretsmanager_secret.keycloak_admin.arn]
  }
}

resource "aws_iam_role_policy" "execution" {
  name   = "${var.name_prefix}-keycloak-execution-policy"
  role   = aws_iam_role.execution.id
  policy = data.aws_iam_policy_document.execution.json
}

data "aws_iam_policy_document" "task_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "task" {
  name               = "${var.name_prefix}-keycloak-task"
  assume_role_policy = data.aws_iam_policy_document.task_assume.json
  tags               = merge(var.tags, { Name = "${var.name_prefix}-keycloak-task" })
}
