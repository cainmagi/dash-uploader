#!/bin/bash --login

# Make bashline configurations.
set -e
RESET='\033[0m'
COLOR='\033[1;32m'
COLOR_ERR='\033[1;31m'

function msg {
    echo -e "${COLOR}$(date): $1${RESET}"
}

function msgerr {
    echo -e "${COLOR_ERR}$(date): $1${RESET}"
}

function fail {
    msgerr "Error : $?"
    exit 1
}

function mcd {
    mkdir -p "$1" || fail
    cd "$1" || fail
}

function nvm_has {
    type "$1" > /dev/null 2>&1
}

if ! nvm_has "yarn"; then
    corepack enable || fail
fi
yarn set version stable || fail
yarn install || fail
