#!/usr/bin/env sh
# Container entrypoint. `bll serve` runs the startup bootstrap itself: it locates
# a reachable ollama (the host's via host.docker.internal, or the bundled
# sibling), pulls the base model only if missing, and builds the aligner profile.
# --wait gives a just-started sibling ollama time to come up.
set -e
exec bll serve --host 0.0.0.0 --port 8000 --wait "${BLL_WAIT:-60}"
