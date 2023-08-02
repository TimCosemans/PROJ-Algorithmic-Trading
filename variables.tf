variable "AZ_RESOURCE_GROUP" {
  description = "Name of the resource group"
  type        = string
  sensitive = true
}
variable "AZ_RESOURCE_GROUP_LOCATION" {
  description = "Location of the resource group"
  type        = string
  sensitive = true
}
variable "AZ_SUBSCRIPTION_ID" {
  description = "Subscription ID"
  type        = string
  sensitive = true
}

variable "AZ_CLIENT_ID" {
  description = "Client ID of Azure Service Principal"
  type        = string
  sensitive = true
}
variable "AZ_CLIENT_SECRET" {
  description = "Client Secret of Azure Service Principal"
  type        = string
  sensitive = true
}
variable "AZ_TENANT_ID" {
  description = "Tenant ID of Azure Service Principal"
  type        = string
  sensitive = true
}