variable "region" {
  type    = string
  default = "ap-south-1" # Mumbai; closest to New Delhi
}

variable "instance_type" {
  type    = string
  default = "t3.micro"
}

variable "my_ip" {
  type        = string
  description = "Your public IP in CIDR form, e.g. 203.0.113.7/32. Restricts SSH and Grafana."
}

variable "public_key_path" {
  type    = string
  default = "~/.ssh/id_ed25519.pub"
}
