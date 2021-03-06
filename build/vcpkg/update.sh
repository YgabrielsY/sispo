#!/bin/bash

echo "Updating vcpkg start"

# Get latest git
cd ../../software/vcpkg || exit
git pull

# Install and integrate
./bootstrap-vcpkg.sh
./vcpkg integrate install

echo "Updating vcpkg done"
