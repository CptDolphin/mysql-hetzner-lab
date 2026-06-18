# Infrastruktura cx22 (Faza 2). `apply` = BRAMKA płatna — czeka na token Hetzner + GO.
# Storage Box (offsite backup) tworzony osobno (poza hcloud provider) — patrz docs/backup-and-recovery.md.

resource "hcloud_ssh_key" "admin" {
  name       = "mysql-lab-admin"
  public_key = var.ssh_public_key
}

# Firewall na brzegu sieci Hetznera (PRZED NIC): tylko 22/80/443 + ICMP. 3306 nigdy publicznie.
resource "hcloud_firewall" "main" {
  name = "mysql-lab-fw"

  dynamic "rule" {
    for_each = ["22", "80", "443"]
    content {
      direction  = "in"
      protocol   = "tcp"
      port       = rule.value
      source_ips = ["0.0.0.0/0", "::/0"]
    }
  }

  rule {
    direction  = "in"
    protocol   = "icmp"
    source_ips = ["0.0.0.0/0", "::/0"]
  }
}

resource "hcloud_server" "db" {
  name         = "mysql-lab-db-01"
  image        = "ubuntu-24.04"
  server_type  = var.server_type
  location     = var.location
  ssh_keys     = [hcloud_ssh_key.admin.id]
  firewall_ids = [hcloud_firewall.main.id]

  public_net {
    ipv4_enabled = true
    ipv6_enabled = true
  }

  labels = {
    project = "mysql-hetzner-lab"
    role    = "db"
  }
}

# Wolumen na /var/lib/mysql — dane przeżywają odtworzenie serwera. prevent_destroy = nie zgubić bazy.
resource "hcloud_volume" "mysql_data" {
  name      = "mysql-lab-data"
  size      = 20
  server_id = hcloud_server.db.id
  automount = false
  format    = "ext4"

  lifecycle {
    prevent_destroy = true
  }
}
