# infra-config-backup — Kubernetes Templates

This directory contains a **public-safe Kubernetes template layer** for deploying `infra-config-backup`.

It is designed to be:

- Fully generic (no environment-specific values)
- Safe for public repositories
- Compatible with Kustomize / ArgoCD overlays
- Driven entirely by external configuration and secrets

---

## ⚙️ Design

This is a **base-only manifest layer**.

All environment-specific values should be injected externally using:

- Kustomize overlays
- CI/CD variable substitution
- ArgoCD Applications
- Infisical-managed Kubernetes Secrets

The manifests are intentionally generic so they can be reused across multiple environments without modification.

---

## 🔐 Secrets

Secrets are managed externally using the **Infisical Operator**.

This repository includes an `InfisicalSecret` resource that synchronizes secrets into a Kubernetes Secret consumed by the application.

No secret values are stored in this repository.

---

## 📦 Structure

The `base/` directory contains:

- `namespace.yaml` — application namespace
- `configmap.yaml` — application configuration template
- `deployment.yaml` — optional continuously running deployment
- `cronjob.yaml` — recommended scheduled backup execution
- `infisicalsecret.yaml` — Infisical secret synchronization
- `kustomization.yaml` — Kustomize entry point

---

## 🧪 Usage

### Kustomize

This directory is intended to be consumed through overlays:

```text
k8s/
├── base/
└── overlays/
    ├── dev/
    └── prod/
```

The base manifests should remain environment agnostic.

---

### Configuration

Application configuration is supplied through the ConfigMap.

Values such as repository locations, provider hosts, and image references are intended to be customized by overlays or deployment pipelines.

Examples include:

- `${IMAGE}`
- `${CRON_SCHEDULE}`
- `${INFISICAL_HOST}`
- `${INFISICAL_PROJECT}`
- `${INFISICAL_ENV}`
- `${INFISICAL_PATH}`
- `${INFISICAL_AUTH_SECRET}`
- `${INFISICAL_AUTH_NAMESPACE}`

Provider credentials are supplied through the synchronized Kubernetes Secret rather than the ConfigMap.

---

## 🚀 Execution

Two execution models are provided:

### CronJob (Recommended)

- Stateless execution
- Scheduled backups
- Automatically creates short-lived Pods
- Ideal for periodic infrastructure backups

### Deployment

- Continuously running container
- Useful for development, testing, or debugging
- Not typically required for production backup workflows

---

## 🔄 GitOps

The manifests are designed for GitOps workflows using tools such as:

- ArgoCD
- Kustomize
- Infisical Operator

Environment-specific customization should live in overlays or deployment repositories rather than this base.

---

## ⚠️ Security

This repository contains:

✔ No secrets  
✔ No credentials  
✔ No production infrastructure endpoints  
✔ No cluster-specific configuration  

It is safe to publish publicly.

---

## 📌 Summary

This Kubernetes directory provides a reusable, template-based deployment for **infra-config-backup** that integrates cleanly with GitOps workflows, external secret management, and environment-specific overlays while keeping the base manifests portable and safe for public repositories.