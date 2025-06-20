#!/bin/bash
export DB_USER=postgres
export DB_PASS=postgres
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=border_db

uvicorn app.main:app --reload
