# infra-config-backup — Kubernetes

Kubernetes manifests for deploying `infra-config-backup` using Kustomize, Infisical, and a scheduled CronJob.

## Structure

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
│   └── patch-infisicalsecret.yaml
└── README.md

## Design

The `base/` manifests define the common Kubernetes resources:

- Namespace
- ConfigMap
- CronJob
- InfisicalSecret

Environment-specific configuration is provided through Kustomize overlays.

The application runs as a short-lived CronJob rather than a continuously running service.

## Configuration

Application configuration is stored in a ConfigMap.

Sensitive values are referenced using environment variables such as:

${GIT_SSH_KEY}
${GIT_KNOWN_HOSTS}
${PFSENSE_FIREWALL_USERNAME}
${PFSENSE_FIREWALL_PASSWORD}

Secrets are not stored directly in the ConfigMap.

## Secrets

Secrets are managed by the Infisical Operator.

The `InfisicalSecret` resource synchronizes the configured Infisical environment into a Kubernetes Secret. The CronJob consumes that Secret through `envFrom`.

This includes Git SSH credentials and provider credentials.

## Environments

### Dev

The development overlay is intended for integration and provider testing.

It can override:

- Application configuration
- Container image
- Infisical environment
- CronJob behavior

Development execution can be triggered manually while the scheduled CronJob remains suspended.

### Prod

The production overlay is intended for scheduled backups.

It inherits the common CronJob configuration and enables scheduled execution.

## GitOps

The manifests are designed to work with Kustomize and GitOps tooling such as ArgoCD.

A typical deployment flow is:

Kustomize Overlay
       │
       ▼
   Kubernetes
       │
       ├── ConfigMap
       ├── InfisicalSecret
       └── CronJob
               │
               ▼
        infra-config-backup

Environment-specific values should remain in their respective overlays, while shared workload configuration belongs in `base/`.