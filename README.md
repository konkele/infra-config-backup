# infra-config-backup

A template-driven infrastructure backup system designed for GitOps and
Kubernetes.

------------------------------------------------------------------------

## 📦 Project Structure

    ├── config
    │   └── config.example.yaml
    ├── k8s
    │   ├── base
    │   │   ├── configmap.yaml
    │   │   ├── cronjob.yaml
    │   │   ├── deployment.yaml
    │   │   ├── infisicalsecret.yaml
    │   │   ├── kustomization.yaml
    │   │   └── namespace.yaml
    │   └── README.md
    ├── src
    │   └── infra_config_backup
    │       ├── providers
    │       ├── config.py
    │       ├── engine.py
    │       ├── git.py
    │       ├── main.py
    │       └── models.py
    ├── Dockerfile
    ├── pyproject.toml
    └── README.md

------------------------------------------------------------------------

## 🚀 Overview

`infra-config-backup` collects configuration backups from infrastructure
systems and commits them to Git.

Key design goals:

-   Git-backed audit history
-   Kubernetes-native execution
-   Pluggable provider architecture
-   External secret injection (Infisical / ExternalSecrets)
-   Fully template-driven deployment

------------------------------------------------------------------------

## ☸️ Kubernetes Design

This repository provides a **public-safe base layer**:

-   No secrets
-   No environment-specific values
-   No real endpoints
-   Fully templated with `${VARIABLES}`

Deployment modes:

- CronJob (recommended)
- Deployment (optional long-running mode)

------------------------------------------------------------------------

## 🔐 Secrets Model

All secrets must be injected externally:

-   Infisical
-   ExternalSecrets Operator
-   CSI Secret Store

This repo only defines *how secrets are consumed*, not stored.

------------------------------------------------------------------------

### 🗂️ Git Configuration

The application stores all backup artifacts in a Git repository.

```yaml
git:
  repo: git@github.com:YOUR_ORG/infra-backups.git
  branch: main

  author:
    name: infra-backup
    email: infra@example.com

  # Optional SSH configuration
  # If omitted, the local user's standard ~/.ssh configuration is used.
  ssh_key: /etc/git-ssh/id_ed25519
  known_hosts: /etc/git-ssh/known_hosts
```

| Setting | Required | Description |
|----------|----------|-------------|
| `repo` | Yes | Git repository to clone and push backups to. HTTPS repositories are supported by Git, but SSH repositories (git@...) are recommended for unattended automation. |
| `branch` | No | Target branch. Defaults to `main`. |
| `author.name` | No | Git commit author name. |
| `author.email` | No | Git commit author email. |
| `ssh_key` | No | Path to a private SSH deploy key. When omitted, Git uses the standard local SSH configuration (`~/.ssh`). |
| `known_hosts` | No | Optional OpenSSH `known_hosts` file. If omitted, the system default is used. |

------------------------------------------------------------------------

## 🔑 Git Authentication

The application supports two authentication modes.

### 💻 Local Development

No additional configuration is required.

If `git.ssh_key` is not configured, Git behaves exactly as it normally would and uses the current user's SSH configuration, including:

- `~/.ssh/id_ed25519`
- `~/.ssh/config`
- `~/.ssh/known_hosts`
- SSH agent authentication

This makes local development simple and requires no Kubernetes-specific configuration.

### ☸️ Kubernetes / GitOps

For Kubernetes deployments, it is recommended to mount an SSH deploy key as a Secret.

Example:

```
/etc/git-ssh/
├── id_ed25519
└── known_hosts
```

Then configure:

```yaml
git:
  ssh_key: /etc/git-ssh/id_ed25519
  known_hosts: /etc/git-ssh/known_hosts
```

The application automatically configures Git to use the mounted key for clone and push operations.

------------------------------------------------------------------------

## 🔒 Using Infisical for Git Deploy Keys

A common deployment pattern is to store the Git deploy key in Infisical.

Example secrets:

| Secret | Description |
|--------|-------------|
| `GIT_SSH_KEY` | Private SSH deploy key used to access the backup repository. |
| `GIT_KNOWN_HOSTS` | Optional OpenSSH `known_hosts` file. |

Mount these secrets into the container as read-only files, for example:

```
/etc/git-ssh/id_ed25519
/etc/git-ssh/known_hosts
```

and configure the application:

```yaml
git:
  ssh_key: /etc/git-ssh/id_ed25519
  known_hosts: /etc/git-ssh/known_hosts
```

If these options are omitted, the application falls back to the standard SSH configuration available to the current user.

------------------------------------------------------------------------

## 🧪 Usage

### 💻 Local

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the project in editable mode:

```bash
pip install -e .
```

Create a configuration file:

```bash
cp config/config.example.yaml config/config.yaml
```

Export the environment variables referenced by the configuration (API keys, passwords, Git settings, etc.), then run the application:

```bash
export CONFIG_FILE=config/config.yaml

infra-config-backup
```

### ☸️ Kubernetes

The repository includes a reusable Kubernetes base along with environment-specific overlays.

```
k8s/
├── base
├── dev
└── prod
```

The recommended deployment model is:

- Base manifests committed to Git
- Environment-specific customization with Kustomize
- Secrets injected by Infisical (or another external secret provider)
- Configuration provided through a ConfigMap

------------------------------------------------------------------------

## 🗄️ Backup Layout

Backups are organized by provider type. Each provider instance produces a backup artifact and a corresponding metadata file.

```text
infra-backups/
├── pfsense
│   ├── primary-backup.xml
│   └── primary-metadata.json
├── portainer
│   ├── main-backup.tar.gz
│   └── main-metadata.json
├── truenas
│   ├── primary-backup.tar
│   └── primary-metadata.json
└── unifi
    ├── controller-backup.unf
    └── controller-metadata.json
```

------------------------------------------------------------------------

## 📄 Metadata Files

Every provider generates a metadata file alongside its backup.

Metadata includes information such as:

- Provider name
- Instance name
- Backup filename
- Backup size
- Content hash
- Modification timestamp
- Backup creation timestamp

These files allow backup verification without needing to inspect the backup artifact itself.

------------------------------------------------------------------------

## ⚙️ Configuration

The application is configured using a YAML configuration file.

Configuration is intentionally split into two categories:

- **Configuration** (repository URLs, hostnames, provider names, Git author, feature flags, timeouts) should live in the ConfigMap.
- **Secrets** (passwords, API keys, SSH deploy keys, bearer tokens) should be injected from Infisical or another external secret provider.

String values of the form `${VARIABLE}` are automatically expanded from the process environment before providers are initialized.

Supported providers:

- pfSense
- Portainer
- TrueNAS
- UniFi

Each provider writes a deterministic backup filename along with a corresponding metadata file describing the backup.

------------------------------------------------------------------------

## 📌 Philosophy

- Stateless execution
- Immutable provider results
- Externalized configuration
- Deterministic backups
- Git as the source of truth
