#!/bin/sh

CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

if [ "$CURRENT_BRANCH" = "main" ]; then
  # Run ruff check if git branch = "main"
  poetry run ruff check --fix --unsafe-fixes telethon-mongo-session
fi
 
