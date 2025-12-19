# ========================================
# Docker Cleanup & Management Script
# Provides menu-driven Docker operations
# ========================================

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Docker Cleanup & Management Tool" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

function Show-Menu {
    Write-Host "Select an option:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  --- CONTAINER OPERATIONS ---" -ForegroundColor Cyan
    Write-Host "  1. List all containers (running & stopped)" -ForegroundColor White
    Write-Host "  2. Stop all running containers" -ForegroundColor White
    Write-Host "  3. Remove all stopped containers" -ForegroundColor White
    Write-Host "  4. Stop AND remove all containers" -ForegroundColor Red
    Write-Host ""
    Write-Host "  --- IMAGE OPERATIONS ---" -ForegroundColor Cyan
    Write-Host "  5. List all images" -ForegroundColor White
    Write-Host "  6. Remove dangling images (unused)" -ForegroundColor White
    Write-Host "  7. Remove ALL images (CAUTION!)" -ForegroundColor Red
    Write-Host ""
    Write-Host "  --- VOLUME & NETWORK ---" -ForegroundColor Cyan
    Write-Host "  8. List volumes" -ForegroundColor White
    Write-Host "  9. Remove unused volumes" -ForegroundColor White
    Write-Host "  10. Remove unused networks" -ForegroundColor White
    Write-Host ""
    Write-Host "  --- FULL CLEANUP ---" -ForegroundColor Magenta
    Write-Host "  11. System prune (containers, networks, dangling images)" -ForegroundColor Yellow
    Write-Host "  12. FULL prune (everything including volumes)" -ForegroundColor Red
    Write-Host "  13. Nuclear option - Remove EVERYTHING" -ForegroundColor Red
    Write-Host ""
    Write-Host "  --- DISK USAGE ---" -ForegroundColor Cyan
    Write-Host "  14. Show Docker disk usage" -ForegroundColor White
    Write-Host ""
    Write-Host "  --- PROJECT SPECIFIC ---" -ForegroundColor Green
    Write-Host "  15. Stop AgentLink containers only" -ForegroundColor White
    Write-Host "  16. Remove AgentLink containers & images" -ForegroundColor White
    Write-Host "  17. Rebuild AgentLink (clean rebuild)" -ForegroundColor White
    Write-Host ""
    Write-Host "  Q. Quit" -ForegroundColor Gray
    Write-Host ""
}

function Confirm-Action {
    param([string]$Message)
    Write-Host ""
    Write-Host "$Message (Y/N): " -ForegroundColor Yellow -NoNewline
    $confirm = Read-Host
    return ($confirm -eq "Y" -or $confirm -eq "y")
}

function Show-DockerDiskUsage {
    Write-Host ""
    Write-Host "Docker Disk Usage:" -ForegroundColor Cyan
    Write-Host "==================" -ForegroundColor Cyan
    docker system df
    Write-Host ""
}

# Main loop
$running = $true
while ($running) {
    Show-Menu
    $choice = Read-Host "Enter your choice"
    
    switch ($choice) {
        "1" {
            Write-Host ""
            Write-Host "All Containers:" -ForegroundColor Cyan
            docker ps -a --format "table {{.ID}}\t{{.Names}}\t{{.Status}}\t{{.Image}}"
            Write-Host ""
        }
        "2" {
            Write-Host ""
            Write-Host "Stopping all running containers..." -ForegroundColor Yellow
            $containers = docker ps -q
            if ($containers) {
                docker stop $containers
                Write-Host "All containers stopped." -ForegroundColor Green
            } else {
                Write-Host "No running containers found." -ForegroundColor Gray
            }
            Write-Host ""
        }
        "3" {
            Write-Host ""
            Write-Host "Removing all stopped containers..." -ForegroundColor Yellow
            docker container prune -f
            Write-Host "Stopped containers removed." -ForegroundColor Green
            Write-Host ""
        }
        "4" {
            if (Confirm-Action "This will STOP and REMOVE all containers. Continue?") {
                Write-Host ""
                Write-Host "Stopping all containers..." -ForegroundColor Yellow
                $containers = docker ps -q
                if ($containers) {
                    docker stop $containers
                }
                Write-Host "Removing all containers..." -ForegroundColor Yellow
                docker container prune -f
                Write-Host "All containers stopped and removed." -ForegroundColor Green
            }
            Write-Host ""
        }
        "5" {
            Write-Host ""
            Write-Host "All Images:" -ForegroundColor Cyan
            docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.ID}}"
            Write-Host ""
        }
        "6" {
            Write-Host ""
            Write-Host "Removing dangling (unused) images..." -ForegroundColor Yellow
            docker image prune -f
            Write-Host "Dangling images removed." -ForegroundColor Green
            Write-Host ""
        }
        "7" {
            if (Confirm-Action "This will remove ALL images. You'll need to rebuild everything. Continue?") {
                Write-Host ""
                Write-Host "Removing all images..." -ForegroundColor Yellow
                docker image prune -a -f
                Write-Host "All images removed." -ForegroundColor Green
            }
            Write-Host ""
        }
        "8" {
            Write-Host ""
            Write-Host "All Volumes:" -ForegroundColor Cyan
            docker volume ls
            Write-Host ""
        }
        "9" {
            Write-Host ""
            Write-Host "Removing unused volumes..." -ForegroundColor Yellow
            docker volume prune -f
            Write-Host "Unused volumes removed." -ForegroundColor Green
            Write-Host ""
        }
        "10" {
            Write-Host ""
            Write-Host "Removing unused networks..." -ForegroundColor Yellow
            docker network prune -f
            Write-Host "Unused networks removed." -ForegroundColor Green
            Write-Host ""
        }
        "11" {
            if (Confirm-Action "System prune will remove stopped containers, unused networks, and dangling images. Continue?") {
                Write-Host ""
                Write-Host "Running system prune..." -ForegroundColor Yellow
                docker system prune -f
                Write-Host "System prune complete." -ForegroundColor Green
                Show-DockerDiskUsage
            }
            Write-Host ""
        }
        "12" {
            if (Confirm-Action "FULL prune will remove everything including volumes. Data will be lost! Continue?") {
                Write-Host ""
                Write-Host "Running full system prune with volumes..." -ForegroundColor Yellow
                docker system prune -a --volumes -f
                Write-Host "Full prune complete." -ForegroundColor Green
                Show-DockerDiskUsage
            }
            Write-Host ""
        }
        "13" {
            if (Confirm-Action "NUCLEAR OPTION: This will remove ALL containers, images, volumes, and networks. Continue?") {
                if (Confirm-Action "Are you REALLY sure? This cannot be undone!") {
                    Write-Host ""
                    Write-Host "Stopping all containers..." -ForegroundColor Red
                    $containers = docker ps -q
                    if ($containers) {
                        docker stop $containers
                    }
                    Write-Host "Removing all containers..." -ForegroundColor Red
                    docker rm -f $(docker ps -aq) 2>$null
                    Write-Host "Removing all images..." -ForegroundColor Red
                    docker rmi -f $(docker images -q) 2>$null
                    Write-Host "Removing all volumes..." -ForegroundColor Red
                    docker volume rm -f $(docker volume ls -q) 2>$null
                    Write-Host "Removing all networks..." -ForegroundColor Red
                    docker network prune -f
                    Write-Host ""
                    Write-Host "============================================" -ForegroundColor Green
                    Write-Host "  Nuclear cleanup complete!" -ForegroundColor Green
                    Write-Host "============================================" -ForegroundColor Green
                    Show-DockerDiskUsage
                }
            }
            Write-Host ""
        }
        "14" {
            Show-DockerDiskUsage
        }
        "15" {
            Write-Host ""
            Write-Host "Stopping AgentLink containers..." -ForegroundColor Yellow
            docker-compose -f docker-compose.local.yml down 2>$null
            docker-compose down 2>$null
            Write-Host "AgentLink containers stopped." -ForegroundColor Green
            Write-Host ""
        }
        "16" {
            if (Confirm-Action "This will remove AgentLink containers and images. Continue?") {
                Write-Host ""
                Write-Host "Stopping AgentLink containers..." -ForegroundColor Yellow
                docker-compose -f docker-compose.local.yml down --rmi all 2>$null
                docker-compose down --rmi all 2>$null
                Write-Host "AgentLink containers and images removed." -ForegroundColor Green
            }
            Write-Host ""
        }
        "17" {
            if (Confirm-Action "This will stop, remove, and rebuild AgentLink. Continue?") {
                Write-Host ""
                Write-Host "Stopping and removing AgentLink..." -ForegroundColor Yellow
                docker-compose -f docker-compose.local.yml down --rmi all -v 2>$null
                Write-Host ""
                Write-Host "Rebuilding AgentLink..." -ForegroundColor Yellow
                docker-compose -f docker-compose.local.yml build --no-cache
                Write-Host ""
                Write-Host "Starting AgentLink..." -ForegroundColor Yellow
                docker-compose -f docker-compose.local.yml up -d
                Write-Host ""
                Write-Host "AgentLink rebuilt and started." -ForegroundColor Green
            }
            Write-Host ""
        }
        "Q" { $running = $false }
        "q" { $running = $false }
        default {
            Write-Host ""
            Write-Host "Invalid option. Please try again." -ForegroundColor Red
            Write-Host ""
        }
    }
    
    if ($running) {
        Write-Host "Press Enter to continue..." -ForegroundColor Gray
        Read-Host
        Clear-Host
        Write-Host ""
        Write-Host "============================================" -ForegroundColor Cyan
        Write-Host "  Docker Cleanup & Management Tool" -ForegroundColor Cyan
        Write-Host "============================================" -ForegroundColor Cyan
        Write-Host ""
    }
}

Write-Host ""
Write-Host "Goodbye!" -ForegroundColor Cyan
Write-Host ""
