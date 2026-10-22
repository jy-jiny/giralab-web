#!/usr/bin/env bash
set -euo pipefail

# Keep the package and preinstalled browsers at the same version. Avoid apt mirror downloads per run.
# https://playwright.dev/docs/docker
image='mcr.microsoft.com/playwright:v1.62.1-noble@sha256:dcc5531e97840b9b5e794f2814476b21571c5124a3fca2267d73041f56e7580e'
browser_tools="${RUNNER_TEMP:?}/giralab-browser-tools"
npm install --prefix "$browser_tools" --no-package-lock --ignore-scripts --no-audit --no-fund playwright@1.62.1

docker run --rm --init --ipc=host \
  --mount "type=bind,source=${GITHUB_WORKSPACE:?},target=/workspace,readonly" \
  --mount "type=bind,source=$browser_tools,target=/browser-tools,readonly" \
  --workdir /workspace \
  --env GIRALAB_BROWSER_TOOLS=/browser-tools \
  "$image" node scripts/test-hearts-release.mjs "$@"
