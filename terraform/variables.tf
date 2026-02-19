variable "cloud_id" {
  type        = string
  description = "Yandex Cloud ID"
}

variable "folder_id" {
  type        = string
  description = "Yandex Cloud Folder ID"
}

variable "service_account_key_file" {
  type        = string
  description = "Path to service account key JSON"
}

variable "zone" {
  type        = string
  description = "Yandex Cloud zone"
  default     = "ru-central1-a"
}

variable "subnet_cidr" {
  type        = string
  description = "CIDR for subnet"
  default     = "10.10.0.0/24"
}

variable "image_family" {
  type        = string
  description = "Compute image family"
  default     = "ubuntu-2204-lts"
}

variable "name_prefix" {
  type        = string
  description = "Name prefix for resources"
  default     = "lab4"
}

variable "ssh_user" {
  type        = string
  description = "SSH username"
  default     = "ubuntu"
}

variable "ssh_public_key_path" {
  type        = string
  description = "Path to SSH public key file"
}

variable "allowed_ssh_cidr" {
  type        = string
  description = "CIDR allowed to access SSH"
  default     = "0.0.0.0/0"
}
