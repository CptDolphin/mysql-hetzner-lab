output "server_ipv4" {
  description = "Publiczny IPv4 serwera (do inventory Ansible)"
  value       = hcloud_server.db.ipv4_address
}

output "server_ipv6" {
  description = "Publiczny IPv6 serwera"
  value       = hcloud_server.db.ipv6_address
}

output "volume_device" {
  description = "Ścieżka urządzenia wolumenu danych MySQL (do montażu)"
  value       = hcloud_volume.mysql_data.linux_device
}
