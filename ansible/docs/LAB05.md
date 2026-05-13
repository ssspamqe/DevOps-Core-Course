# Lab 5 — Ansible Fundamentals

## 1. Architecture Overview

- **Ansible version:** core 2.20.3
- **Target VM OS:** Ubuntu (Linux 5.15.0, x86_64), Yandex Cloud
- **Python on control node:** 3.14.3

### Role Structure

```
ansible/
├── ansible.cfg                    # Global config (inventory path, vault, become)
├── .vault_pass                    # Vault password file (gitignored)
├── inventory/
│   ├── hosts.ini                  # Static inventory with VM details
│   └── group_vars/
│       └── all.yml                # Encrypted credentials (Ansible Vault)
├── roles/
│   ├── common/                    # Basic system setup
│   │   ├── tasks/main.yml
│   │   └── defaults/main.yml
│   ├── docker/                    # Docker CE installation
│   │   ├── tasks/main.yml
│   │   ├── handlers/main.yml
│   │   └── defaults/main.yml
│   └── app_deploy/                # Application deployment
│       ├── tasks/main.yml
│       ├── handlers/main.yml
│       └── defaults/main.yml
└── playbooks/
    ├── site.yml                   # Full provision + deploy
    ├── provision.yml              # System provisioning only
    └── deploy.yml                 # App deployment only
```

### Why Roles Instead of Monolithic Playbooks?

Roles split logic into reusable, testable units. Each role has a single responsibility (e.g., install Docker), can be shared across projects via Ansible Galaxy, and keeps playbooks clean — the playbook only lists which roles to apply, while all implementation details live inside the roles.

---

## 2. Roles Documentation

### common

- **Purpose:** Update apt cache, install essential system packages, set timezone.
- **Variables:**
  - `common_packages` — list of packages to install (python3-pip, curl, git, vim, htop, wget, etc.)
  - `timezone` — system timezone (default: `UTC`)
- **Handlers:** None
- **Dependencies:** None

### docker

- **Purpose:** Install Docker CE from the official Docker repository on Ubuntu.
- **Variables:**
  - `docker_user` — user to add to the docker group (default: `ubuntu`)
  - `docker_packages` — list of Docker packages (docker-ce, docker-ce-cli, containerd.io, etc.)
- **Handlers:**
  - `restart docker` — restarts the Docker service; triggered when Docker packages are installed/updated.
- **Dependencies:** None (but runs after `common` in the provisioning playbook)

### app_deploy

- **Purpose:** Pull and run the containerized Python app from Docker Hub using Vault-encrypted credentials.
- **Variables:**
  - `app_port` — exposed port (default: `8080`)
  - `app_restart_policy` — Docker restart policy (default: `unless-stopped`)
  - `app_env` — environment variables passed to the container
  - Vault variables: `dockerhub_username`, `dockerhub_password`, `docker_image`, `docker_image_tag`, `app_container_name`
- **Handlers:**
  - `restart app container` — restarts the application container.
- **Dependencies:** Requires Docker to be installed (docker role).

---

## 3. Idempotency Demonstration

### First Run (`ansible-playbook playbooks/provision.yml`)

```
PLAY [Provision web servers] ****************************************************

TASK [Gathering Facts] **********************************************************
ok: [vm1]

TASK [common : Update apt cache] ************************************************
ok: [vm1]

TASK [common : Install common packages] *****************************************
changed: [vm1]

TASK [common : Set timezone] ****************************************************
changed: [vm1]

TASK [docker : Install required packages for Docker repository] *****************
ok: [vm1]

TASK [docker : Create keyrings directory] ***************************************
ok: [vm1]

TASK [docker : Add Docker GPG key] **********************************************
changed: [vm1]

TASK [docker : Get architecture] ************************************************
ok: [vm1]

TASK [docker : Add Docker repository] *******************************************
changed: [vm1]

TASK [docker : Install Docker packages] *****************************************
changed: [vm1]

TASK [docker : Ensure Docker service is running and enabled] ********************
ok: [vm1]

TASK [docker : Add user to docker group] ****************************************
changed: [vm1]

TASK [docker : Install python3-docker for Ansible docker modules] ***************
changed: [vm1]

RUNNING HANDLER [docker : restart docker] ***************************************
changed: [vm1]

PLAY RECAP **********************************************************************
vm1                        : ok=14   changed=8    unreachable=0    failed=0
```

**Analysis:** 8 tasks changed — packages installed, Docker GPG key added, Docker repo added, Docker installed, user added to docker group, timezone set, and Docker restarted via handler.

### Second Run (Idempotency)

```
PLAY [Provision web servers] ****************************************************

TASK [Gathering Facts] **********************************************************
ok: [vm1]

TASK [common : Update apt cache] ************************************************
ok: [vm1]

TASK [common : Install common packages] *****************************************
ok: [vm1]

TASK [common : Set timezone] ****************************************************
ok: [vm1]

TASK [docker : Install required packages for Docker repository] *****************
ok: [vm1]

TASK [docker : Create keyrings directory] ***************************************
ok: [vm1]

TASK [docker : Add Docker GPG key] **********************************************
ok: [vm1]

TASK [docker : Get architecture] ************************************************
ok: [vm1]

TASK [docker : Add Docker repository] *******************************************
ok: [vm1]

TASK [docker : Install Docker packages] *****************************************
ok: [vm1]

TASK [docker : Ensure Docker service is running and enabled] ********************
ok: [vm1]

TASK [docker : Add user to docker group] ****************************************
ok: [vm1]

TASK [docker : Install python3-docker for Ansible docker modules] ***************
ok: [vm1]

PLAY RECAP **********************************************************************
vm1                        : ok=13   changed=0    unreachable=0    failed=0
```

**Analysis:** `changed=0` — all tasks returned "ok" (green). The desired state was already achieved, so no modifications were made. The handler did not run because no task triggered it. This proves **idempotency**: running the playbook multiple times produces the same result without unintended side effects.

### What Makes Roles Idempotent?

- Using `apt: state=present` installs packages only if missing.
- Using `service: state=started, enabled=yes` only acts if the service isn't already running/enabled.
- Using `get_url: force=false` skips download if file exists.
- Using `apt_repository: state=present` only adds if not already there.
- Using `user: groups=docker, append=yes` is a no-op if user already in the group.

---

## 4. Ansible Vault Usage

### How Credentials Are Stored

Sensitive data (Docker Hub credentials, app config) is stored in `inventory/group_vars/all.yml`, encrypted with Ansible Vault using AES256.

### Vault Password Management

A `.vault_pass` file contains the vault password and is:
- Referenced in `ansible.cfg` via `vault_password_file = .vault_pass`
- Added to `.gitignore` to prevent committing
- Has permissions `600` (owner-only read/write)

### Encrypted File Contents

```
$ head -3 inventory/group_vars/all.yml
$ANSIBLE_VAULT;1.1;AES256
61626364656667...  (encrypted blob)
```

The file is safe to commit — it cannot be decrypted without the vault password.

### Why Ansible Vault Is Important

- Prevents credentials from being exposed in version control
- Allows secrets to coexist with code in the same repo safely
- Uses strong AES256 encryption
- Integrates seamlessly into Ansible workflows — no external tools needed

---

## 5. Deployment Verification

### Deploy Run (`ansible-playbook playbooks/deploy.yml`)

```
PLAY [Deploy application] *******************************************************

TASK [Gathering Facts] **********************************************************
ok: [vm1]

TASK [app_deploy : Log in to Docker Hub] ****************************************
changed: [vm1]

TASK [app_deploy : Pull Docker image] *******************************************
changed: [vm1]

TASK [app_deploy : Stop and remove existing container] **************************
ok: [vm1]

TASK [app_deploy : Run application container] ***********************************
changed: [vm1]

TASK [app_deploy : Wait for application to be ready] ****************************
ok: [vm1]

TASK [app_deploy : Verify health endpoint] **************************************
ok: [vm1]

TASK [app_deploy : Display health check result] *********************************
ok: [vm1] => {
    "health_check.json": {
        "status": "healthy",
        "timestamp": "2026-02-25T18:19:56.757106+00:00",
        "uptime_seconds": 10
    }
}

RUNNING HANDLER [app_deploy : restart app container] ****************************
changed: [vm1]

PLAY RECAP **********************************************************************
vm1                        : ok=9    changed=4    unreachable=0    failed=0
```

### Container Status

```
$ ansible webservers -a "docker ps"
CONTAINER ID   IMAGE                                 COMMAND                  CREATED        STATUS        PORTS                    NAMES
ce1bd49f910a   ssspamqe/devops-info-service:latest   "gunicorn --bind 0.0…"   54 seconds ago Up 37 seconds 0.0.0.0:8080->8080/tcp   devops-info-service
```

### Health Check (from VM)

```
$ ansible webservers -a "curl -s http://localhost:8080/health"
{"status":"healthy","timestamp":"2026-02-25T18:25:21.312372+00:00","uptime_seconds":318}
```

### Handler Execution

The `restart app container` handler was triggered by the "Run application container" task (since a new container was created, it notified the handler).

---

## 6. Key Decisions

- **Why use roles instead of plain playbooks?**
  Roles provide a standardized directory structure for organizing tasks, handlers, defaults, and files. This makes the code modular, reusable across projects, and easier to test/maintain independently.

- **How do roles improve reusability?**
  A role like `docker` can be used in any project that needs Docker. Variables in `defaults/` allow customization without modifying the role itself. Roles can also be shared via Ansible Galaxy.

- **What makes a task idempotent?**
  Using Ansible's declarative modules (e.g., `apt: state=present`) that check current state before acting. They only make changes when the desired state differs from the actual state.

- **How do handlers improve efficiency?**
  Handlers run only when notified and only once at the end of a play, even if notified multiple times. This avoids unnecessary service restarts — e.g., Docker is restarted once after all config changes, not after each individual task.

- **Why is Ansible Vault necessary?**
  Secrets like Docker Hub tokens must be stored somewhere for automation, but plain text in a repo is a security risk. Vault encrypts them in-place so they travel safely with the codebase while remaining usable by authorized operators.

---

## 7. Challenges

- **Vault password mismatch in interactive terminal:** Typing passwords in the terminal prompt was unreliable. Solved by using a `.vault_pass` file referenced in `ansible.cfg`.
- **group_vars path:** Ansible looks for `group_vars` relative to the inventory directory, not the project root. Moved `group_vars/` inside `inventory/` to fix variable loading.
- **Deprecation warning:** `ansible_distribution_release` as a top-level fact is deprecated; switched to `ansible_facts['distribution_release']`.
- **External access:** The app health check works from within the VM but external curl gets empty replies — this is a cloud security group/firewall issue, not an Ansible problem.
