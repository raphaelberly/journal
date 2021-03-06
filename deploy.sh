#!/usr/bin/env bash

echo "### Stopping server..."
sudo service supervisor stop

echo "### Pulling changes from pi-hub..."
git pull pi-hub master

echo "### Starting server..."
sudo service supervisor start

echo "### All done."