#!/bin/bash

# Sentimatix Scraper EC2 Setup Script
# Supports: Ubuntu, Amazon Linux 2, Amazon Linux 2023

echo "🚀 Starting Sentimatix Scraper Setup..."

# Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
else
    OS="unknown"
fi

echo "📦 Detected OS: $OS"

if [[ "$OS" == "ubuntu" || "$OS" == "debian" ]]; then
    echo "🔧 Installing for Ubuntu/Debian..."
    sudo apt-get update
    sudo apt-get install -y ca-certificates curl gnupg lsb-release
    sudo mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

elif [[ "$OS" == "amzn" || "$OS" == "al2" || "$OS" == "al2023" ]]; then
    echo "🔧 Installing for Amazon Linux..."
    sudo yum update -y
    sudo yum install -y docker
    sudo systemctl start docker
    sudo systemctl enable docker
    # Install Docker Compose V2
    mkdir -p ~/.docker/cli-plugins/
    curl -SL https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64 -o ~/.docker/cli-plugins/docker-compose
    chmod +x ~/.docker/cli-plugins/docker-compose
else
    echo "❌ Unsupported OS: $OS. Please install Docker and Docker Compose manually."
    exit 1
fi

# 3. Enable Docker for current user
sudo usermod -aG docker $USER

echo "✅ Docker installed successfully."
echo "⚠️  Please LOG OUT and LOG BACK IN for Docker permissions to take effect."

# 4. Instructions for the user
echo ""
echo "--------------------------------------------------------"
echo "Next Steps:"
echo "1. Clone your repository: git clone <your-repo-url>"
echo "2. CD into the directory: cd workers/scrape/stock-news/x-news"
echo "3. Create .env file with your secrets."
echo "4. Transfer tg_session.session to scrapers/ folder."
echo "5. Build and run: docker compose up --build -d"
echo "--------------------------------------------------------"
