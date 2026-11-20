output "public_ip" {
  value = aws_eip.app.public_ip
}

output "domain_nip_io" {
  description = "Free HTTPS hostname if you have no domain"
  value       = "${replace(aws_eip.app.public_ip, ".", "-")}.nip.io"
}

output "ssh" {
  value = "ssh ubuntu@${aws_eip.app.public_ip}"
}
