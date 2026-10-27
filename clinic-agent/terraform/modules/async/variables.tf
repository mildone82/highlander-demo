variable "name_prefix" {
  type = string
}

variable "report_generator_arn" {
  type = string
}

variable "report_generator_name" {
  type = string
}

variable "tags" {
  type    = map(string)
  default = {}
}
