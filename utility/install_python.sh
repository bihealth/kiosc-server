#!/usr/bin/env bash

echo "***********************************************"
echo "Installing Python 3.14"
echo "***********************************************"
apt-get -y update
apt-get -y install software-properties-common
add-apt-repository -y ppa:deadsnakes/ppa
apt-get -y update
apt-get -y install python3.14 python3.14-dev python3.14-venv python3.14-gdbm
