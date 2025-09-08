#!/bin/bash

# Script para executar Python com ambiente virtual
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
WASABI_DIR="$(dirname "$SCRIPT_DIR")"
VENV_PATH="$WASABI_DIR/.venv"

# Ativar ambiente virtual se existir
if [ -d "$VENV_PATH" ]; then
    source "$VENV_PATH/bin/activate"
fi

# Executar o comando Python
python3 "$@"