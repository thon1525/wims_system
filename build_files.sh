#!/bin/bash
export DJANGO_SETTINGS_MODULE="wims.settings"
pip3 install -r requirements.txt  # Optional if @vercel/python handles it
python3 manage.py collectstatic --noinput