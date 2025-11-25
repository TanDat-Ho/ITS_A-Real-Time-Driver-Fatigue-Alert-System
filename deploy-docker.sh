#!/bin/bash
# Docker Deployment Script for Driver Fatigue Alert System

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🐳 Driver Fatigue Alert System - Docker Deployment${NC}"
echo "=================================================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed. Please install Docker Compose first.${NC}"
    exit 1
fi

# Function to build and run the application
build_and_run() {
    echo -e "${YELLOW}🔨 Building Docker image...${NC}"
    docker build -t driver-fatigue-alert:latest .
    
    echo -e "${YELLOW}🚀 Starting application...${NC}"
    
    # Check if we're on Linux/macOS for X11 forwarding
    if [[ "$OSTYPE" == "linux-gnu"* ]] || [[ "$OSTYPE" == "darwin"* ]]; then
        # Allow X11 forwarding
        xhost +local:docker 2>/dev/null || echo "Warning: Could not set X11 permissions"
        export DISPLAY=${DISPLAY:-:0}
    fi
    
    docker-compose up -d driver-fatigue-alert
    
    echo -e "${GREEN}✅ Application started successfully!${NC}"
    echo -e "${BLUE}📊 To view logs: docker-compose logs -f driver-fatigue-alert${NC}"
    echo -e "${BLUE}🛑 To stop: docker-compose down${NC}"
}

# Function to run in headless mode
run_headless() {
    echo -e "${YELLOW}🔨 Building Docker image for headless mode...${NC}"
    docker build -t driver-fatigue-alert:latest .
    
    echo -e "${YELLOW}🚀 Starting application in headless mode...${NC}"
    docker-compose --profile headless up -d driver-fatigue-alert-headless
    
    echo -e "${GREEN}✅ Application started in headless mode!${NC}"
    echo -e "${BLUE}📊 To view logs: docker-compose logs -f driver-fatigue-alert-headless${NC}"
    echo -e "${BLUE}🛑 To stop: docker-compose --profile headless down${NC}"
}

# Function to stop all services
stop_services() {
    echo -e "${YELLOW}🛑 Stopping all services...${NC}"
    docker-compose down
    docker-compose --profile headless down
    echo -e "${GREEN}✅ All services stopped.${NC}"
}

# Function to view logs
view_logs() {
    echo -e "${BLUE}📊 Viewing application logs...${NC}"
    docker-compose logs -f
}

# Function to clean up
cleanup() {
    echo -e "${YELLOW}🧹 Cleaning up Docker resources...${NC}"
    docker-compose down --rmi all --volumes --remove-orphans
    docker system prune -f
    echo -e "${GREEN}✅ Cleanup completed.${NC}"
}

# Main menu
case "${1:-}" in
    "build")
        build_and_run
        ;;
    "headless")
        run_headless
        ;;
    "stop")
        stop_services
        ;;
    "logs")
        view_logs
        ;;
    "cleanup")
        cleanup
        ;;
    *)
        echo -e "${YELLOW}Usage: $0 {build|headless|stop|logs|cleanup}${NC}"
        echo ""
        echo -e "${BLUE}Commands:${NC}"
        echo "  build    - Build and run with GUI support"
        echo "  headless - Run in headless mode (no GUI)"
        echo "  stop     - Stop all running services"
        echo "  logs     - View application logs"
        echo "  cleanup  - Clean up all Docker resources"
        echo ""
        echo -e "${YELLOW}Examples:${NC}"
        echo "  $0 build     # Run with GUI"
        echo "  $0 headless  # Run without GUI"
        echo "  $0 stop      # Stop services"
        exit 1
        ;;
esac
