#!/bin/bash

# Pull the latest code
sudo git pull origin main

sudo docker compose up -d --build

exit