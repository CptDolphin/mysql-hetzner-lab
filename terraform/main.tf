# Zasoby infrastruktury powstają w Fazie 2 (TASKS.md). `apply` to BRAMKA płatna — czeka na GO.
# Szkielet docelowy: serwer cx22 (Ubuntu 24.04) + Hetzner Firewall (22/80/443) + Volume na
# /var/lib/mysql (prevent_destroy) + Storage Box (offsite). Odkomentowujemy wraz z Fazą 2.

# resource "hcloud_ssh_key" "admin" {
#   name       = "mysql-lab-admin"
#   public_key = var.ssh_public_key
# }

# resource "hcloud_server" "db" {
#   name        = "mysql-lab-db-01"
#   image       = "ubuntu-24.04"
#   server_type = var.server_type
#   location    = var.location
#   ssh_keys    = [hcloud_ssh_key.admin.id]
# }

# resource "hcloud_firewall" "db" {
#   name = "mysql-lab-fw"
#   # allow 22/80/443; reszta deny. 3306 NIGDY publicznie.
# }

# resource "hcloud_volume" "mysql_data" {
#   name      = "mysql-lab-data"
#   size      = 20
#   server_id = hcloud_server.db.id
#   lifecycle {
#     prevent_destroy = true
#   }
# }
