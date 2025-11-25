#!/bin/bash

set -eo pipefail

ISAAC_SIM_PATH="${ISAAC_SIM_PATH:-$HOME/isaac-sim}" 
LAUNCHER="${ISAAC_SIM_LAUNCHER:-isaac-sim.streaming.sh}"

if [ ! -x "$ISAAC_SIM_PATH/$LAUNCHER" ]; then
  echo "Isaac Sim launcher not found at $ISAAC_SIM_PATH/$LAUNCHER" >&2
  exit 1
fi

cd "$ISAAC_SIM_PATH"
"./$LAUNCHER"
