output "alb_arn" {
  value = aws_lb.keycloak.arn
}

output "alb_dns_name" {
  value = aws_lb.keycloak.dns_name
}

output "db_endpoint" {
  value = aws_db_instance.keycloak.endpoint
}

output "db_secret_arn" {
  value = aws_secretsmanager_secret.db.arn
}

output "ecs_cluster_id" {
  value = aws_ecs_cluster.keycloak.id
}
