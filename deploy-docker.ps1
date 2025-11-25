# Docker Deployment Script for Driver Fatigue Alert System (Windows)
# PowerShell version

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("build", "headless", "stop", "logs", "cleanup")]
    [string]$Action = "help"
)

# Colors for output
function Write-ColorOutput($ForegroundColor) {
    if ($host.UI.RawUI.ForegroundColor) {
        $fc = $host.UI.RawUI.ForegroundColor
        $host.UI.RawUI.ForegroundColor = $ForegroundColor
        if ($args) {
            Write-Output $args
        } else {
            $input | Write-Output
        }
        $host.UI.RawUI.ForegroundColor = $fc
    } else {
        if ($args) {
            Write-Output $args
        } else {
            $input | Write-Output
        }
    }
}

function Write-Info($message) {
    Write-ColorOutput Blue "🐳 $message"
}

function Write-Success($message) {
    Write-ColorOutput Green "✅ $message"
}

function Write-Warning($message) {
    Write-ColorOutput Yellow "⚠️ $message"
}

function Write-Error($message) {
    Write-ColorOutput Red "❌ $message"
}

Write-Info "Driver Fatigue Alert System - Docker Deployment"
Write-Output "=================================================="

# Check if Docker is installed
try {
    docker --version | Out-Null
} catch {
    Write-Error "Docker is not installed. Please install Docker Desktop first."
    exit 1
}

# Check if Docker Compose is available
try {
    docker-compose --version | Out-Null
} catch {
    try {
        docker compose version | Out-Null
    } catch {
        Write-Error "Docker Compose is not available. Please install Docker Compose."
        exit 1
    }
}

function Build-And-Run {
    Write-Warning "Building Docker image..."
    docker build -t driver-fatigue-alert:latest .
    
    Write-Warning "Starting application..."
    docker-compose up -d driver-fatigue-alert
    
    Write-Success "Application started successfully!"
    Write-Info "To view logs: docker-compose logs -f driver-fatigue-alert"
    Write-Info "To stop: docker-compose down"
}

function Run-Headless {
    Write-Warning "Building Docker image for headless mode..."
    docker build -t driver-fatigue-alert:latest .
    
    Write-Warning "Starting application in headless mode..."
    docker-compose --profile headless up -d driver-fatigue-alert-headless
    
    Write-Success "Application started in headless mode!"
    Write-Info "To view logs: docker-compose logs -f driver-fatigue-alert-headless"
    Write-Info "To stop: docker-compose --profile headless down"
}

function Stop-Services {
    Write-Warning "Stopping all services..."
    docker-compose down
    docker-compose --profile headless down
    Write-Success "All services stopped."
}

function View-Logs {
    Write-Info "Viewing application logs..."
    docker-compose logs -f
}

function Cleanup-Resources {
    Write-Warning "Cleaning up Docker resources..."
    docker-compose down --rmi all --volumes --remove-orphans
    docker system prune -f
    Write-Success "Cleanup completed."
}

switch ($Action) {
    "build" {
        Build-And-Run
    }
    "headless" {
        Run-Headless
    }
    "stop" {
        Stop-Services
    }
    "logs" {
        View-Logs
    }
    "cleanup" {
        Cleanup-Resources
    }
    default {
        Write-Warning "Usage: .\deploy-docker.ps1 -Action {build|headless|stop|logs|cleanup}"
        Write-Output ""
        Write-Info "Commands:"
        Write-Output "  build    - Build and run with GUI support"
        Write-Output "  headless - Run in headless mode (no GUI)"
        Write-Output "  stop     - Stop all running services"
        Write-Output "  logs     - View application logs"
        Write-Output "  cleanup  - Clean up all Docker resources"
        Write-Output ""
        Write-Warning "Examples:"
        Write-Output "  .\deploy-docker.ps1 -Action build     # Run with GUI"
        Write-Output "  .\deploy-docker.ps1 -Action headless  # Run without GUI"
        Write-Output "  .\deploy-docker.ps1 -Action stop      # Stop services"
    }
}
