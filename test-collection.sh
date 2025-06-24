#!/bin/bash

# Test script for openrail.switchos collection
# This script allows testing without building tar.gz files

echo "Testing openrail.switchos collection..."
echo "========================================"

# Set the collections path to include the current directory
export ANSIBLE_COLLECTIONS_PATH=$(pwd):~/.ansible/collections

# Run the test playbook
ansible-playbook openrail/switchos/playbook.yml

echo ""
echo "Test completed!"
