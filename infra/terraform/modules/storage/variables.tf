variable "environment" {
  type = string
}

variable "project" {
  type = string
}

variable "model_api_key_primary" {
  description = "In-region inference API key; must not be empty (fail closed)"
  type        = string
  sensitive   = true

  validation {
    condition     = length(var.model_api_key_primary) > 0
    error_message = "model_api_key_primary must be a non-empty value."
  }
}

variable "model_api_key_fallback" {
  description = "Domestic fallback API key; must not be empty (fail closed)"
  type        = string
  sensitive   = true

  validation {
    condition     = length(var.model_api_key_fallback) > 0
    error_message = "model_api_key_fallback must be a non-empty value."
  }
}

variable "tags" {
  type    = map(string)
  default = {}
}
