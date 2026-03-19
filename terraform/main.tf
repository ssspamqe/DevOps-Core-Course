provider "yandex" {
  service_account_key_file = var.service_account_key_file
  cloud_id                 = var.cloud_id
  folder_id                = var.folder_id
  zone                     = "ru-central1-a"
}


data "yandex_compute_image" "ubuntu" {
  family = var.image_family
}

resource "yandex_vpc_network" "lab4" {
  name = "${var.name_prefix}-net"
}

resource "yandex_vpc_subnet" "lab4" {
  name           = "${var.name_prefix}-subnet"
  zone           = var.zone
  network_id     = yandex_vpc_network.lab4.id
  v4_cidr_blocks = [var.subnet_cidr]
}

resource "yandex_vpc_security_group" "lab4" {
  name       = "${var.name_prefix}-sg"
  network_id = yandex_vpc_network.lab4.id

  ingress {
    protocol       = "TCP"
    description    = "SSH"
    port           = 22
    v4_cidr_blocks = [var.allowed_ssh_cidr]
  }

  ingress {
    protocol       = "TCP"
    description    = "HTTP"
    port           = 80
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    protocol       = "TCP"
    description    = "App"
    port           = 5000
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    protocol       = "ANY"
    description    = "Allow all"
    v4_cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "yandex_compute_instance" "lab4" {
  name        = "${var.name_prefix}-vm"
  platform_id = "standard-v2"
  zone        = var.zone

  resources {
    cores         = 2
    memory        = 1
    core_fraction = 20
  }

  boot_disk {
    initialize_params {
      image_id = data.yandex_compute_image.ubuntu.id
      size     = 10
      type     = "network-hdd"
    }
  }

  network_interface {
    subnet_id          = yandex_vpc_subnet.lab4.id
    nat                = true
    security_group_ids = [yandex_vpc_security_group.lab4.id]
  }

  metadata = {
    "ssh-keys" = "${var.ssh_user}:${file(var.ssh_public_key_path)}"
  }

  labels = {
    project    = "lab4"
    managed_by = "terraform"
  }
}
