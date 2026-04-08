# Pulumi Lab 4 (Yandex Cloud)

Required config keys (set via `pulumi config set`):

- cloudId
- folderId
- serviceAccountKeyFile
- sshPublicKeyPath

Optional config keys:

- zone (default: ru-central1-a)
- subnetCidr (default: 10.10.0.0/24)
- imageFamily (default: ubuntu-2204-lts)
- namePrefix (default: lab4)
- sshUser (default: ubuntu)
- allowedSshCidr (default: 0.0.0.0/0)
