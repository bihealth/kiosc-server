#!/usr/bin/env bash

echo "***********************************************"
echo "Installing Python 3.13"
echo "***********************************************"
apt-get -y update
apt-get -y install software-properties-common
add-apt-repository -y ppa:deadsnakes/ppa
apt-get -y update
apt-get -y install python3.13 python3.13-dev python3.13-venv python3.13-gdbm
