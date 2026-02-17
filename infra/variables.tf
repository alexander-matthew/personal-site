variable "domain" {
  description = "Domain name for the personal site (e.g. yourdomain.com)"
  type        = string
}

variable "letsencrypt_email" {
  description = "Email address for Let's Encrypt certificate notifications"
  type        = string
}

variable "secret_key" {
  description = "Secret key for session signing (generate with: python -c \"import secrets; print(secrets.token_urlsafe(64))\")"
  type        = string
  sensitive   = true
}

variable "spotify_client_id" {
  description = "Spotify API client ID (from developer.spotify.com)"
  type        = string
  default     = ""
}

variable "spotify_client_secret" {
  description = "Spotify API client secret (from developer.spotify.com)"
  type        = string
  sensitive   = true
  default     = ""
}

variable "ssh_public_key_path" {
  description = "Path to your SSH public key (e.g. ~/.ssh/id_rsa.pub)"
  type        = string
  default     = "~/.ssh/id_rsa.pub"
}

variable "aws_region" {
  description = "AWS region to deploy in"
  type        = string
  default     = "us-east-2"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.micro"
}
