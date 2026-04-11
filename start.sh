#!/usr/bin/env bash

uvicorn app.main:app --host 0.0.0.0 --port 10000 &
celery -A app.worker worker --loglevel=info --pool=solo