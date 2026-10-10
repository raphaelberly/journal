#!/usr/bin/env bash

echo "### Stopping server..."
sudo service supervisor stop

echo "### Pulling changes from pi-hub..."
git pull origin master

echo "### Syncing the environment with uv.lock..."
uv sync --frozen

echo "### Starting server..."
sudo service supervisor start

echo "### All done."