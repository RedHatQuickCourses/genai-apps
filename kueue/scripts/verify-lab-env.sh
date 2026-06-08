#!/usr/bin/env bash
#
# verify-lab-env.sh — Verify that the cluster is ready for the Kueue course.
#
# Checks all prerequisites before starting Part 1:
#   - Logged in as cluster admin
#   - OCP version and node configuration
#   - At least 2 dedicated worker nodes with sufficient resources
#   - No leftover lab resources from a previous run
#   - Required CLI tools (oc, helm, git)
#   - cert-manager Operator installed
#   - Authentication operator healthy
#
# If any check fails, the script tells you exactly what to do.
#
# Works on both macOS and Linux.
#
# Usage:
#   bash scripts/verify-lab-env.sh
#

set -uo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

ok()    { echo -e "  ${GREEN}✓${NC} $*"; }
fail()  { echo -e "  ${RED}✗${NC} $*"; }
warn()  { echo -e "  ${YELLOW}!${NC} $*"; }
info()  { echo -e "  ${CYAN}→${NC} $*"; }
header(){ echo -e "\n${BOLD}$*${NC}"; }

PASS=0
FAIL=0
WARN=0

check_pass() { ok "$1"; ((PASS++)); }
check_fail() { fail "$1"; ((FAIL++)); }
check_warn() { warn "$1"; ((WARN++)); }

###############################################################################
header "1. Cluster Access"
###############################################################################

if ! oc whoami &>/dev/null; then
  check_fail "Not logged in to the cluster"
  echo -e "     ${CYAN}Fix:${NC} oc login -u <admin-user> -p <password> <api-url>"
  echo ""
  echo -e "${RED}Cannot continue without cluster access. Fix the login and re-run.${NC}"
  exit 1
fi

CURRENT_USER=$(oc whoami 2>/dev/null)
check_pass "Logged in as $CURRENT_USER"

# Check for cluster-admin privileges
if oc auth can-i '*' '*' --all-namespaces &>/dev/null; then
  check_pass "User has cluster-admin privileges"
else
  check_fail "User $CURRENT_USER does not have cluster-admin privileges"
  echo -e "     ${CYAN}Fix:${NC} Log in as a cluster admin user"
fi

###############################################################################
header "2. OpenShift Version"
###############################################################################

OCP_VERSION=$(oc get clusterversion version -o jsonpath='{.status.desired.version}' 2>/dev/null || echo "unknown")
K8S_VERSION=$(oc version -o json 2>/dev/null | python3 -c "import json,sys; print(json.load(sys.stdin).get('serverVersion',{}).get('gitVersion','unknown'))" 2>/dev/null || echo "unknown")

check_pass "OpenShift $OCP_VERSION (Kubernetes $K8S_VERSION)"

MAJOR_MINOR=$(echo "$OCP_VERSION" | cut -d. -f1,2)
MIN_VERSION="4.17"
if python3 -c "exit(0 if tuple(map(int,'$MAJOR_MINOR'.split('.'))) >= tuple(map(int,'$MIN_VERSION'.split('.'))) else 1)" 2>/dev/null; then
  check_pass "Version $MAJOR_MINOR meets minimum requirement ($MIN_VERSION+)"
else
  check_fail "Version $MAJOR_MINOR is below minimum requirement ($MIN_VERSION+)"
fi

###############################################################################
header "3. Node Configuration"
###############################################################################

TOTAL_NODES=$(oc get nodes --no-headers 2>/dev/null | wc -l | tr -d ' ')
check_pass "$TOTAL_NODES total nodes in cluster"

# Find dedicated worker nodes (not control-plane)
WORKER_LIST=$(oc get nodes --no-headers -o custom-columns=NAME:.metadata.name 2>/dev/null \
  | while read node; do
    ROLES=$(oc get node "$node" -o jsonpath='{.metadata.labels}' 2>/dev/null \
      | python3 -c "import json,sys; labels=json.load(sys.stdin); roles=[k.split('/')[1] for k in labels if k.startswith('node-role.kubernetes.io/')]; print(' '.join(roles))" 2>/dev/null)
    if echo "$ROLES" | grep -q "worker" && ! echo "$ROLES" | grep -q "control-plane" && ! echo "$ROLES" | grep -q "master"; then
      echo "$node"
    fi
  done)

WORKER_COUNT=$(echo "$WORKER_LIST" | grep -c . 2>/dev/null || echo "0")

if [[ "$WORKER_COUNT" -ge 2 ]]; then
  check_pass "$WORKER_COUNT dedicated worker nodes found"
  WORKER_NODE1=$(echo "$WORKER_LIST" | head -1)
  WORKER_NODE2=$(echo "$WORKER_LIST" | sed -n '2p')
  info "Worker 1: $WORKER_NODE1"
  info "Worker 2: $WORKER_NODE2"

  # Check resources on each worker
  for node in $WORKER_NODE1 $WORKER_NODE2; do
    CPU=$(oc get node "$node" -o jsonpath='{.status.capacity.cpu}' 2>/dev/null || echo "0")
    MEM_KI=$(oc get node "$node" -o jsonpath='{.status.capacity.memory}' 2>/dev/null || echo "0Ki")
    MEM_GI=$(echo "$MEM_KI" | sed 's/Ki//' | awk '{printf "%.0f", $1/1048576}')

    if [[ "$CPU" -ge 8 && "$MEM_GI" -ge 32 ]]; then
      check_pass "$node: ${CPU} vCPUs, ${MEM_GI} GiB RAM"
    else
      check_fail "$node: ${CPU} vCPUs, ${MEM_GI} GiB RAM (need ≥8 vCPUs, ≥32 GiB)"
    fi
  done
else
  check_fail "Found $WORKER_COUNT dedicated worker node(s) — need at least 2"
  echo -e "     ${CYAN}Fix:${NC} Provision a cluster with at least 2 dedicated worker nodes"
fi

###############################################################################
header "4. No Leftover Lab Resources"
###############################################################################

LEFTOVERS=0

# Check GPU taints
for node in $WORKER_NODE1 $WORKER_NODE2; do
  [[ -z "$node" ]] && continue
  TAINTS=$(oc get node "$node" -o jsonpath='{.spec.taints}' 2>/dev/null || echo "[]")
  if echo "$TAINTS" | grep -q "nvidia.com/gpu"; then
    check_fail "GPU taint found on $node"
    ((LEFTOVERS++))
  fi
done

# Check GPU labels
GPU_LABELED=$(oc get nodes -l run.ai/simulated-gpu-node-pool --no-headers 2>/dev/null | wc -l | tr -d ' ')
if [[ "$GPU_LABELED" -gt 0 ]]; then
  check_fail "GPU pool labels found on $GPU_LABELED node(s)"
  ((LEFTOVERS++))
fi

# Check lab namespaces
for ns in training-jobs inference-apps team-b-jobs gpu-operator openshift-kueue-operator; do
  if oc get ns "$ns" &>/dev/null; then
    check_fail "Lab namespace '$ns' still exists"
    ((LEFTOVERS++))
  fi
done

# Check RHOAI
if oc get datasciencecluster default-dsc &>/dev/null; then
  check_fail "DataScienceCluster 'default-dsc' still exists (RHOAI installed)"
  ((LEFTOVERS++))
fi
for ns in redhat-ods-operator redhat-ods-applications redhat-ods-monitoring; do
  if oc get ns "$ns" &>/dev/null; then
    check_fail "RHOAI namespace '$ns' still exists"
    ((LEFTOVERS++))
  fi
done

# Check Kueue resources
CQ_OUTPUT=$(oc get clusterqueues --no-headers 2>/dev/null || true)
if [[ -n "$CQ_OUTPUT" ]]; then
  CQ_COUNT=$(echo "$CQ_OUTPUT" | wc -l | tr -d ' ')
  check_fail "$CQ_COUNT ClusterQueue(s) still exist"
  ((LEFTOVERS++))
fi

if [[ "$LEFTOVERS" -eq 0 ]]; then
  check_pass "No leftover lab resources found"
else
  echo ""
  echo -e "     ${CYAN}Fix:${NC} Run the cleanup script to remove all leftover resources:"
  echo -e "     ${BOLD}bash scripts/cluster-reset.sh${NC}"
fi

###############################################################################
header "5. Required CLI Tools"
###############################################################################

for tool in oc helm git python3; do
  if command -v "$tool" &>/dev/null; then
    VERSION=$("$tool" version --client --short 2>/dev/null || "$tool" version --short 2>/dev/null || "$tool" --version 2>/dev/null | head -1)
    check_pass "$tool: $VERSION"
  else
    check_fail "$tool not found in PATH"
    echo -e "     ${CYAN}Fix:${NC} Install $tool and ensure it is in your PATH"
  fi
done

###############################################################################
header "6. cert-manager Operator"
###############################################################################

CERTMGR=$(oc get csv -A --no-headers 2>/dev/null | grep cert-manager | grep Succeeded | head -1)
if [[ -n "$CERTMGR" ]]; then
  CERTMGR_NAME=$(echo "$CERTMGR" | awk '{print $2}')
  check_pass "cert-manager installed: $CERTMGR_NAME"
else
  check_fail "cert-manager Operator not found or not in Succeeded phase"
  echo -e "     ${CYAN}Fix:${NC} Install the cert-manager Operator from OperatorHub"
fi

###############################################################################
header "7. Cluster Health"
###############################################################################

# Authentication operator
AUTH_AVAIL=$(oc get co authentication -o jsonpath='{.status.conditions[?(@.type=="Available")].status}' 2>/dev/null || echo "Unknown")
AUTH_DEGRADED=$(oc get co authentication -o jsonpath='{.status.conditions[?(@.type=="Degraded")].status}' 2>/dev/null || echo "Unknown")

if [[ "$AUTH_AVAIL" == "True" && "$AUTH_DEGRADED" != "True" ]]; then
  check_pass "Authentication operator: Available"
else
  check_fail "Authentication operator: Available=$AUTH_AVAIL, Degraded=$AUTH_DEGRADED"
  echo -e "     ${CYAN}Fix:${NC} Check 'oc get co authentication -o yaml' for details"
fi

# Count degraded cluster operators
DEGRADED_COUNT=$(oc get co -o json 2>/dev/null | python3 -c "
import json,sys
data=json.load(sys.stdin)
count=0
for item in data.get('items',[]):
    for c in item.get('status',{}).get('conditions',[]):
        if c.get('type')=='Degraded' and c.get('status')=='True':
            count+=1
print(count)" 2>/dev/null || echo "unknown")

if [[ "$DEGRADED_COUNT" == "0" ]]; then
  check_pass "No degraded cluster operators"
else
  check_warn "$DEGRADED_COUNT cluster operator(s) degraded"
  echo -e "     ${CYAN}Check:${NC} oc get co | grep -v 'True.*False.*False'"
fi

###############################################################################
# Summary
###############################################################################

echo ""
header "Summary"

if [[ $FAIL -eq 0 && $WARN -eq 0 ]]; then
  echo -e "${GREEN}All $PASS checks passed. Your cluster is ready for the course.${NC}"
elif [[ $FAIL -eq 0 ]]; then
  echo -e "${GREEN}$PASS checks passed${NC}, ${YELLOW}$WARN warning(s)${NC}. Cluster is usable but review the warnings above."
else
  echo -e "${RED}$FAIL check(s) failed${NC}, $PASS passed, $WARN warning(s). Fix the issues above before starting the course."
fi
echo ""
