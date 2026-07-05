#!/bin/bash

# Environment checker
if ! command -v python &> /dev/null
then
    echo "Python is not installed."
    exit
fi

echo "SDD Environment Initialized"
