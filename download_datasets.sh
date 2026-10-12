#!/usr/bin/env bash
# TelecomSafe - download every training dataset in one go (macOS / Linux).
#   bash download_datasets.sh
# Roboflow datasets need ROBOFLOW_API_KEY in .env; APD (private) is extracted from
# APD.v1i.yolov8.zip if you put it in this folder or in ~/Downloads.
# Datasets already present are skipped, so it is safe to run again.
set -u
cd "$(dirname "$0")"

if ! command -v conda >/dev/null 2>&1; then
    echo "[Error] conda not found. Install Miniconda, then: conda env create -f environment.yml"
    exit 1
fi
if ! conda env list | grep -qE '^telecomsafe\s'; then
    echo "[Error] conda environment \"telecomsafe\" not found. Create it: conda env create -f environment.yml"
    exit 1
fi
PY=(conda run --no-capture-output -n telecomsafe python)

if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env from .env.example."
fi
if ! grep -qE '^ROBOFLOW_API_KEY=.+' .env && [ -z "${ROBOFLOW_API_KEY:-}" ]; then
    echo
    echo "ROBOFLOW_API_KEY is empty. Get it at app.roboflow.com -> Settings -> API Keys,"
    echo "put it after ROBOFLOW_API_KEY= in .env (never commit .env), then run this script again."
    exit 1
fi

echo
echo "Downloading datasets into data/raw/ ..."
echo
"${PY[@]}" -m telecomsafe.data.download
result=$?

echo
echo "---------------------------------------------------------------------------"
echo "Status (a tick means present):"
"${PY[@]}" -m telecomsafe.data.download --list
echo
echo "Phase 1 needs six of these: construction_site_safety, construction_ppe,"
echo "body_harness, work_at_height, construction_safety_v2 and apd."
echo "shel5k, chv and telecom_eval are optional or built separately."
if [ "$result" -ne 0 ]; then
    echo
    echo "[Error] Some downloads failed - see the messages above. Check ROBOFLOW_API_KEY in .env"
    echo "        and your network, then run this script again: finished datasets are skipped."
fi
exit $result
