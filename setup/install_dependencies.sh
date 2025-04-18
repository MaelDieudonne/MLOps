#!/bin/bash


# Install Chrome
echo "Installing Chrome..."
sudo apt install -y wget gnupg

## Download Google's signing key using the newer method
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | gpg --dearmor | sudo tee /usr/share/keyrings/google-chrome.gpg > /dev/null

## Add Chrome repository using the newer method with signed-by option
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list

## Update package lists with the new repository
sudo apt update

## Install Chrome and verify installation
sudo apt install -y google-chrome-stable
google-chrome --version
echo "Google Chrome has been installed successfully!"


# Set time zone
echo "Setting timezone to Europe/Paris..."
sudo DEBIAN_FRONTEND=noninteractive apt install -y tzdata
sudo ln -sf /usr/share/zoneinfo/Europe/Paris /etc/localtime
echo "Verifying timezone using date:"
date


# Install Python and dependencies with Poetry
echo "Installing Python and Poetry..."
sudo apt-get -y update
sudo apt-get install -y python3 python3-pip curl

curl -sSL https://install.python-poetry.org | python3 -
export PATH="$HOME/.local/bin:$PATH"

echo "Installing dependencies via Poetry..."
poetry install


# Create the tables and restoring backup
poetry run python -m setup.db_init


# Launch the scheduler
poetry run python scheduler.py &
