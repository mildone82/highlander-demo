variable "environment" {
  type = string
}

variable "project" {
  type = string
}

variable "ingestion_dlq_name" {
  type = string
}

variable "memory_dlq_name" {
  type = string
}

variable "tags" {
  type    = map(string)
  default = {}
}
