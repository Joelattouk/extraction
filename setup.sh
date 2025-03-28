#!/bin/bash

# Mise à jour et installation des dépendances système
apt-get update
apt-get install -y --no-install-recommends \
    chromium \
    chromium-chromedriver \
    libglib2.0-0 \
    libnss3 \
    libgconf-2-4 \
    libfontconfig1 \
    fonts-freefont-ttf \
    xvfb

# Configuration des liens symboliques
ln -s /usr/bin/chromium /usr/bin/google-chrome
ln -s /usr/lib/chromium/chromedriver /usr/bin/chromedriver

# Installation des dépendances Python
pip install --no-cache-dir -r requirements.txt
