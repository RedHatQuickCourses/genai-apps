#!/usr/bin/env bash
#
# cluster-reset.sh — Reset the cluster to pre-lab state.
#
# What this script removes:
#   - GPU taints and labels on worker nodes
#   - Workloads (Jobs, Deployments) in lab namespaces
#   - RBAC bindings created by the course
#   - Kueue custom resources (LocalQueues, ClusterQueues, ResourceFlavors, etc.)
#   - MIG annotations and labels
#   - Helm releases: kueue, gpu-operator, rhoai-operators
#   - Lab namespaces: training-jobs, inference-apps, team-b-jobs
#
# What this script does NOT touch:
#   - CSVs, Subscriptions, or OperatorGroups (let OLM handle those)
#   - RHOAI namespaces (removed by the operator when its Subscription is gone)
#   - Any platform-level dependencies (NFD, Serverless, Pipelines, etc.)
#
# Idempotent — safe to run at any point in the course.
#
# Usage:
#   bash scripts/cluster-reset.sh
#

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

info()  { echo -e "${CYAN}[INFO]${NC}  $*"; }
ok()    { echo -e "${GREEN}[ OK ]${NC}  $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
step()  { echo -e "\n${BOLD}${CYAN}━━━ $* ━━━${NC}"; }

###############################################################################
# PRE-FLIGHT
###############################################################################

step "Pre-flight checks"

if ! oc whoami --request-timeout=10s &>/dev/null; then
  echo -e "${RED}Not logged in or cluster unreachable. Run 'oc login' first.${NC}"
  exit 1
fi
ok "Logged in as $(oc whoami)"

if ! oc get nodes --request-timeout=10s &>/dev/null; then
  echo -e "${RED}Cannot reach cluster API. Check your connection and try again.${NC}"
  exit 1
fi
ok "Cluster API reachable"

# Auto-detect worker nodes
WORKERS=()
while IFS= read -r node; do
  [[ -n "$node" ]] && WORKERS+=("$node")
done < <(oc get nodes -l node-role.kubernetes.io/worker \
  --no-headers -o custom-columns=NAME:.metadata.name 2>/dev/null \
  | grep -v control-plane | head -2)

if [[ ${#WORKERS[@]} -gt 0 ]]; then
  ok "Workers: ${WORKERS[*]}"
else
  warn "No worker nodes found — node cleanup will be skipped"
fi

###############################################################################
# 1 — Remove GPU taints (do this first to prevent scheduling cascade)
###############################################################################

step "1. Remove GPU taints"

for node in "${WORKERS[@]}"; do
  oc adm taint nodes "$node" nvidia.com/gpu=present:NoSchedule- 2>/dev/null \
    && ok "Removed taint from $node" \
    || ok "No taint on $node"
done

###############################################################################
# 2 — Delete workloads in lab namespaces
###############################################################################

step "2. Delete workloads"

for ns in training-jobs inference-apps team-b-jobs; do
  if oc get ns "$ns" &>/dev/null; then
    oc delete jobs --all -n "$ns" --ignore-not-found --timeout=30s 2>/dev/null || true
    oc delete deployments --all -n "$ns" --ignore-not-found --timeout=30s 2>/dev/null || true
    ok "Cleaned $ns"
  else
    ok "$ns not found (skipping)"
  fi
done

###############################################################################
# 3 — Delete RBAC bindings
###############################################################################

step "3. Delete RBAC bindings"

oc delete clusterrolebinding kueue-batch-admin-binding --ignore-not-found 2>/dev/null || true
for rb in kueue-admin-edit kueue-batch-user-binding kueue-user-edit; do
  oc delete rolebinding "$rb" -n training-jobs --ignore-not-found 2>/dev/null || true
done
ok "RBAC bindings removed"

###############################################################################
# 4 — Delete Kueue custom resources
###############################################################################

step "4. Delete Kueue resources"

if oc api-resources --api-group=kueue.x-k8s.io &>/dev/null 2>&1 \
   && oc api-resources --api-group=kueue.x-k8s.io --no-headers 2>/dev/null | grep -q .; then
  for ns in training-jobs inference-apps team-b-jobs; do
    oc delete localqueues --all -n "$ns" --ignore-not-found --timeout=30s 2>/dev/null || true
  done
  oc delete clusterqueue --all --ignore-not-found --timeout=30s 2>/dev/null || true
  oc delete resourceflavor --all --ignore-not-found --timeout=30s 2>/dev/null || true
  oc delete workloadpriorityclasses --all --ignore-not-found --timeout=30s 2>/dev/null || true
  ok "Kueue resources deleted"
else
  ok "Kueue CRDs not present (skipping)"
fi

###############################################################################
# 5 — Undo MIG configuration
###############################################################################

step "5. Undo MIG configuration"

if [[ ${#WORKERS[@]} -gt 0 ]]; then
  node="${WORKERS[0]}"
  oc annotate node "$node" run.ai/mig.config- run.ai/mig-mapping- &>/dev/null || true
  oc label node "$node" \
    node-role.kubernetes.io/runai-dynamic-mig- \
    node-role.kubernetes.io/runai-mig-enabled- \
    nvidia.com/mig.config.state- &>/dev/null || true
  ok "MIG config removed from $node"
fi

###############################################################################
# 6 — Helm uninstall (the only operator removal we do)
###############################################################################

step "6. Helm uninstall"

helm uninstall kueue -n default --timeout=60s 2>/dev/null \
  && ok "Uninstalled kueue" \
  || ok "kueue release not found"

helm uninstall gpu-operator -n gpu-operator --timeout=60s 2>/dev/null \
  && ok "Uninstalled gpu-operator" \
  || ok "gpu-operator release not found"

helm uninstall rhoai-operators -n default --timeout=120s 2>/dev/null \
  && ok "Uninstalled rhoai-operators" \
  || ok "rhoai-operators release not found"

###############################################################################
# 7 — Remove GPU labels from worker nodes
###############################################################################

step "7. Remove GPU labels"

for node in "${WORKERS[@]}"; do
  oc label node "$node" \
    run.ai/simulated-gpu-node-pool- \
    nvidia.com/gpu.product- \
    nvidia.com/gpu.count- \
    nvidia.com/gpu.replicas- \
    nvidia.com/gpu.memory- &>/dev/null || true
  oc annotate node "$node" \
    run.ai/mig.config- \
    run.ai/mig-mapping- &>/dev/null || true
done
ok "GPU labels and annotations removed"

###############################################################################
# 8 — Delete lab namespaces
###############################################################################

step "8. Delete lab namespaces"

for ns in training-jobs inference-apps team-b-jobs gpu-operator openshift-kueue-operator; do
  if oc get ns "$ns" &>/dev/null; then
    oc delete ns "$ns" --timeout=60s 2>/dev/null \
      && ok "Deleted $ns" \
      || warn "$ns deletion timed out — may still be terminating"
  else
    ok "$ns already gone"
  fi
done

###############################################################################
# 9 — Summary
###############################################################################

step "Done"
echo ""
echo -e "${GREEN}Cluster reset complete.${NC}"
echo -e "${YELLOW}RHOAI namespaces may take a few minutes to terminate on their own.${NC}"
echo -e "${YELLOW}Run 'oc get ns' to check progress.${NC}"
echo ""
