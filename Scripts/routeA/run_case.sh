#!/usr/bin/env bash

if [ "$#" -ne 1 ]; then
    echo "usage: $0 CASE_DIRECTORY" >&2
    exit 2
fi

source /opt/openfoam13/etc/bashrc
set -eo pipefail
case_dir=$(readlink -f "$1")
project_dir=$(cd "$(dirname "$0")/../.." && pwd)

foamVersion > "$case_dir/log.environment" 2>&1
{
    command -v foamRun
    echo "WM_PROJECT=$WM_PROJECT"
    echo "WM_PROJECT_VERSION=$WM_PROJECT_VERSION"
    echo "WM_PROJECT_DIR=$WM_PROJECT_DIR"
    echo "FOAM_RUN=$FOAM_RUN"
    echo "WM_OPTIONS=$WM_OPTIONS"
    hostname
    date --iso-8601=seconds
} >> "$case_dir/log.environment"

blockMesh -case "$case_dir" > "$case_dir/log.blockMesh" 2>&1
checkMesh -case "$case_dir" -allGeometry -allTopology > "$case_dir/log.checkMesh" 2>&1

init_dir=$(python3 "$project_dir/Scripts/routeA/prepare_initialization_check.py" "$case_dir")
foamRun -case "$init_dir" > "$init_dir/log.foamRun.initialization" 2>&1

foamRun -case "$case_dir" > "$case_dir/log.foamRun" 2>&1
