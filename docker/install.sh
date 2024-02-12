#!/bin/bash --login

# Make bashline configurations.
set -e
RESET='\033[0m'
COLOR='\033[1;32m'

function msg {
    echo -e "${COLOR}$(date): $1${RESET}"
}

function fail {
    msg "Error : $?"
    exit 1
}

function mcd {
    mkdir -p "$1" || fail
    cd "$1" || fail
}

function nvm_has {
    type "$1" > /dev/null 2>&1
}


PYTHON=python3

if ! nvm_has "yarn"; then
    corepack enable
fi

yarn set version stable
yarn install

${PYTHON} -m pip install pip wheel setuptools build --upgrade
${PYTHON} -m pip install .[dev]
