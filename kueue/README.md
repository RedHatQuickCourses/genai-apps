# Kueue Lab Files

Lab resource files for the [GPU Quota Management with Kueue on Red Hat OpenShift AI](https://redhatquickcourses.github.io/kueue) course.

## Directory Structure

```
kueue/
├── helm-charts/          # Helm charts for operator installation
│   ├── kueue/            # Red Hat Build of Kueue operator
│   ├── rhoai-3.4/        # Red Hat OpenShift AI 3.4 + dependencies
│   └── fake-gpu-operator/# Fake GPU Operator values for OpenShift
├── kueue-config/         # Kueue resource manifests (applied in order)
│   ├── 1-namespaces.yaml
│   ├── 2-resource-flavors.yaml
│   ├── 3-cluster-queues.yaml
│   ├── 4-local-queues.yaml
│   ├── 5-workload-priority-classes.yaml
│   ├── 6-6b: MIG configuration
│   ├── 7-8: MIG ClusterQueue and LocalQueue
│   ├── 9-9a: Cohort borrowing and reclaim
│   ├── 10-10a: Fair sharing
│   └── 11-12: RBAC bindings
├── workloads/            # Kubernetes workload manifests for lab exercises
│   ├── job-*.yaml        # Training Jobs (FIFO, priority, MIG, fair sharing)
│   ├── deployment-*.yaml # Inference Deployments (cohort borrowing, workloads)
│   └── pod-gpu-test.yaml # GPU verification pod
└── scripts/              # Utility scripts
    ├── cluster-reset.sh  # Remove all lab resources (10-phase cleanup)
    └── verify-lab-env.sh # Verify cluster readiness (15 checks)
```

## Usage

These files are used from the course labs. Clone this repo and work from the `kueue/` directory:

```bash
git clone https://github.com/RedHatQuickCourses/genai-apps.git
cd genai-apps/kueue
```

All commands in the course reference files with relative paths (e.g., `oc apply -f kueue-config/1-namespaces.yaml`).

## Prerequisites

- OpenShift 4.17+ cluster with 2 dedicated worker nodes
- Cluster admin access (`oc` CLI)
- Helm 3.x
- No real NVIDIA GPUs or GPU Operator installed (the course uses the Fake GPU Operator)
