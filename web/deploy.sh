#!/bin/bash

# Financial Transcription Web App Deployment Script

echo "=================================================="
echo "🚀 Financial Transcription Web App Deployment"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed. Please install Docker first.${NC}"
    echo "Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed. Please install Docker Compose first.${NC}"
    echo "Visit: https://docs.docker.com/compose/install/"
    exit 1
fi

echo -e "${GREEN}✅ Docker and Docker Compose are installed${NC}"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  No .env file found. Creating one...${NC}"
    
    echo "OPENAI_API_KEY=" > .env
    echo "SENDER_EMAIL=" >> .env
    echo "SENDER_PASSWORD=" >> .env
    echo "OUTPUT_EMAIL=" >> .env
    
    echo -e "${BLUE}📝 Created .env file. Please configure your settings:${NC}"
    echo "1. Edit .env file with your OpenAI API key"
    echo "2. Optionally add email settings for reports"
    echo "3. Or configure these settings in the web interface after deployment"
    echo
fi

# Create necessary directories
echo -e "${BLUE}📁 Creating directories...${NC}"
mkdir -p uploads output

# Build and start the application
echo -e "${BLUE}🔨 Building Docker image...${NC}"
docker-compose build

echo -e "${BLUE}🚀 Starting the application...${NC}"
docker-compose up -d

# Wait for the application to start
echo -e "${BLUE}⏳ Waiting for application to start...${NC}"
sleep 10

# Check if the application is running
if curl -f http://localhost:5000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Application is running successfully!${NC}"
    echo
    echo "=================================================="
    echo -e "${GREEN}🎉 DEPLOYMENT COMPLETE!${NC}"
    echo "=================================================="
    echo
    echo -e "${BLUE}📖 Access your application at:${NC}"
    echo "   🌐 Web Interface: http://localhost:5000"
    echo "   ⚙️  Settings: http://localhost:5000/settings"
    echo
    echo -e "${BLUE}📋 Next Steps:${NC}"
    echo "1. Open http://localhost:5000 in your browser"
    echo "2. Go to Settings and configure your OpenAI API key"
    echo "3. Optionally configure email settings for reports"
    echo "4. Start transcribing your financial audio content!"
    echo
    echo -e "${BLUE}🛠️  Useful Commands:${NC}"
    echo "   • View logs: docker-compose logs -f"
    echo "   • Stop app: docker-compose down"
    echo "   • Restart: docker-compose restart"
    echo "   • Update: docker-compose pull && docker-compose up -d"
    echo
else
    echo -e "${RED}❌ Application failed to start. Check logs:${NC}"
    echo "docker-compose logs"
    exit 1
fi