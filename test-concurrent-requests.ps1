# ========================================
# Concurrent Request Test Script
# Tests 5 simultaneous PDF generation requests
# ========================================

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Docker RQ Concurrent Request Test" -ForegroundColor Cyan
Write-Host "  Testing 5 simultaneous requests..." -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

$API_URL = "http://localhost:8000/api/generate-agents-report"

# Define all 5 requests
$requests = @(
    @{
        name = "Greenfields, WA"
        body = @{
            suburb = "Greenfields"
            state = "WA"
            property_types = $null
            min_bedrooms = 1
            max_bedrooms = $null
            min_bathrooms = 1
            max_bathrooms = $null
            min_carspaces = 1
            max_carspaces = $null
            include_surrounding_suburbs = $false
            post_code = "6174"
            region = $null
            area = $null
            min_land_area = $null
            max_land_area = $null
            home_owner_pricing = "`$1m-`$1.5m"
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
            home_owner_pricing = "`$500k-`$1m"
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
            home_owner_pricing = "`$500k-`$1m"
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
            home_owner_pricing = "`$1m-`$1.5m"
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
            home_owner_pricing = "`$1.5m-`$2m"
        }
    }
)

# Test API connection first
Write-Host "[INFO] Testing API connection..." -ForegroundColor Yellow
try {
    # Try to connect - even 404 means API is running
    $testResponse = Invoke-WebRequest -Uri "http://localhost:8000" -Method GET -TimeoutSec 5 -ErrorAction SilentlyContinue
    Write-Host "[OK] API is reachable!" -ForegroundColor Green
} catch {
    # Check if it's just a 404 (which means API is running)
    if ($_.Exception.Response.StatusCode.value__ -eq 404) {
        Write-Host "[OK] API is reachable!" -ForegroundColor Green
    } else {
        Write-Host "[ERROR] Cannot connect to API at http://localhost:8000" -ForegroundColor Red
        Write-Host "Make sure Docker containers are running:" -ForegroundColor Red
        Write-Host "  docker-compose -f docker-compose.local.yml up" -ForegroundColor Yellow
        exit 1
    }
}

Write-Host ""
Write-Host "Sending 5 concurrent requests at: $(Get-Date -Format 'HH:mm:ss')" -ForegroundColor Cyan
Write-Host "--------------------------------------------" -ForegroundColor Gray

# Array to store job IDs and results
$jobResults = @()
$jobs = @()

# Send all 5 requests concurrently using background jobs
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
        Write-Host "Invoke-RestMethod -Uri `"http://localhost:8000/api/job-status/$($job.job_id)`"" -ForegroundColor Gray
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
                    $status = Invoke-RestMethod -Uri "http://localhost:8000/api/job-status/$($job.job_id)"
                    
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
                    $status = Invoke-RestMethod -Uri "http://localhost:8000/api/job-status/$($job.job_id)"
                    if ($status.status -eq "completed") {
                        Write-Host ""
                        Write-Host "[OK] $($job.name)" -ForegroundColor Green
                        Write-Host "  Agent Report: $($status.dropbox_url)" -ForegroundColor Gray
                        if ($status.commission_dropbox_url) {
                            Write-Host "  Commission Report: $($status.commission_dropbox_url)" -ForegroundColor Gray
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
Write-Host "# Connect to Redis" -ForegroundColor White
Write-Host "docker-compose -f docker-compose.local.yml exec redis redis-cli" -ForegroundColor Gray
Write-Host ""
Write-Host "Then inside Redis CLI:" -ForegroundColor White
Write-Host "  KEYS job:*                         # List all jobs" -ForegroundColor Gray
Write-Host "  LLEN rq:queue:agentlink-queue      # Check queue length" -ForegroundColor Gray
Write-Host "  LRANGE rq:queue:agentlink-queue 0 -1  # List queued jobs" -ForegroundColor Gray
Write-Host "  HGETALL job:JOB_ID                 # Get job details" -ForegroundColor Gray
Write-Host "  INFO stats                         # Redis statistics" -ForegroundColor Gray
Write-Host "  EXIT                               # Quit Redis CLI" -ForegroundColor Gray
Write-Host ""
Write-Host "Test completed at: $(Get-Date -Format 'HH:mm:ss')" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
