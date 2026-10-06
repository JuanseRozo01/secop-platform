@echo off

python -m compileall app tests

pytest -q