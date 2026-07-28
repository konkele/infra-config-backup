# infra-config-backup — Kubernetes

Kubernetes manifests for deploying `infra-config-backup` using Kustomize, Infisical, and a scheduled CronJob.

## Structure

```text
k8s/
├── base/
│   ├── configmap.yaml
│   ├── cronjob.yaml
│   ├── infisicalsecret.yaml
│   ├── kustomization.yaml
│   └── namespace.yaml
├── dev/
│   ├── configmap.yaml
│   ├── kustomization.yaml
│   ├── patch-cronjob.yaml
│   └── patch-infisicalsecret.yaml
└── README.md
```

## Design

The Kubernetes manifests follow a Kustomize base/overlay layout.

The `base/` directory contains the shared workload definition that is intended to be reused across environments, including:

- Namespace
- ConfigMap
- InfisicalSecret
- CronJob

Environment-specific behavior is implemented through overlays that patch or replace only the resources that differ.

The application is designed to execute as a short-lived Kubernetes `CronJob` rather than a continuously running deployment.

## Configuration

Application configuration is provided through a ConfigMap containing `config.yaml`.

Typical configuration includes:

- Git repository settings
- Commit author information
- SSH key locations
- Runtime options
- Provider definitions

Sensitive values should be referenced through environment variables, for example:

```yaml
${GIT_SSH_KEY}
${GIT_KNOWN_HOSTS}
${PFSENSE_USER}
${PFSENSE_PASS}
${TRUENAS_API_KEY}
${PORTAINER_API_KEY}
```

Secrets should never be committed directly into the ConfigMap.

## Secrets

Secrets are synchronized into Kubernetes using the Infisical Operator.

The `InfisicalSecret` resource creates and maintains a Kubernetes Secret containing all required credentials.

The CronJob consumes these secrets via `envFrom`, while Git SSH credentials are mounted as files for SSH-based repository authentication.

Typical secret categories include:

- Git SSH credentials
- Firewall credentials
- Storage platform API keys
- Infrastructure platform API keys

## Environments

### Base

The base manifests define the common deployment shared by every environment.

Responsibilities include:

- Namespace creation
- Default application configuration
- Secret synchronization
- CronJob definition
- Security context
- Volume mounts
- Secret mounting

### Development

The development overlay is intended for testing and validation.

It can customize:

- Application configuration
- Container image and tag
- Infisical environment
- CronJob schedule
- CronJob suspend state

This allows developers to run backups on a more frequent schedule or manually trigger Jobs without modifying the shared base manifests.

The development overlay should contain only environment-specific configuration and should avoid embedding organization-specific or sensitive information.

### Production

A production overlay can inherit the shared base configuration while overriding only the values required for production, such as:

- Image tag
- Secret environment
- Backup schedule
- Runtime configuration

## GitOps

The manifests are designed for GitOps workflows using Kustomize with tools such as Argo CD or Flux.

Typical deployment flow:

```text
            Overlay
               │
               ▼
          Kustomize Build
               │
               ▼
          Kubernetes API
               │
      ┌────────┴────────┐
      │                 │
      ▼                 ▼
 ConfigMap      InfisicalSecret
      │                 │
      └────────┬────────┘
               ▼
            CronJob
               │
               ▼
    infra-config-backup
```

## Overlay Responsibilities

As a general guideline:

**Base**

- Shared Kubernetes resources
- Default application configuration
- Security settings
- Secret integration
- Common CronJob definition

**Overlay**

- Environment-specific configuration
- Container image selection
- Scheduling changes
- Secret environment selection
- Runtime overrides

Keeping this separation minimizes duplication and makes new environments easy to add while ensuring shared infrastructure remains consistent.