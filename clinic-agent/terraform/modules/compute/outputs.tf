output "api_handler_function_name" {
  value = aws_lambda_function.api_handler.function_name
}

output "api_handler_function_arn" {
  value = aws_lambda_function.api_handler.arn
}

output "api_handler_invoke_arn" {
  value = aws_lambda_function.api_handler.invoke_arn
}

output "model_gateway_function_name" {
  value = aws_lambda_function.model_gateway.function_name
}

output "report_generator_function_name" {
  value = aws_lambda_function.report_generator.function_name
}

output "report_generator_function_arn" {
  value = aws_lambda_function.report_generator.arn
}

output "ingest_function_name" {
  value = aws_lambda_function.ingest.function_name
}

output "sagemaker_endpoint_name" {
  value = aws_sagemaker_endpoint.embedding.name
}

output "agentcore_runtime_id" {
  value = aws_bedrockagentcore_agent_runtime.main.agent_runtime_id
}

output "agentcore_runtime_arn" {
  value = aws_bedrockagentcore_agent_runtime.main.agent_runtime_arn
}

output "agent_ecr_repository_url" {
  value = aws_ecr_repository.agent.repository_url
}
