#!/usr/bin/env bash
set -euo pipefail

# Default values
SOURCE_ADDR=""
SOURCE_CACERT=""
SOURCE_TOKEN=""
DEST_ADDR=""
DEST_CACERT=""
DEST_TOKEN=""
MOUNT=""
START_PATH=""
DRY_RUN="false"
KV_VERSION="2"

usage() {
    cat <<EOF
Usage: $0 [options]

Migrate secrets from source Vault to destination Vault.
Uses vault CLI parameters directly without environment variables.

Required options:
    --source-addr ADDR         Source Vault address (e.g., https://10.44.77.172:8200)
    --source-cacert PATH       Path to source Vault CA certificate
    --source-token TOKEN       Source Vault authentication token
    --dest-addr ADDR           Destination Vault address
    --dest-cacert PATH         Path to destination Vault CA certificate
    --dest-token TOKEN         Destination Vault authentication token
    --mount MOUNT              KV mount path to migrate (e.g., "kv")

Optional:
    --start-path PATH          Sub-path within mount (e.g., "mypasswords/")
    --dry-run                  Simulate migration without making changes
    --kv-version VERSION       KV secrets engine version (default: 2)
    --help                     Show this help message

Examples:
    # Migrate all secrets from 'kv' mount
    $0 --source-addr https://10.44.77.172:8200 \\
        --source-cacert ./source-vault.pem \\
        --source-token hvs.source_token \\
        --dest-addr https://10.5.0.10:8200 \\
        --dest-cacert ./dest-vault.pem \\
        --dest-token hvs.dest_token \\
        --mount kv

    # Migrate from specific path with dry-run
    $0 --source-addr https://10.44.77.172:8200 \\
        --source-cacert ./source-vault.pem \\
        --source-token hvs.source_token \\
        --dest-addr https://10.5.0.10:8200 \\
        --dest-cacert ./dest-vault.pem \\
        --dest-token hvs.dest_token \\
        --mount kv \\
        --start-path mypasswords/ \\
        --dry-run
EOF
    exit 1
}

# Helper function to call vault with source credentials
vault_source() {
    VAULT_ADDR="$SOURCE_ADDR" VAULT_CACERT="$SOURCE_CACERT" VAULT_TOKEN="$SOURCE_TOKEN" vault "$@"
}

# Helper function to call vault with destination credentials
vault_dest() {
    VAULT_ADDR="$DEST_ADDR" VAULT_CACERT="$DEST_CACERT" VAULT_TOKEN="$DEST_TOKEN" vault "$@"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --source-addr)
            SOURCE_ADDR="$2"
            shift 2
            ;;
        --source-cacert)
            SOURCE_CACERT="$2"
            shift 2
            ;;
        --source-token)
            SOURCE_TOKEN="$2"
            shift 2
            ;;
        --dest-addr)
            DEST_ADDR="$2"
            shift 2
            ;;
        --dest-cacert)
            DEST_CACERT="$2"
            shift 2
            ;;
        --dest-token)
            DEST_TOKEN="$2"
            shift 2
            ;;
        --mount)
            MOUNT="$2"
            shift 2
            ;;
        --start-path)
            START_PATH="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN="true"
            shift
            ;;
        --kv-version)
            KV_VERSION="$2"
            shift 2
            ;;
        --help|-h)
            usage
            ;;
        *)
            echo "Unknown option: $1" >&2
            usage
            ;;
    esac
done

# Validate required parameters
if [[ -z "$SOURCE_ADDR" || -z "$SOURCE_CACERT" || -z "$SOURCE_TOKEN" ]]; then
    echo "ERROR: --source-addr, --source-cacert, and --source-token are required" >&2
    usage
fi

if [[ -z "$DEST_ADDR" || -z "$DEST_CACERT" || -z "$DEST_TOKEN" ]]; then
    echo "ERROR: --dest-addr, --dest-cacert, and --dest-token are required" >&2
    usage
fi

if [[ -z "$MOUNT" ]]; then
    echo "ERROR: --mount is required" >&2
    usage
fi

# Check required commands
command -v vault >/dev/null || { echo "ERROR: vault CLI not found" >&2; exit 1; }
command -v jq >/dev/null   || { echo "ERROR: jq not found" >&2; exit 1; }

# Verify CA certificates exist
if [[ ! -f "$SOURCE_CACERT" ]]; then
    echo "ERROR: Source CA certificate not found: $SOURCE_CACERT" >&2
    exit 1
fi

if [[ ! -f "$DEST_CACERT" ]]; then
    echo "ERROR: Destination CA certificate not found: $DEST_CACERT" >&2
    exit 1
fi

# Normalize start path: "" or ends with /
if [[ -n "$START_PATH" && "$START_PATH" != */ ]]; then
    START_PATH="${START_PATH}/"
fi

echo "=== Vault Secret Migration ===" >&2
echo "Source: $SOURCE_ADDR (mount: $MOUNT, path: ${START_PATH:-/})" >&2
echo "Destination: $DEST_ADDR (mount: $MOUNT)" >&2
if [[ "$DRY_RUN" == "true" ]]; then
    echo "Mode: DRY RUN (no changes will be made)" >&2
fi
echo "" >&2

if ! vault_source status >/dev/null 2>&1; then
    echo "ERROR: Cannot connect to source Vault at $SOURCE_ADDR" >&2
    exit 1
fi

if ! vault_dest status >/dev/null 2>&1; then
    echo "ERROR: Cannot connect to destination Vault at $DEST_ADDR" >&2
    exit 1
fi

# Ensure destination mount exists
ensure_mount() {
    local mount="$1"
    local key="${mount}/"

    if echo "$(vault_dest secrets list -format=json)" | jq -e --arg k "$key" 'has($k)' >/dev/null; then
        echo "Mount exists: $key" >&2
        return 0
    fi

    echo "Mount missing, enabling KV v${KV_VERSION} at: $key" >&2
    if [[ "$DRY_RUN" == "true" ]]; then
        echo "DRY_RUN: would enable mount at '$mount' with version '$KV_VERSION'" >&2
        return 0
    fi

    vault_dest secrets enable -path="$mount" -version="$KV_VERSION" kv >/dev/null
}

ensure_mount "$MOUNT"
echo "" >&2


echo "--- Migrating secrets ---" >&2

walk() {
    local prefix="$1"   # relative path inside mount, always "" or ends with /

    local keys_json
    # Only pass prefix argument if it's not empty
    if [[ -n "$prefix" ]]; then
        if ! keys_json="$(vault_source kv list -format=json -mount="$MOUNT" "$prefix" 2>/dev/null)"; then
            echo "WARN: cannot list: ${MOUNT}/${prefix}" >&2
            return 0
        fi
    else
        if ! keys_json="$(vault_source kv list -format=json -mount="$MOUNT" 2>/dev/null)"; then
            echo "WARN: cannot list: ${MOUNT}/" >&2
            return 0
        fi
    fi

    echo "$keys_json" | jq -r '.[]' | while IFS= read -r k; do
        if [[ "$k" == */ ]]; then
            # recurse into subfolder
            walk "${prefix}${k}"
        else
            local rel="${prefix}${k}"
            echo "Migrating: ${MOUNT}/${rel}" >&2

            # Get secret data from source
            if data="$(vault_source kv get -format=json -field=data -mount="$MOUNT" "$rel" 2>/dev/null)"; then
                if [[ "$DRY_RUN" == "true" ]]; then
                    echo "DRY_RUN: would import to ${MOUNT}/${rel}" >&2
                else
                    # Write to destination
                    if ! echo "$data" | vault_dest kv put -mount="$MOUNT" "$rel" - >/dev/null 2>&1; then
                        echo "ERROR: failed to import ${MOUNT}/${rel}" >&2
                    fi
                fi
            else
                echo "WARN: cannot read: ${MOUNT}/${rel}" >&2
            fi
        fi
    done
}

walk "$START_PATH"
