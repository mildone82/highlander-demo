output "rest_api_id" {
  value = aws_api_gateway_rest_api.main.id
}

output "invoke_url" {
  value = aws_api_gateway_stage.main.invoke_url
}

output "authorizer_function_name" {
  value = aws_lambda_function.authorizer.function_name
}
