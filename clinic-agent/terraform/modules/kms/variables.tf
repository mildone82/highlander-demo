variable "name_prefix" {
  type = string
}

variable "tenants" {
  type = map(string)
}

variable "tags" {
  type    = map(string)
  default = {}
}
