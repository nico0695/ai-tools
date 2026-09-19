#!/bin/sh
command -v node >/dev/null 2>&1 || { echo "error: Node >= 20 required (https://nodejs.org)" >&2; exit 1; }
exec node "$(dirname "$0")/scripts/installer/cli.js" "$@"
