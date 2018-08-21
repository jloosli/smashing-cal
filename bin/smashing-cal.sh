#!/usr/bin/env bash

BINPATH=`dirname $0`
VENV_DIR="${BINPATH}/../venv"
source "${VENV_DIR}/bin/activate"
python "$BINPATH/../main.py" $@
deactivate