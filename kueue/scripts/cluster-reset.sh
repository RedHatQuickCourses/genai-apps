#!/usr/bin/env bash
#
# cluster-reset.sh — Restore the RHDP cluster to its pre-lab (day-0) state.
#
# Removes EVERYTHING the Kueue GPU Quota Management course installs:
#   - GPU taints and labels on worker nodes
#   - All workloads (Jobs, Deployments, Pods) in lab namespaces
#   - RBAC bindings (ClusterRoleBindings, RoleBindings)
#   - All Kueue custom resources (LocalQueues, ClusterQueues, ResourceFlavors, etc.)
#   - MIG node annotations and labels
#   - Kueue operator (Helm release, CSV, namespace, CRDs)
#   - Fake GPU operator (Helm release, namespace)
#   - RHOAI and all dependency operators (NFD, Serverless, Authorino, Pipelines)
#   - Lab namespaces (training-jobs, inference-apps, team-b-jobs)
#   - RHOAI namespaces (redhat-ods-*, rhods-notebooks, rhoai-model-registries)
#
# After running this script, the cluster is in the same state as when
# first provisioned from RHDP. Students can start the lab from Part 1.
#
# The script is idempotent — safe to run multiple times or at any point
# in the course, even if you only completed Part 3.
#
# Works on both macOS and Linux.
#
# Usage:
#   bash scripts/cluster-reset.sh
#
# Prerequisites:
#   - Logged in as cluster admin (oc whoami)
#   - WORKER_NODE1 and WORKER_NODE2 exported, OR the script auto-detects them
#

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

info()  { echo -e "${CYAN}[INFO]${NC}  $*"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
fail()  { echo -e "${RED}[FAIL]${NC}  $*"; }
step()  { echo -e "\n${BOLD}${CYAN}━━━ $* ━━━${NC}"; }

PASS=0
FAIL=0
verify_gone() {
  local label="$1"; shift
  if "$@" &>/dev/null; then
    fail "$label"
    ((FAIL++))
  else
    ok "$label"
    ((PASS++))
  fi
}
verify_true() {
  local label="$1"; shift
  if "$@" &>/dev/null; then
    ok "$label"
    ((PASS++))
  else
    fail "$label"
    ((FAIL++))
  fi
}

###############################################################################
# PRE-FLIGHT
###############################################################################

step "Pre-flight checks"

if ! oc whoami &>/dev/null; then
  fail "Not logged in. Run 'oc login' first."
  exit 1
fi
ok "Logged in as $(oc whoami)"

# Auto-detect worker nodes if not already set
if [[ -z "${WORKER_NODE1:-}" || -z "${WORKER_NODE2:-}" ]]; then
  WORKER_LIST=$(oc get nodes -l node-role.kubernetes.io/worker \
    --no-headers -o custom-columns=NAME:.metadata.name 2>/dev/null \
    | grep -v control-plane | head -2)
  WORKER_NODE1=$(echo "$WORKER_LIST" | sed -n '1p')
  WORKER_NODE2=$(echo "$WORKER_LIST" | sed -n '2p')
  if [[ -n "$WORKER_NODE1" ]]; then
    ok "Auto-detected workers: ${WORKER_NODE1}${WORKER_NODE2:+, $WORKER_NODE2}"
  else
    warn "No dedicated worker nodes found — node cleanup will be skipped"
  fi
else
  ok "Using provided workers: $WORKER_NODE1, $WORKER_NODE2"
fi

ALL_NODES=()
[[ -n "$WORKER_NODE1" ]] && ALL_NODES+=("$WORKER_NODE1")
[[ -n "$WORKER_NODE2" ]] && ALL_NODES+=("$WORKER_NODE2")

###############################################################################
# PHASE 1 — Remove GPU taints  (prevents Ceph/Keycloak/OAuth cascade on reboot)
###############################################################################

step "Phase 1: Remove GPU taints from worker nodes"

for node in "${ALL_NODES[@]}"; do
  if oc adm taint nodes "$node" nvidia.com/gpu=present:NoSchedule- 2>/dev/null; then
    ok "Removed GPU taint from $node"
  else
    ok "No GPU taint on $node (already clean)"
  fi
done

###############################################################################
# PHASE 2 — Delete all workloads
###############################################################################

step "Phase 2: Delete all workloads"

for ns in training-jobs inference-apps team-b-jobs; do
  if oc get ns "$ns" &>/dev/null; then
    oc delete jobs --all -n "$ns" --ignore-not-found 2>/dev/null || true
    oc delete deployments --all -n "$ns" --ignore-not-found 2>/dev/null || true
    oc delete workloads --all -n "$ns" --ignore-not-found 2>/dev/null || true
    ok "Cleaned workloads in $ns"
  fi
done

oc delete pod gpu-test-a100 gpu-test-t4 --ignore-not-found 2>/dev/null || true
ok "Cleaned test pods from default namespace"

###############################################################################
# PHASE 3 — Delete RBAC bindings
###############################################################################

step "Phase 3: Delete RBAC bindings"

oc delete clusterrolebinding kueue-batch-admin-binding --ignore-not-found 2>/dev/null || true
oc delete rolebinding kueue-admin-edit     -n training-jobs --ignore-not-found 2>/dev/null || true
oc delete rolebinding kueue-batch-user-binding -n training-jobs --ignore-not-found 2>/dev/null || true
oc delete rolebinding kueue-user-edit      -n training-jobs --ignore-not-found 2>/dev/null || true
ok "RBAC bindings removed"

###############################################################################
# PHASE 4 — Delete Kueue configuration resources (reverse dependency order)
###############################################################################

step "Phase 4: Delete Kueue configuration resources"

info "Deleting LocalQueues..."
for ns in training-jobs inference-apps team-b-jobs; do
  oc delete localqueues --all -n "$ns" --ignore-not-found 2>/dev/null || true
done
ok "LocalQueues deleted"

info "Deleting ClusterQueues..."
oc delete clusterqueue \
  a100-cluster-queue t4-cluster-queue mig-cluster-queue \
  team-a-cluster-queue team-b-cluster-queue shared-gpu-queue \
  --ignore-not-found 2>/dev/null || true
ok "ClusterQueues deleted"

info "Deleting ResourceFlavors..."
oc delete resourceflavor a100-gpu t4-gpu a100-mig --ignore-not-found 2>/dev/null || true
ok "ResourceFlavors deleted"

info "Deleting WorkloadPriorityClasses..."
oc delete workloadpriorityclasses low-priority medium-priority high-priority \
  --ignore-not-found 2>/dev/null || true
ok "WorkloadPriorityClasses deleted"

###############################################################################
# PHASE 5 — Revert operator patches and undo MIG
###############################################################################

step "Phase 5: Revert operator patches and undo MIG"

# 5a — Revert Kueue CR (if operator still exists)
if oc get ns openshift-kueue-operator &>/dev/null; then
  info "Scaling Kueue operator back up..."
  oc scale deployment openshift-kueue-operator -n openshift-kueue-operator \
    --replicas=2 2>/dev/null || true
  sleep 5

  info "Reverting Kueue CR to defaults..."
  oc patch kueues.kueue.openshift.io cluster -n openshift-kueue-operator \
    --type merge -p '{"spec":{"config":{"preemption":{"preemptionPolicy":"Classical"}}}}' \
    2>/dev/null || true
  ok "Kueue CR reverted"
fi

# 5b — Undo MIG configuration on worker-1
if [[ -n "$WORKER_NODE1" ]]; then
  info "Undoing MIG configuration on $WORKER_NODE1..."
  oc annotate node "$WORKER_NODE1" run.ai/mig.config- run.ai/mig-mapping- 2>/dev/null || true
  oc label node "$WORKER_NODE1" \
    node-role.kubernetes.io/runai-dynamic-mig- \
    node-role.kubernetes.io/runai-mig-enabled- \
    nvidia.com/mig.config.state- 2>/dev/null || true

  if oc get ns gpu-operator &>/dev/null; then
    oc delete configmap "topology-$WORKER_NODE1" -n gpu-operator \
      --ignore-not-found 2>/dev/null || true
    oc delete pod -n gpu-operator -l app=status-updater 2>/dev/null || true
    info "Waiting 15s for topology regeneration..."
    sleep 15
    DEVICE_POD=$(oc get pods -n gpu-operator -l app=device-plugin \
      -o jsonpath="{.items[?(@.spec.nodeName==\"$WORKER_NODE1\")].metadata.name}" 2>/dev/null || true)
    [[ -n "$DEVICE_POD" ]] && oc delete pod -n gpu-operator "$DEVICE_POD" 2>/dev/null || true
  fi
  ok "MIG configuration undone"
fi

###############################################################################
# PHASE 6 — Uninstall Kueue operator
###############################################################################

step "Phase 6: Uninstall Kueue operator"

helm uninstall kueue 2>/dev/null || true

if oc get ns openshift-kueue-operator &>/dev/null; then
  # Delete the Kueue CR instance before removing the operator
  oc delete kueues.kueue.openshift.io cluster -n openshift-kueue-operator \
    --ignore-not-found 2>/dev/null || true

  KUEUE_CSV=$(oc get csv -n openshift-kueue-operator --no-headers 2>/dev/null \
    | grep kueue | awk '{print $1}' || true)
  [[ -n "$KUEUE_CSV" ]] && oc delete csv "$KUEUE_CSV" -n openshift-kueue-operator 2>/dev/null || true
fi

# Delete Kueue CRDs — the operator CSV may leave them behind, and stale CRDs
# block namespace termination via API discovery failures
info "Deleting Kueue CRDs..."
oc get crd -o name 2>/dev/null \
  | grep -E 'kueue\.x-k8s\.io|kueue\.openshift\.io' \
  | xargs oc delete --ignore-not-found 2>/dev/null || true
ok "Kueue CRDs deleted"

# Delete stale Kueue APIService entries — the visibility server APIServices
# reference the now-deleted namespace and block API discovery
info "Deleting Kueue APIService entries..."
oc get apiservice -o name 2>/dev/null \
  | grep kueue \
  | xargs oc delete --ignore-not-found 2>/dev/null || true
ok "Kueue APIServices deleted"

# Now the namespace can terminate cleanly
if oc get ns openshift-kueue-operator &>/dev/null; then
  info "Deleting openshift-kueue-operator namespace..."
  oc delete ns openshift-kueue-operator --ignore-not-found --timeout=60s 2>/dev/null || true
fi
ok "Kueue operator uninstalled"

###############################################################################
# PHASE 7 — Uninstall Fake GPU operator
###############################################################################

step "Phase 7: Uninstall Fake GPU operator"

helm uninstall gpu-operator -n gpu-operator 2>/dev/null || true
oc delete ns gpu-operator --ignore-not-found --timeout=60s 2>/dev/null || true
ok "Fake GPU operator uninstalled"

# Remove all GPU-related labels from worker nodes
info "Removing GPU labels and annotations from worker nodes..."
for node in "${ALL_NODES[@]}"; do
  oc label node "$node" \
    run.ai/simulated-gpu-node-pool- \
    nvidia.com/gpu.product- \
    nvidia.com/gpu.count- \
    nvidia.com/gpu.replicas- \
    nvidia.com/gpu.memory- 2>/dev/null || true
  oc annotate node "$node" \
    run.ai/mig.config- \
    run.ai/mig-mapping- 2>/dev/null || true
done
ok "GPU labels and annotations removed"

###############################################################################
# PHASE 8 — Uninstall RHOAI and dependency operators
###############################################################################

step "Phase 8: Uninstall RHOAI and dependency operators"

# 8a — Delete the DataScienceCluster and DSCInitialization CRs first
#       so the RHOAI operator cleans up its managed resources
info "Deleting DataScienceCluster CR..."
oc delete datasciencecluster default-dsc --ignore-not-found 2>/dev/null || true
ok "DataScienceCluster CR deleted"

info "Deleting DSCInitialization CR..."
oc delete dsci default-dsci --ignore-not-found 2>/dev/null || true
ok "DSCInitialization CR deleted"

info "Waiting 30s for RHOAI operator to clean up managed resources..."
sleep 30

# 8b — Remove Helm release (deletes Subscriptions, OperatorGroups)
info "Removing RHOAI Helm release..."
helm uninstall rhoai-operators 2>/dev/null || true
ok "RHOAI Helm release removed"

# 8c — Delete Subscriptions that may have survived Helm uninstall
info "Cleaning up remaining Subscriptions..."
oc delete subscription nfd -n openshift-nfd --ignore-not-found 2>/dev/null || true
oc delete subscription serverless-operator -n openshift-serverless --ignore-not-found 2>/dev/null || true
oc delete subscription authorino-operator -n openshift-operators --ignore-not-found 2>/dev/null || true
oc delete subscription openshift-pipelines-operator-rh -n openshift-operators --ignore-not-found 2>/dev/null || true
oc delete subscription rhods-operator -n redhat-ods-operator --ignore-not-found 2>/dev/null || true
ok "Subscriptions removed"

# 8d — Delete CSVs across all operator namespaces
info "Cleaning up CSVs..."
oc get csv -A --no-headers 2>/dev/null \
  | grep -E 'nfd|serverless|authorino|pipeline|rhods' \
  | awk '{print "oc delete csv " $2 " -n " $1 " --ignore-not-found 2>/dev/null"}' \
  | sh 2>/dev/null || true

# Also clean up Kueue CSV in keycloak namespace (leftover from RHOAI)
oc get csv -A --no-headers 2>/dev/null \
  | grep -E 'kueue-operator' \
  | awk '{print "oc delete csv " $2 " -n " $1 " --ignore-not-found 2>/dev/null"}' \
  | sh 2>/dev/null || true

# Clean up servicemesh CSV if installed by RHOAI
oc get csv -A --no-headers 2>/dev/null \
  | grep -E 'servicemesh' \
  | awk '{print "oc delete csv " $2 " -n " $1 " --ignore-not-found 2>/dev/null"}' \
  | sh 2>/dev/null || true
ok "CSVs cleaned up"

# 8e — Delete RHOAI-created namespaces
info "Deleting RHOAI namespaces (this may take a few minutes)..."
for ns in \
  redhat-ods-operator \
  redhat-ods-applications \
  redhat-ods-monitoring \
  rhods-notebooks \
  rhoai-model-registries \
  openshift-nfd \
  openshift-serverless \
  openshift-pipelines; do
  oc delete ns "$ns" --ignore-not-found --timeout=120s 2>/dev/null || warn "Namespace $ns deletion timed out — may still be terminating"
done
ok "RHOAI namespaces deleted"

# 8f — Delete OperatorGroups that Helm may have left behind
info "Cleaning up OperatorGroups..."
oc delete operatorgroup openshift-nfd -n openshift-nfd --ignore-not-found 2>/dev/null || true
oc delete operatorgroup openshift-serverless -n openshift-serverless --ignore-not-found 2>/dev/null || true
oc delete operatorgroup rhods-operator -n redhat-ods-operator --ignore-not-found 2>/dev/null || true
ok "OperatorGroups cleaned up"

###############################################################################
# PHASE 9 — Delete lab namespaces
###############################################################################

step "Phase 9: Delete lab namespaces"

for ns in training-jobs inference-apps team-b-jobs; do
  if oc delete ns "$ns" --ignore-not-found --timeout=60s 2>/dev/null; then
    ok "Deleted namespace $ns"
  else
    ok "Namespace $ns already gone"
  fi
done

###############################################################################
# PHASE 10 — Verification
###############################################################################

step "Phase 10: Verification"
echo ""

# Disable exit-on-error for verification — we want to run all checks
set +e

info "Checking GPU taints..."
for node in "${ALL_NODES[@]}"; do
  TAINTS=$(oc get node "$node" -o jsonpath='{.spec.taints}' 2>/dev/null || echo "[]")
  if echo "$TAINTS" | grep -q "nvidia.com/gpu"; then
    fail "GPU taint still present on $node"
    ((FAIL++))
  else
    ok "No GPU taint on $node"
    ((PASS++))
  fi
done

info "Checking GPU labels..."
GPU_LABELED=$(oc get nodes -l run.ai/simulated-gpu-node-pool --no-headers 2>/dev/null | wc -l | tr -d ' ')
if [[ "$GPU_LABELED" -eq 0 ]]; then
  ok "No GPU pool labels on any node"
  ((PASS++))
else
  fail "GPU pool labels still on $GPU_LABELED node(s)"
  ((FAIL++))
fi

info "Checking lab namespaces..."
for ns in training-jobs inference-apps team-b-jobs gpu-operator openshift-kueue-operator; do
  verify_gone "Namespace $ns removed" oc get ns "$ns"
done

info "Checking RHOAI namespaces..."
for ns in redhat-ods-operator redhat-ods-applications redhat-ods-monitoring; do
  verify_gone "Namespace $ns removed" oc get ns "$ns"
done

info "Checking Kueue resources..."
CQ_OUTPUT=$(oc get clusterqueues --no-headers 2>/dev/null || true)
CQ_COUNT=0
if [[ -n "$CQ_OUTPUT" ]]; then
  CQ_COUNT=$(echo "$CQ_OUTPUT" | wc -l | tr -d ' ')
fi
if [[ "$CQ_COUNT" -eq 0 ]]; then
  ok "No ClusterQueues (CRD removed or no instances)"
  ((PASS++))
else
  fail "$CQ_COUNT ClusterQueue(s) still exist"
  ((FAIL++))
fi

info "Checking RHOAI operator..."
verify_gone "No RHOAI Subscription" oc get subscription rhods-operator -n redhat-ods-operator
verify_gone "No DataScienceCluster CR" oc get datasciencecluster default-dsc

info "Checking authentication..."
AUTH_AVAIL=$(oc get co authentication \
  -o jsonpath='{.status.conditions[?(@.type=="Available")].status}' 2>/dev/null || echo "Unknown")
if [[ "$AUTH_AVAIL" == "True" ]]; then
  ok "Authentication operator Available"
  ((PASS++))
else
  fail "Authentication operator: $AUTH_AVAIL"
  ((FAIL++))
fi

###############################################################################
# SUMMARY
###############################################################################

echo ""
step "Summary"

if [[ $FAIL -eq 0 ]]; then
  echo -e "${GREEN}All $PASS checks passed. Cluster is restored to pre-lab state.${NC}"
  echo -e "${GREEN}You can now start the lab from Part 1.${NC}"
else
  echo -e "${RED}$FAIL check(s) failed, $PASS passed. Review the output above.${NC}"
  echo -e "${YELLOW}Some namespaces may take a few minutes to fully terminate.${NC}"
  echo -e "${YELLOW}Re-run this script after a minute if you see pending deletions.${NC}"
fi
echo ""
