import os

import pulumi
import pulumi_yandex as yandex

config = pulumi.Config()

cloud_id = config.require("cloudId")
folder_id = config.require("folderId")
service_account_key_file = config.require("serviceAccountKeyFile")
zone = config.get("zone") or "ru-central1-a"
subnet_cidr = config.get("subnetCidr") or "10.10.0.0/24"
image_family = config.get("imageFamily") or "ubuntu-2204-lts"
name_prefix = config.get("namePrefix") or "lab4"
ssh_user = config.get("sshUser") or "ubuntu"
ssh_public_key_path = config.require("sshPublicKeyPath")
allowed_ssh_cidr = config.get("allowedSshCidr") or "0.0.0.0/0"

public_key_path = os.path.expanduser(ssh_public_key_path)
with open(public_key_path, "r", encoding="utf-8") as key_file:
    public_key = key_file.read().strip()

provider = yandex.Provider(
    "yc",
    service_account_key_file=service_account_key_file,
    cloud_id=cloud_id,
    folder_id=folder_id,
    zone=zone,
)

image = yandex.get_compute_image(family=image_family,
    opts=pulumi.InvokeOptions(provider=provider))

network = yandex.VpcNetwork(
    f"{name_prefix}-net",
    name=f"{name_prefix}-net",
    opts=pulumi.ResourceOptions(provider=provider),
)

subnet = yandex.VpcSubnet(
    f"{name_prefix}-subnet",
    name=f"{name_prefix}-subnet",
    zone=zone,
    network_id=network.id,
    v4_cidr_blocks=[subnet_cidr],
    opts=pulumi.ResourceOptions(provider=provider),
)

security_group = yandex.VpcSecurityGroup(
    f"{name_prefix}-sg",
    name=f"{name_prefix}-sg",
    network_id=network.id,
    ingresses=[
        yandex.VpcSecurityGroupIngressArgs(
            protocol="TCP",
            description="SSH",
            port=22,
            v4_cidr_blocks=[allowed_ssh_cidr],
        ),
        yandex.VpcSecurityGroupIngressArgs(
            protocol="TCP",
            description="HTTP",
            port=80,
            v4_cidr_blocks=["0.0.0.0/0"],
        ),
        yandex.VpcSecurityGroupIngressArgs(
            protocol="TCP",
            description="App",
            port=5000,
            v4_cidr_blocks=["0.0.0.0/0"],
        ),
    ],
    egresses=[
        yandex.VpcSecurityGroupEgressArgs(
            protocol="ANY",
            description="Allow all",
            v4_cidr_blocks=["0.0.0.0/0"],
        )
    ],
    opts=pulumi.ResourceOptions(provider=provider),
)

instance = yandex.ComputeInstance(
    f"{name_prefix}-vm",
    name=f"{name_prefix}-vm",
    platform_id="standard-v2",
    zone=zone,
    resources=yandex.ComputeInstanceResourcesArgs(
        cores=2,
        memory=1,
        core_fraction=20,
    ),
    boot_disk=yandex.ComputeInstanceBootDiskArgs(
        initialize_params=yandex.ComputeInstanceBootDiskInitializeParamsArgs(
            image_id=image.id,
            size=10,
            type="network-hdd",
        )
    ),
    network_interfaces=[
        yandex.ComputeInstanceNetworkInterfaceArgs(
            subnet_id=subnet.id,
            nat=True,
            security_group_ids=[security_group.id],
        )
    ],
    metadata={"ssh-keys": f"{ssh_user}:{public_key}"},
    labels={"project": "lab4", "managed_by": "pulumi"},
    opts=pulumi.ResourceOptions(provider=provider),
)

pulumi.export("public_ip", instance.network_interfaces[0].nat_ip_address)
pulumi.export("internal_ip", instance.network_interfaces[0].ip_address)
pulumi.export("ssh_command", pulumi.Output.concat("ssh ", ssh_user, "@", instance.network_interfaces[0].nat_ip_address))
