#!/bin/bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
fastapi dev app/main.py