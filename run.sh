#!/usr/bin/env bash

: "${VENV:=venv}"

echo "Sourcing virtual environment from $VENV"

# shellcheck disable=SC1090
source "$VENV/bin/activate"

if [[ -e "vars.sh" ]]; then
    echo "Local vars detected, including in environment"
    # shellcheck disable=SC1091
    source vars.sh
fi

if [[ -e "local.vars.sh" ]]; then
    echo "Local override vars found, including in environment"
    source local.vars.sh
fi

python newrelic-hipchat-lambda.py
