#!/bin/bash

export DJANGO_SETTINGS_MODULE=settings
export PYTHONPATH=~/pysec

python manage.py syncdb
python manage.py sec_import_index

python populateDB.py
