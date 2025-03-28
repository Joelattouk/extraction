#!/bin/bash

# Mise à jour des paquets système et installation des dépendances nécessaires pour Selenium
apt-get update
apt-get install -y libglib2.0-0 libsm6 libxext6 libxrender1

# Installer les dépendances Python spécifiées dans requirements.txt
pip install -r requirements.txt
