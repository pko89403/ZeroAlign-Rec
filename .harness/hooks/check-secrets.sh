#!/bin/bash

set -euo pipefail

if ! git rev-parse --show-toplevel >/dev/null 2>&1; then
  exit 0
fi

cd "$(git rev-parse --show-toplevel)"

staged_files="$(git diff --cached --name-only)"
if [ -z "$staged_files" ]; then
  exit 0
fi

warned=0

while IFS= read -r file; do
  [ -n "$file" ] || continue
  case "$file" in
    *.example)
      continue
      ;;
    .env|.env.*|*/.env|*/.env.*|*credentials.json|*secret.json|*secrets.json|*secret.yaml|*secrets.yaml|*secret.yml|*secrets.yml|*secret.toml|*secrets.toml|*.pem|*.key|*.p12|*.pfx)
      echo "WARN: staged file looks like secret material: $file" >&2
      warned=1
      ;;
  esac
done <<EOF
$staged_files
EOF

if git diff --cached -U0 | grep -Eq '^\+.*(AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]+|sk-[A-Za-z0-9]{20,}|AIza[0-9A-Za-z_-]{20,}|hf_[A-Za-z0-9]{20,}|BEGIN (RSA|OPENSSH|EC|DSA) PRIVATE KEY|anthropic_api_key|youtube_api_key)'; then
  echo "WARN: staged diff may contain credentials or private key material." >&2
  warned=1
fi

if [ "$warned" -eq 1 ]; then
  echo "WARN: review staged changes for accidental secret exposure before pushing." >&2
fi
