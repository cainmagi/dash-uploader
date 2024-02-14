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

function nvm_default_install_dir {
    [ -z "${XDG_CONFIG_HOME-}" ] && printf %s "${HOME}/.nvm" || printf %s "${XDG_CONFIG_HOME}/nvm"
}

function nvm_install_dir {
    if [ -n "$NVM_DIR" ]; then
        printf %s "${NVM_DIR}"
    else
        nvm_default_install_dir
    fi
}

function install_nvm {
    msg "Installing NVM, version: $1"
    wget -O- https://raw.githubusercontent.com/nvm-sh/nvm/v$1/install.sh | bash || fail
}

function install_nodejs {
    msg "Installing Node.js, version: $1"
    RUN_NVM_DIR="$(nvm_install_dir)" || fail
    msg "Finding NVM in: ${RUN_NVM_DIR}".
    bash -c ". $RUN_NVM_DIR/nvm.sh \
    && . $RUN_NVM_DIR/bash_completion \
    && nvm install v$1 \
    && nvm alias default v$1 \
    && nvm use default" || fail
}

function install_nodejs_lts {
    msg "Installing Node.js, LTS version"
    RUN_NVM_DIR="$(nvm_install_dir)" || fail
    msg "Finding NVM in: ${RUN_NVM_DIR}".
    bash -c ". $RUN_NVM_DIR/nvm.sh \
    && . $RUN_NVM_DIR/bash_completion \
    && nvm install --lts --latest-npm \
    && nvm use --lts" || fail
}

if nvm_has "python"; then
    PYTHON=python
else
    if nvm_has "python3"; then
        PYTHON=python3
    else
        msgerr "Fail to find Python3 in the base image, stop the build."
        exit 1
    fi
fi

INSTALL_MODE=$1

# Required packages
msg "Install dependencies by APT."
apt-get -y update || fail && apt-get -y install \
    apt-utils apt-transport-https curl wget \
    gnupg2 lsb-release ${EXTRA_PY} || fail

if ! nvm_has "lsb_release"; then
    msg_err "lsb_release does not exist. This should not happen. Please contact the author for technical supports."
    exit 1
fi

# Check the OS version
NAME_OS=$(lsb_release -is)

if [ "x${NAME_OS}" = "xUbuntu" ] || [ "x${NAME_OS}" = "xDebian" ]; then
	msg "Pass the OS check. Current OS: ${NAME_OS}."
else
	msg_err "The base image is an unknown OS, this dockerfile does not support it: ${NAME_OS}."
fi

msg "Install developer's dependencies by APT."
if [ "x${INSTALL_MODE}" = "xdev" ]; then
	apt-get -y upgrade || fail
	apt-get -y update -qq || fail && apt-get -y install git-core || fail
	msg "Successfully install developer's dependencies."
fi

apt-get -y update || fail && apt-get -y upgrade || fail && apt-get -y \
    dist-upgrade || fail && apt-get -y autoremove || fail && apt-get -y \
    autoclean || fail

msg "Install NodeJS"

if ! nvm_has "npm"; then
    if ! nvm_has "nvm"; then
        install_nvm 0.39.7 || fail
    fi
    install_nodejs_lts || fail
fi

msg "Enable Yarn v4+."

bash --login ./install-yarn.sh || fail

msg "Install Python packages."

${PYTHON} -m pip install --compile --no-cache-dir pip wheel setuptools build --upgrade || fail

if [ "x${INSTALL_MODE}" = "xdev" ]; then
    msg "Install developer's Python Packages."
    ${PYTHON} -m pip install --compile --no-cache-dir .[dev] || fail
else  # default
    msg "Install Basic Packages."
    ${PYTHON} -m pip install --compile --no-cache-dir . || fail
fi
