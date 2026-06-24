#!/usr/bin/env bash
# hermes-preflight skill installer
#
# Install + verify:
#   1. Copy templates/SOUL.md -> ~/.hermes/SOUL.md   (gives you the runtime workflow)
#   2. Copy this repo     -> ~/.hermes/skills/hermes/hermes-preflight/
#                                                  (gives you docs + validator)
#   3. Run the validator to confirm SOUL.md is well-formed
#
# Usage:
#   bash install.sh                    # interactive (asks before overwriting SOUL.md)
#   HERMES_HOME=/path bash install.sh  # custom Hermes home
#   bash install.sh --yes              # non-interactive (overwrites if exists)
#   bash install.sh --help             # show this message
#
# Environment variables:
#   HERMES_HOME   Path to Hermes config dir (default: ~/.hermes)

set -e

# ---------- args ----------
YES=0
for arg in "$@"; do
    case "$arg" in
        --yes|-y) YES=1 ;;
        --help|-h)
            sed -n '2,20p' "$0"
            exit 0
            ;;
        *)
            echo "Unknown argument: $arg" >&2
            echo "Try: bash install.sh --help" >&2
            exit 2
            ;;
    esac
done

# ---------- paths ----------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
SOUL_SRC="$SCRIPT_DIR/templates/SOUL.md"
SOUL_DST="$HERMES_HOME/SOUL.md"
SKILL_DST="$HERMES_HOME/skills/hermes/hermes-preflight"
VALIDATOR="$SKILL_DST/scripts/validate_preflight.py"

# ---------- header ----------
echo ""
echo "  Hermes Preflight installer"
echo "  --------------------------"
echo "  Source : $SCRIPT_DIR"
echo "  Target : $HERMES_HOME"
echo ""

# ---------- preflight checks ----------
if [ ! -f "$SOUL_SRC" ]; then
    echo "ERROR: $SOUL_SRC not found." >&2
    echo "  Are you running install.sh from inside the cloned repo?" >&2
    exit 1
fi

if [ ! -d "$HERMES_HOME" ]; then
    echo "ERROR: $HERMES_HOME does not exist." >&2
    echo "  Is Hermes Agent installed? Set HERMES_HOME to override." >&2
    exit 1
fi

# ---------- Step 1: SOUL.md ----------
SKIP_SOUL=0
if [ -f "$SOUL_DST" ]; then
    if [ "$YES" -eq 1 ]; then
        echo "  Overwriting existing $SOUL_DST (--yes)"
    else
        echo "  WARNING: $SOUL_DST already exists."
        printf "  Overwrite? [y/N] "
        read -r REPLY
        if [[ ! "$REPLY" =~ ^[Yy]$ ]]; then
            echo "  Skipping SOUL.md copy."
            SKIP_SOUL=1
        fi
    fi
fi

if [ "$SKIP_SOUL" -eq 0 ]; then
    cp "$SOUL_SRC" "$SOUL_DST"
    echo "  Copied templates/SOUL.md -> $SOUL_DST"
fi

# ---------- Step 2: skill ----------
mkdir -p "$HERMES_HOME/skills/hermes"
# Remove existing skill dir to ensure a clean install (no stale files from prior versions)
if [ -d "$SKILL_DST" ]; then
    rm -rf "$SKILL_DST"
fi
cp -r "$SCRIPT_DIR" "$SKILL_DST"
echo "  Installed skill to $SKILL_DST"

# ---------- Step 3: validate ----------
echo ""
echo "  Running validator on $SOUL_DST..."
if python3 "$VALIDATOR" "$SOUL_DST"; then
    echo ""
    echo "  Install complete."
    echo ""
    echo "  Next steps:"
    echo "    1. Restart Hermes (or start a new session) to load the new SOUL.md"
    echo "    2. Customize the Persona / How I think sections of SOUL.md to match your voice"
    echo "    3. Add a memory entry so your agent knows the skill exists across sessions:"
    echo "         memory(action='add', target='memory', content='hermes-preflight skill at ...')"
    echo "       (see README \"Recommended post-install memory entry\" for the full string)"
    echo ""
else
    echo ""
    echo "  WARNING: Validator reported issues." >&2
    echo "  The skill is installed but $SOUL_DST may need manual fixes." >&2
    echo "  See validator output above for line numbers and suggested fixes." >&2
    exit 1
fi
