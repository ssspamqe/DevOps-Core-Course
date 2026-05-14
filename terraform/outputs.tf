output "public_ip" {
  description = "Public IP of the VM"
  value       = yandex_compute_instance.lab4.network_interface[0].nat_ip_address
}

output "internal_ip" {
  description = "Internal IP of the VM"
  value       = yandex_compute_instance.lab4.network_interface[0].ip_address
}

output "ssh_command" {
  description = "SSH command to access the VM"
  value       = "ssh ${var.ssh_user}@${yandex_compute_instance.lab4.network_interface[0].nat_ip_address}"
}
