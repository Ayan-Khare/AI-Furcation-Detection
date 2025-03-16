#!/bin/bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker api.main:app --bind 0.0.0.0:8000 --timeout 0
