#!/bin/sh
set -eu
if [ "$#" -ne 2 ]; then
    printf 'Uso: %s ARQUIVO-045.lsmix "pergunta"\n' "$0" >&2
    exit 2
fi
root=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
digest=$(cat "$root/adapter.sha256")
exec "$root/liquid-sense-046" calibrated "$1" "$root/readout.lscal" "$digest" ask "$2"
