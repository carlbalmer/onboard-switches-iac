#!/bin/bash

# Test script for openrail.switchos collection
# This script allows testing without building tar.gz files

echo "Testing openrail.switchos collection..."
echo "========================================"

# Set the collections path to include the current directory
ansible-galaxy collection build --force
ansible-galaxy collection install openrail-switchos-1.0.0.tar.gz --force

# Run the test playbook
ansible-playbook playbook.yml

echo ""
echo "Test completed!"
