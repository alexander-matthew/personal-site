output "elastic_ip" {
  description = "Elastic IP address — point your domain's DNS A record here"
  value       = aws_eip.this.public_ip
}

output "ssh_command" {
  description = "SSH command to connect to the instance"
  value       = "ssh -i ${replace(var.ssh_public_key_path, ".pub", "")} ec2-user@${aws_eip.this.public_ip}"
}

output "next_steps" {
  description = "What to do after terraform apply"
  value       = <<-EOT
    1. Set your DNS: create an A record for ${var.domain} → ${aws_eip.this.public_ip}
       (If using Cloudflare, set to "DNS only" / gray cloud — do not proxy)
    2. Wait for DNS propagation (usually 1-5 minutes)
    3. Run: ./deploy.sh
  EOT
}
