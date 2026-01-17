# ========================================
# Concurrent Request Test Script
# Tests 5 simultaneous PDF generation requests
# ========================================

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Docker RQ Concurrent Request Test" -ForegroundColor Cyan
Write-Host "  Testing 5 simultaneous requests..." -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Test Type Selection
Write-Host "Select test type:" -ForegroundColor Yellow
Write-Host "  1. Top Agents Report (generate-agents-report)" -ForegroundColor White
Write-Host "  2. Top Leasing Agencies Report (generate-agency-report)" -ForegroundColor White
Write-Host ""
$testTypeChoice = Read-Host "Enter your choice (1 or 2)"

switch ($testTypeChoice) {
    "1" {
        $TEST_TYPE = "agents"
        $TEST_NAME = "Top Agents Report"
        $ENDPOINT_PATH = "/api/generate-agents-report"
        Write-Host "[INFO] Selected: $TEST_NAME" -ForegroundColor Green
    }
    "2" {
        $TEST_TYPE = "agencies"
        $TEST_NAME = "Top Leasing Agencies Report"
        $ENDPOINT_PATH = "/api/generate-agency-report"
        Write-Host "[INFO] Selected: $TEST_NAME" -ForegroundColor Green
    }
    default {
        Write-Host "[ERROR] Invalid choice. Defaulting to Top Agents Report." -ForegroundColor Red
        $TEST_TYPE = "agents"
        $TEST_NAME = "Top Agents Report"
        $ENDPOINT_PATH = "/api/generate-agents-report"
    }
}
Write-Host ""

# Server Selection
Write-Host "Select target server:" -ForegroundColor Yellow
Write-Host "  1. Local (localhost:8000)" -ForegroundColor White
Write-Host "  2. Production (65.108.146.173)" -ForegroundColor White
Write-Host ""
$serverChoice = Read-Host "Enter your choice (1 or 2)"

switch ($serverChoice) {
    "1" {
        $API_BASE_URL = "http://localhost:8000"
        $SERVER_NAME = "Local"
        Write-Host "[INFO] Testing LOCAL server: $API_BASE_URL" -ForegroundColor Green
    }
    "2" {
        $API_BASE_URL = "http://65.108.146.173"
        $SERVER_NAME = "Production"
        Write-Host "[INFO] Testing PRODUCTION server: $API_BASE_URL" -ForegroundColor Green
    }
    default {
        Write-Host "[ERROR] Invalid choice. Defaulting to Local server." -ForegroundColor Red
        $API_BASE_URL = "http://localhost:8000"
        $SERVER_NAME = "Local"
    }
}

$API_URL = "$API_BASE_URL$ENDPOINT_PATH"
$STATUS_URL = "$API_BASE_URL/api/job-status"
Write-Host ""

# Define all available requests for AGENTS
$agentRequests = @(
    @{
        name = "Kellyville, NSW"
        body = @{
            suburb = "Kellyville"
            state = "NSW"
            property_types = $null
            min_bedrooms = 1
            max_bedrooms = $null
            min_bathrooms = 1
            max_bathrooms = $null
            min_carspaces = 1
            max_carspaces = $null
            include_surrounding_suburbs = $false
            post_code = "2155"
            region = $null
            area = $null
            min_land_area = $null
            max_land_area = $null
            home_owner_pricing = "Less than `$500k"
        }
    },
    @{
        name = "Wellington Point, QLD"
        body = @{
            suburb = "Wellington Point"
            state = "QLD"
            property_types = $null
            min_bedrooms = 1
            max_bedrooms = $null
            min_bathrooms = 1
            max_bathrooms = $null
            min_carspaces = 1
            max_carspaces = $null
            include_surrounding_suburbs = $false
            post_code = "4160"
            region = $null
            area = $null
            min_land_area = $null
            max_land_area = $null
            home_owner_pricing = "`$1m-`$1.5m"
        }
    },
    @{
        name = "Frankston, VIC"
        body = @{
            suburb = "Frankston"
            state = "VIC"
            property_types = $null
            min_bedrooms = 1
            max_bedrooms = $null
            min_bathrooms = 1
            max_bathrooms = $null
            min_carspaces = 1
            max_carspaces = $null
            include_surrounding_suburbs = $false
            post_code = "3199"
            region = $null
            area = $null
            min_land_area = $null
            max_land_area = $null
            home_owner_pricing = "`$500k-`$1m"
        }
    },
    @{
        name = "Seaford Rise, SA"
        body = @{
            suburb = "Seaford rise"
            state = "SA"
            property_types = $null
            min_bedrooms = 1
            max_bedrooms = $null
            min_bathrooms = 1
            max_bathrooms = $null
            min_carspaces = 1
            max_carspaces = $null
            include_surrounding_suburbs = $false
            post_code = "5169"
            region = $null
            area = $null
            min_land_area = $null
            max_land_area = $null
            home_owner_pricing = "`$1m-`$1.5m"
        }
    },
    @{
        name = "Kingswood, NSW"
        body = @{
            suburb = "kingswood"
            state = "NSW"
            property_types = $null
            min_bedrooms = 1
            max_bedrooms = $null
            min_bathrooms = 1
            max_bathrooms = $null
            min_carspaces = 1
            max_carspaces = $null
            include_surrounding_suburbs = $false
            post_code = "2747"
            region = $null
            area = $null
            min_land_area = $null
            max_land_area = $null
            home_owner_pricing = "`$1.5m-`$2m"
        }
    },
    @{
        name = "South Penrith, NSW"
        body = @{
            suburb = "South Penrith"
            state = "NSW"
            property_types = $null
            min_bedrooms = 1
            max_bedrooms = $null
            min_bathrooms = 1
            max_bathrooms = $null
            min_carspaces = 1
            max_carspaces = $null
            include_surrounding_suburbs = $false
            post_code = "2750"
            region = $null
            area = $null
            min_land_area = $null
            max_land_area = $null
            home_owner_pricing = "`$2m-`$2.5m"
        }
    },
    @{
        name = "Winston Hills, NSW"
        body = @{
            suburb = "Winston Hills"
            state = "NSW"
            property_types = $null
            min_bedrooms = 1
            max_bedrooms = $null
            min_bathrooms = 1
            max_bathrooms = $null
            min_carspaces = 1
            max_carspaces = $null
            include_surrounding_suburbs = $false
            post_code = "2153"
            region = $null
            area = $null
            min_land_area = $null
            max_land_area = $null
            home_owner_pricing = "`$2.5m-`$3m"
        }
    },
    @{
        name = "Clovelly, NSW (Deduplication Test)"
        body = @{
            suburb = "Clovelly"
            state = "NSW"
            property_types = $null
            min_bedrooms = 1
            max_bedrooms = $null
            min_bathrooms = 1
            max_bathrooms = $null
            min_carspaces = 1
            max_carspaces = $null
            include_surrounding_suburbs = $false
            post_code = "2031"
            region = $null
            area = $null
            min_land_area = $null
            max_land_area = $null
            home_owner_pricing = "`$2.5m-`$3m"
        }
    },
    @{
        name = "Double Bay, NSW (High-End Test)"
        body = @{
            suburb = "Double Bay"
            state = "NSW"
            property_types = $null
            min_bedrooms = 1
            max_bedrooms = $null
            min_bathrooms = 1
            max_bathrooms = $null
            min_carspaces = 1
            max_carspaces = $null
            include_surrounding_suburbs = $false
            post_code = "2028"
            region = $null
            area = $null
            min_land_area = $null
            max_land_area = $null
            home_owner_pricing = "`$3m-`$3.5m"
        }
    },
    @{
        name = "Mosman, NSW (Premium Test)"
        body = @{
            suburb = "Mosman"
            state = "NSW"
            property_types = $null
            min_bedrooms = 1
            max_bedrooms = $null
            min_bathrooms = 1
            max_bathrooms = $null
            min_carspaces = 1
            max_carspaces = $null
            include_surrounding_suburbs = $false
            post_code = "2088"
            region = $null
            area = $null
            min_land_area = $null
            max_land_area = $null
            home_owner_pricing = "`$3.5m-`$4m"
        }
    },
    @{
        name = "Vaucluse, NSW (Luxury Test)"
        body = @{
            suburb = "Vaucluse"
            state = "NSW"
            property_types = $null
            min_bedrooms = 1
            max_bedrooms = $null
            min_bathrooms = 1
            max_bathrooms = $null
            min_carspaces = 1
            max_carspaces = $null
            include_surrounding_suburbs = $false
            post_code = "2030"
            region = $null
            area = $null
            min_land_area = $null
            max_land_area = $null
            home_owner_pricing = "`$4m-`$6m"
        }
    },
    @{
        name = "Point Piper, NSW (Ultra-Luxury Test)"
        body = @{
            suburb = "Point Piper"
            state = "NSW"
            property_types = $null
            min_bedrooms = 1
            max_bedrooms = $null
            min_bathrooms = 1
            max_bathrooms = $null
            min_carspaces = 1
            max_carspaces = $null
            include_surrounding_suburbs = $false
            post_code = "2027"
            region = $null
            area = $null
            min_land_area = $null
            max_land_area = $null
            home_owner_pricing = "`$6m-`$8m"
        }
    },
    @{
        name = "Bellevue Hill, NSW (Top-Tier Test)"
        body = @{
            suburb = "Bellevue Hill"
            state = "NSW"
            property_types = $null
            min_bedrooms = 1
            max_bedrooms = $null
            min_bathrooms = 1
            max_bathrooms = $null
            min_carspaces = 1
            max_carspaces = $null
            include_surrounding_suburbs = $false
            post_code = "2023"
            region = $null
            area = $null
            min_land_area = $null
            max_land_area = $null
            home_owner_pricing = "`$8m-`$10m"
        }
    },
    @{
        name = "Toorak, VIC (Ultra-Premium Test)"
        body = @{
            suburb = "Toorak"
            state = "VIC"
            property_types = $null
            min_bedrooms = 1
            max_bedrooms = $null
            min_bathrooms = 1
            max_bathrooms = $null
            min_carspaces = 1
            max_carspaces = $null
            include_surrounding_suburbs = $false
            post_code = "3142"
            region = $null
            area = $null
            min_land_area = $null
            max_land_area = $null
            home_owner_pricing = "`$10m+"
        }
    }
)

# Define all available requests for LEASING AGENCIES
$agencyRequests = @(
    @{
        name = "Palm Beach, QLD (Leasing)"
        body = @{
            suburb = "Palm Beach"
            state = "QLD"
            property_types = $null
            min_bedrooms = 1
            max_bedrooms = $null
            min_bathrooms = 1
            max_bathrooms = $null
            min_carspaces = 1
            max_carspaces = $null
            include_surrounding_suburbs = $false
            post_code = "4221"
            region = $null
            area = $null
            min_land_area = $null
            max_land_area = $null
        }
    },
    @{
        name = "Surfers Paradise, QLD (Leasing)"
        body = @{
            suburb = "Surfers Paradise"
            state = "QLD"
            property_types = $null
            min_bedrooms = 1
            max_bedrooms = $null
            min_bathrooms = 1
            max_bathrooms = $null
            min_carspaces = 1
            max_carspaces = $null
            include_surrounding_suburbs = $false
            post_code = "4217"
            region = $null
            area = $null
            min_land_area = $null
            max_land_area = $null
        }
    },
    @{
        name = "Broadbeach, QLD (Leasing)"
        body = @{
            suburb = "Broadbeach"
            state = "QLD"
            property_types = $null
            min_bedrooms = 1
            max_bedrooms = $null
            min_bathrooms = 1
            max_bathrooms = $null
            min_carspaces = 1
            max_carspaces = $null
            include_surrounding_suburbs = $false
            post_code = "4218"
            region = $null
            area = $null
            min_land_area = $null
            max_land_area = $null
        }
    },
    @{
        name = "Southport, QLD (Leasing)"
        body = @{
            suburb = "Southport"
            state = "QLD"
            property_types = $null
            min_bedrooms = 1
            max_bedrooms = $null
            min_bathrooms = 1
            max_bathrooms = $null
            min_carspaces = 1
            max_carspaces = $null
            include_surrounding_suburbs = $false
            post_code = "4215"
            region = $null
            area = $null
            min_land_area = $null
            max_land_area = $null
        }
    },
    @{
        name = "Burleigh Heads, QLD (Leasing)"
        body = @{
            suburb = "Burleigh Heads"
            state = "QLD"
            property_types = $null
            min_bedrooms = 1
            max_bedrooms = $null
            min_bathrooms = 1
            max_bathrooms = $null
            min_carspaces = 1
            max_carspaces = $null
            include_surrounding_suburbs = $false
            post_code = "4220"
            region = $null
            area = $null
            min_land_area = $null
            max_land_area = $null
        }
    }
)

# Select the appropriate request list based on test type
if ($TEST_TYPE -eq "agents") {
    $allRequests = $agentRequests
} else {
    $allRequests = $agencyRequests
}

# Display available requests
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Available Test Requests - $TEST_NAME" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
for ($i = 0; $i -lt $allRequests.Count; $i++) {
    Write-Host "  $($i + 1). $($allRequests[$i].name)" -ForegroundColor White
}
Write-Host ""
Write-Host "Enter request numbers separated by commas (e.g., 1,2,3)" -ForegroundColor Yellow
Write-Host "Or press Enter to run ALL requests" -ForegroundColor Yellow
Write-Host ""
$requestSelection = Read-Host "Your selection"

# Parse selection
$requests = @()
if ([string]::IsNullOrWhiteSpace($requestSelection)) {
    # Run all requests
    $requests = $allRequests
    Write-Host "[INFO] Running ALL $($allRequests.Count) requests" -ForegroundColor Green
} else {
    # Parse comma-separated numbers
    $selectedIndices = $requestSelection -split ',' | ForEach-Object { $_.Trim() }
    
    foreach ($idx in $selectedIndices) {
        $index = [int]$idx - 1
        if ($index -ge 0 -and $index -lt $allRequests.Count) {
            $requests += $allRequests[$index]
            Write-Host "[INFO] Added: $($allRequests[$index].name)" -ForegroundColor Green
        } else {
            Write-Host "[WARNING] Invalid index: $idx (ignored)" -ForegroundColor Yellow
        }
    }
    
    if ($requests.Count -eq 0) {
        Write-Host "[ERROR] No valid requests selected. Exiting." -ForegroundColor Red
        exit 1
    }
}

# Test API connection first
Write-Host "[INFO] Testing API connection..." -ForegroundColor Yellow
try {
    # Try to connect - even 404 means API is running
    $testResponse = Invoke-WebRequest -Uri "$API_BASE_URL" -Method GET -TimeoutSec 5 -ErrorAction SilentlyContinue
    Write-Host "[OK] API is reachable!" -ForegroundColor Green
} catch {
    # Check if it's just a 404 (which means API is running)
    if ($_.Exception.Response.StatusCode.value__ -eq 404) {
        Write-Host "[OK] API is reachable!" -ForegroundColor Green
    } else {
        Write-Host "[ERROR] Cannot connect to API at $API_BASE_URL" -ForegroundColor Red
        if ($SERVER_NAME -eq "Local") {
            Write-Host "Make sure Docker containers are running:" -ForegroundColor Red
            Write-Host "  docker-compose -f docker-compose.local.yml up" -ForegroundColor Yellow
        } else {
            Write-Host "Make sure production server is accessible and containers are running." -ForegroundColor Red
        }
        exit 1
    }
}

Write-Host ""
Write-Host "Sending $($requests.Count) concurrent request(s) at: $(Get-Date -Format 'HH:mm:ss')" -ForegroundColor Cyan
Write-Host "--------------------------------------------" -ForegroundColor Gray

# Array to store job IDs and results
$jobResults = @()
$jobs = @()

# Send all selected requests concurrently using background jobs
for ($i = 0; $i -lt $requests.Count; $i++) {
    $req = $requests[$i]
    
    Write-Host "[$($i+1)] Sending: $($req.name)..." -ForegroundColor White
    
    # Create background job for each request
    $job = Start-Job -ScriptBlock {
        param($url, $body, $name)
        
        $bodyJson = $body | ConvertTo-Json -Depth 10
        
        try {
            $response = Invoke-RestMethod -Uri $url -Method Post `
                -ContentType "application/json" `
                -Body $bodyJson `
                -ErrorAction Stop
            
            return @{
                success = $true
                name = $name
                job_id = $response.job_id
                status = $response.status
                timestamp = Get-Date -Format 'HH:mm:ss'
            }
        } catch {
            return @{
                success = $false
                name = $name
                error = $_.Exception.Message
                timestamp = Get-Date -Format 'HH:mm:ss'
            }
        }
    } -ArgumentList $API_URL, $req.body, $req.name
    
    $jobs += $job
}

Write-Host ""
Write-Host "Waiting for all requests to complete..." -ForegroundColor Yellow

# Wait for all jobs and collect results
$results = $jobs | Wait-Job | Receive-Job

# Clean up jobs
$jobs | Remove-Job

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "           REQUEST RESULTS" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

$successCount = 0
$failCount = 0

foreach ($result in $results) {
    if ($result.success) {
        $successCount++
        Write-Host "[OK] $($result.name)" -ForegroundColor Green
        Write-Host "  Job ID: $($result.job_id)" -ForegroundColor Gray
        Write-Host "  Status: $($result.status)" -ForegroundColor Gray
        Write-Host "  Time: $($result.timestamp)" -ForegroundColor Gray
        
        $jobResults += @{
            name = $result.name
            job_id = $result.job_id
        }
    } else {
        $failCount++
        Write-Host "[FAIL] $($result.name)" -ForegroundColor Red
        Write-Host "  Error: $($result.error)" -ForegroundColor Red
        Write-Host "  Time: $($result.timestamp)" -ForegroundColor Gray
    }
    Write-Host ""
}

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "Summary: $successCount succeeded, $failCount failed" -ForegroundColor $(if ($failCount -eq 0) { "Green" } else { "Yellow" })
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

if ($successCount -gt 0) {
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host "     JOB STATUS TRACKING" -ForegroundColor Cyan
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host ""
    
    # Save job IDs to file for later reference
    $jobResults | ConvertTo-Json | Out-File "job_ids.json"
    Write-Host "[INFO] Job IDs saved to job_ids.json" -ForegroundColor Yellow
    Write-Host ""
    
    # Display check status commands
    Write-Host "Check individual job status:" -ForegroundColor Cyan
    foreach ($job in $jobResults) {
        Write-Host ""
        Write-Host "# $($job.name)" -ForegroundColor White
        Write-Host "Invoke-RestMethod -Uri `"$STATUS_URL/$($job.job_id)`"" -ForegroundColor Gray
    }
    
    Write-Host ""
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host ""
    
    # Offer to start monitoring
    Write-Host "Would you like to monitor job progress? (Y/N): " -ForegroundColor Yellow -NoNewline
    $monitor = Read-Host
    
    if ($monitor -eq "Y" -or $monitor -eq "y") {
        Write-Host ""
        Write-Host "Starting job monitoring (Press Ctrl+C to stop)..." -ForegroundColor Cyan
        Write-Host "Checking every 30 seconds..." -ForegroundColor Gray
        Write-Host ""
        
        $allCompleted = $false
        $checkCount = 0
        
        while (-not $allCompleted) {
            $checkCount++
            Start-Sleep -Seconds 30
            
            Write-Host "--------------------------------------------" -ForegroundColor Gray
            Write-Host "Check #$checkCount at $(Get-Date -Format 'HH:mm:ss')" -ForegroundColor Yellow
            Write-Host "--------------------------------------------" -ForegroundColor Gray
            
            $completedCount = 0
            $processingCount = 0
            $failedCount = 0
            
            foreach ($job in $jobResults) {
                try {
                    $status = Invoke-RestMethod -Uri "$STATUS_URL/$($job.job_id)"
                    
                    $statusSymbol = switch ($status.status) {
                        "completed" { "[OK]"; $completedCount++ }
                        "failed" { "[FAIL]"; $failedCount++ }
                        default { "[PROC]"; $processingCount++ }
                    }
                    
                    $color = switch ($status.status) {
                        "completed" { "Green" }
                        "failed" { "Red" }
                        default { "Yellow" }
                    }
                    
                    $progressPercent = $status.progress
                    Write-Host "$statusSymbol $($job.name): $($status.status) ($progressPercent%)" -ForegroundColor $color
                    
                    if ($status.status -eq "completed" -and $status.dropbox_url) {
                        Write-Host "  File: $($status.filename)" -ForegroundColor Gray
                    }
                    if ($status.status -eq "failed" -and $status.error) {
                        Write-Host "  Error: $($status.error)" -ForegroundColor Red
                    }
                    
                } catch {
                    Write-Host "[FAIL] $($job.name): Error checking status" -ForegroundColor Red
                }
            }
            
            Write-Host ""
            Write-Host "Status: $completedCount completed, $processingCount processing, $failedCount failed" -ForegroundColor Cyan
            
            if ($completedCount + $failedCount -eq $jobResults.Count) {
                $allCompleted = $true
                Write-Host ""
                Write-Host "============================================" -ForegroundColor Green
                Write-Host "  ALL JOBS COMPLETED!" -ForegroundColor Green
                Write-Host "============================================" -ForegroundColor Green
                Write-Host ""
                
                # Show final results
                Write-Host "Final Results:" -ForegroundColor Cyan
                foreach ($job in $jobResults) {
                    $status = Invoke-RestMethod -Uri "$STATUS_URL/$($job.job_id)"
                    if ($status.status -eq "completed") {
                        Write-Host ""
                        Write-Host "[OK] $($job.name)" -ForegroundColor Green
                        Write-Host "  Agent Report: $($status.dropbox_url)" -ForegroundColor Gray
                        if ($status.commission_dropbox_url) {
                            Write-Host "  Commission Report: $($status.commission_dropbox_url)" -ForegroundColor Gray
                            if ($status.commission_rate) {
                                Write-Host "  Commission Rate: $($status.commission_rate)" -ForegroundColor Cyan
                            }
                            if ($status.discount) {
                                Write-Host "  Discount: $($status.discount)" -ForegroundColor Cyan
                            }
                        }
                    } else {
                        Write-Host ""
                        Write-Host "[FAIL] $($job.name)" -ForegroundColor Red
                        Write-Host "  Error: $($status.error)" -ForegroundColor Red
                    }
                }
            }
        }
    } else {
        Write-Host ""
        Write-Host "[INFO] You can check job status manually using the commands above" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  REDIS MONITORING COMMANDS" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "To check Redis, open a new terminal and run:" -ForegroundColor Yellow
Write-Host ""

if ($SERVER_NAME -eq "Local") {
    Write-Host "# Connect to Redis (Local)" -ForegroundColor White
    Write-Host "docker-compose -f docker-compose.local.yml exec redis redis-cli" -ForegroundColor Gray
} else {
    Write-Host "# Connect to Production Redis (SSH first)" -ForegroundColor White
    Write-Host "ssh root@65.108.146.173" -ForegroundColor Gray
    Write-Host "cd /var/www/fastapi-app/AgentLink" -ForegroundColor Gray
    Write-Host "docker compose exec redis redis-cli" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Then inside Redis CLI:" -ForegroundColor White
Write-Host "  KEYS job:*                         # List all jobs" -ForegroundColor Gray
Write-Host "  LLEN rq:queue:agentlink-queue      # Check queue length" -ForegroundColor Gray
Write-Host "  LRANGE rq:queue:agentlink-queue 0 -1  # List queued jobs" -ForegroundColor Gray
Write-Host "  HGETALL job:JOB_ID                 # Get job details" -ForegroundColor Gray
Write-Host "  SMEMBERS rq:workers                # List active workers" -ForegroundColor Gray
Write-Host "  INFO stats                         # Redis statistics" -ForegroundColor Gray
Write-Host "  EXIT                               # Quit Redis CLI" -ForegroundColor Gray
Write-Host ""
Write-Host "Test completed at: $(Get-Date -Format 'HH:mm:ss')" -ForegroundColor Cyan
Write-Host "Server tested: $SERVER_NAME ($API_BASE_URL)" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
