variable "hcloud_token" {
  description = "Hetzner Cloud API token (z CI/sekretu — nigdy w repo)"
  type        = string
  sensitive   = true
}

variable "server_type" {
  description = "Typ serwera Hetzner (cx22 = 2 vCPU / 4 GB)"
  type        = string
  default     = "cx22"
}

variable "location" {
  description = "Lokalizacja Hetzner (nbg1 / fsn1 / hel1)"
  type        = string
  default     = "nbg1"
}

variable "ssh_public_key" {
  description = "Publiczny klucz SSH admina"
  type        = string
}
