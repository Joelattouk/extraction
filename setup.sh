#!/bin/bash

# Mise à jour et installation de Chromium + drivers
apt-get update
apt-get install -y --no-install-recommends \
    chromium \
    chromium-driver \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1

# Installation des dépendances Python
pip install --no-cache-dir -r requirements.txt
