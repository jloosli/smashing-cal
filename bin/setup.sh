#!/usr/bin/env bash
set -e
BINPATH=`dirname $0`
VENV_DIR="${BINPATH}/../venv"

if [ ! -d ${VENV_DIR} ]; then
    virtualenv $VENV_DIR --python=/usr/bin/python3
fi

source "${VENV_DIR}/bin/activate"
pip install -r requirements.txt
deactivate