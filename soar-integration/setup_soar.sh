#!/bin/bash
# Setup script for Shuffle SOAR and dependencies (VM-1)

echo "Update and Install dependencies"
sudo apt update -y
sudo apt install -y python3-pip git

echo "Installing Python packages for AI Pipeline"
pip3 install flask pandas joblib scikit-learn

echo "Installing Docker..."
curl -fsSL https://get.docker.com | sudo bash

echo "Installing Docker Compose Plugin..."
sudo apt install docker-compose-plugin -y

echo "Cloning Shuffle..."
mkdir -p ~/soc-project/soar
cd ~/soc-project/soar
if [ ! -d "Shuffle" ]; then
    git clone https://github.com/Shuffle/Shuffle.git
fi

echo "Starting Shuffle SOAR..."
cd Shuffle
sudo docker compose up -d

echo "Shuffle SOAR is starting! Give it a few minutes."
echo "You can check status with: sudo docker ps"
echo "Don't forget to run app.py (from ai-model directory) to start the AI Pipeline API."
