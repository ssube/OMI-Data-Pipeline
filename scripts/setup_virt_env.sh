#!/bin/bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install ./modules/odr_core
pip install -e ./modules/odr_api
pip install -r ./requirements-dev.txt
pre-commit install
