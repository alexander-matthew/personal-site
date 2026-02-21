terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# --- AMI Lookup ---

data "aws_ami" "amazon_linux_2023" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# --- Deployer IP (for SSH access) ---

data "http" "deployer_ip" {
  url = "https://checkip.amazonaws.com"
}

locals {
  deployer_ip = "${chomp(data.http.deployer_ip.response_body)}/32"
}

# --- Security Group ---

resource "aws_security_group" "personal_site" {
  name        = "personal-site-sg"
  description = "Security group for personal-site EC2 instance"

  ingress {
    description = "SSH from deployer"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [local.deployer_ip]
  }

  ingress {
    description = "HTTP (ACME challenges + redirect)"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# --- Key Pair ---

resource "aws_key_pair" "deployer" {
  key_name   = "personal-site-key"
  public_key = file(pathexpand(var.ssh_public_key_path))
}

# --- EC2 Instance ---

resource "aws_instance" "personal_site" {
  ami                    = data.aws_ami.amazon_linux_2023.id
  instance_type          = var.instance_type
  key_name               = aws_key_pair.deployer.key_name
  vpc_security_group_ids = [aws_security_group.personal_site.id]

  root_block_device {
    volume_size = 30
    volume_type = "gp3"
  }

  user_data = <<-EOF
    #!/bin/bash
    set -e

    # Install Docker
    dnf update -y
    dnf install -y docker git
    systemctl start docker
    systemctl enable docker
    usermod -aG docker ec2-user

    # Install Docker Compose plugin
    mkdir -p /usr/local/lib/docker/cli-plugins
    curl -SL https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64 \
      -o /usr/local/lib/docker/cli-plugins/docker-compose
    chmod +x /usr/local/lib/docker/cli-plugins/docker-compose

    # Install Buildx
    mkdir -p /home/ec2-user/.docker/cli-plugins
    BUILDX_VERSION=$(curl -s https://api.github.com/repos/docker/buildx/releases/latest | grep '"tag_name"' | cut -d'"' -f4)
    curl -SL "https://github.com/docker/buildx/releases/download/$${BUILDX_VERSION}/buildx-$${BUILDX_VERSION}.linux-amd64" \
      -o /home/ec2-user/.docker/cli-plugins/docker-buildx
    chmod +x /home/ec2-user/.docker/cli-plugins/docker-buildx
    chown -R ec2-user:ec2-user /home/ec2-user/.docker

    # Signal that bootstrap is complete
    touch /home/ec2-user/.bootstrap-complete
  EOF

  tags = {
    Name = "personal-site"
  }

  lifecycle {
    ignore_changes = [ami, user_data]
  }
}

# --- Elastic IP ---

resource "aws_eip" "this" {
  instance = aws_instance.personal_site.id
  domain   = "vpc"
}
