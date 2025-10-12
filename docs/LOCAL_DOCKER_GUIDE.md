# 🐳 Local Docker Testing Guide

## Why `--progress=plain` Works

### The Issue
Docker's default build output uses **BuildKit** with fancy progress bars that sometimes:
- Masks actual errors
- Uses experimental features that can fail
- Hides detailed download/layer information
- Can timeout on slow connections

### The Solution
```bash
docker-compose -f docker-compose.local.yml build --progress=plain
```

### Why This Works Better

1. **Plain Text Output** 
   - Shows every step clearly
   - No fancy animations that can break
   - Better error visibility

2. **More Verbose Logging**
   - See exactly which layer is downloading
   - See all Docker commands executed
   - Easier to debug if something fails

3. **Better for Slow Connections**
   - Doesn't timeout waiting for UI updates
   - Shows progress in simple percentages
   - Less overhead

4. **Works with Network Issues**
   - More retry-friendly
   - Better error messages
   - Shows exactly where network fails

---

## 🚀 Complete Local Docker Testing Guide

### Prerequisites Checklist

- ✅ Docker Desktop installed and running
- ✅ `.env` file with all API keys present
- ✅ Port 8000 available (not used by other apps)
- ✅ At least 2GB free disk space

---

## Step-by-Step Instructions

### **Step 1: Navigate to Project Directory**

```bash
cd "d:\Work\Upwork\Make+DropBox integration\CodeBase\Make-Integration"
```

### **Step 2: Build Docker Image**

```bash
docker-compose -f docker-compose.local.yml build --progress=plain
```

**What this does:**
- Reads `docker-compose.local.yml` configuration
- Builds the `agentlink` Docker image
- Installs all Python dependencies from `requirements.txt`
- Uses plain text output for better visibility

**Expected output:**
```
#1 [internal] load .dockerignore
#1 transferring context: 2B done
#1 DONE 0.0s

#2 [internal] load build definition from Dockerfile
#2 transferring dockerfile: 1.02kB done
#2 DONE 0.0s

#3 [internal] load metadata for docker.io/library/python:3.11-slim
#3 DONE 2.5s

#4 [1/7] FROM docker.io/library/python:3.11-slim@sha256:...
#4 DONE 0.0s

#5 [internal] load build context
#5 transferring context: 45.23kB done
#5 DONE 0.1s

#6 [2/7] WORKDIR /app
#6 CACHED

#7 [3/7] RUN apt-get update && apt-get install -y ...
#7 CACHED

#8 [4/7] COPY requirements.txt .
#8 CACHED

#9 [5/7] RUN pip install --no-cache-dir -r requirements.txt
#9 CACHED

#10 [6/7] COPY . .
#10 DONE 0.5s

#11 exporting to image
#11 exporting layers done
#11 writing image sha256:abc123... done
#11 naming to docker.io/library/agentlink done
#11 DONE 0.1s
```

**Build time:** 2-5 minutes (first time), 10-30 seconds (cached)

---

### **Step 3: Start All Services**

```bash
docker-compose -f docker-compose.local.yml up
```

**What this starts:**
- ✅ **Redis** - Job queue (port 6379)
- ✅ **AgentLink API** - FastAPI server (port 8000, with hot reload)
- ✅ **AgentLink Worker** - RQ worker for PDF generation

**Expected output:**
```
Creating network "make-integration_default" with the default driver
Creating volume "make-integration_redis-data-local" with default driver
Creating make-integration_redis_1 ... done
Creating make-integration_agentlink_1 ... done
Creating make-integration_agentlink-worker_1 ... done

Attaching to redis_1, agentlink_1, agentlink-worker_1

redis_1    | 1:C 12 Oct 2025 07:43:15.234 # oO0OoO0OoO0Oo Redis is starting oO0OoO0OoO0Oo
redis_1    | 1:C 12 Oct 2025 07:43:15.234 # Redis version=7.0.15, bits=64
redis_1    | 1:M 12 Oct 2025 07:43:15.236 * Ready to accept connections

agentlink_1 | INFO:     Will watch for changes in these directories: ['/app']
agentlink_1 | INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
agentlink_1 | INFO:     Started reloader process [1] using StatReload
agentlink_1 | 2025-10-12 07:43:16,123 - articflow - INFO - Environment variables loaded
agentlink_1 | 2025-10-12 07:43:16,125 - articflow - INFO - FastAPI application initialized

agentlink-worker_1 | 07:43:16 RQ worker 'rq:worker:abc123.1' started
agentlink-worker_1 | 07:43:16 Subscribing to channel rq:pubsub:abc123
agentlink-worker_1 | 07:43:16 *** Listening on agentlink-queue...
```

**Keep this terminal open!** It shows live logs from all services.

---

### **Step 4: Test in New Terminal**

Open a **new terminal** (keep services running in first terminal):

#### **Test 1: Health Check**

```bash
curl http://localhost:8000
```

**Expected:** API responds (might be 404, but shows it's running)

#### **Test 2: Generate Single Report**

```bash
curl -X POST http://localhost:8000/api/generate-agents-report `
  -H "Content-Type: application/json" `
  -Body '{
    "suburb": "Manly",
    "state": "NSW",
    "property_types": ["House"],
    "min_bedrooms": 2
  }'
```

**Expected response:**
```json
{
  "job_id": "abc-123-xyz-456",
  "status": "processing"
}
```

#### **Test 3: Check Job Status**

```bash
curl http://localhost:8000/api/job-status/abc-123-xyz-456
```

**Progress states:**
```json
// Just started
{
  "job_id": "abc-123-xyz-456",
  "status": "processing",
  "progress": 10,
  "dropbox_url": "",
  "filename": ""
}

// Fetching data
{
  "status": "fetching_agents_data",
  "progress": 30
}

// Generating PDF
{
  "status": "generating_pdf",
  "progress": 60
}

// Uploading
{
  "status": "uploading_to_dropbox",
  "progress": 85
}

// Complete! ✅
{
  "status": "completed",
  "progress": 100,
  "dropbox_url": "https://www.dropbox.com/...",
  "filename": "Manly_Top_Agents_abc-123-xyz-456.pdf"
}
```

#### **Test 4: Concurrent Requests** 🎯

**PowerShell:**
```powershell
# Send 5 requests at once
1..5 | ForEach-Object {
  Start-Job -ScriptBlock {
    Invoke-RestMethod -Method Post `
      -Uri "http://localhost:8000/api/generate-agents-report" `
      -ContentType "application/json" `
      -Body '{"suburb": "Manly", "state": "NSW"}'
  }
}

# Wait for all jobs and show results
Get-Job | Wait-Job | Receive-Job
```

**Expected:**
- ✅ All 5 return unique `job_id`
- ✅ No requests dropped
- ✅ All eventually complete (check status)

---

## 📊 Monitoring and Debugging

### **View Logs**

```bash
# All services
docker-compose -f docker-compose.local.yml logs -f

# Just API
docker-compose -f docker-compose.local.yml logs -f agentlink

# Just Worker
docker-compose -f docker-compose.local.yml logs -f agentlink-worker

# Just Redis
docker-compose -f docker-compose.local.yml logs -f redis

# Last 50 lines from worker
docker-compose -f docker-compose.local.yml logs --tail=50 agentlink-worker
```

### **Check Container Status**

```bash
# List running containers
docker-compose -f docker-compose.local.yml ps

# Expected output:
NAME                              IMAGE       STATUS
make-integration-agentlink-1      agentlink   Up
make-integration-agentlink-worker-1  agentlink   Up
make-integration-redis-1          redis:7-alpine   Up
```

### **Check Redis Jobs**

```bash
# Connect to Redis CLI
docker-compose -f docker-compose.local.yml exec redis redis-cli

# Inside Redis:
KEYS job:*                         # List all jobs
HGETALL job:abc-123-xyz            # Get job details
LLEN rq:queue:agentlink-queue      # Check queue length
LRANGE rq:queue:agentlink-queue 0 -1  # List queued jobs
EXIT
```

### **Check Worker Status**

```bash
docker-compose -f docker-compose.local.yml exec agentlink-worker rq info --url redis://redis:6379/0
```

**Output shows:**
```
agentlink-queue |████████████████████| 5

1 queues, 1 worker, 5 jobs
```

### **Monitor Resource Usage**

```bash
docker stats
```

**Shows real-time:**
- CPU usage
- Memory usage
- Network I/O
- Disk I/O

---

## 🛠️ Development Workflow

### **Making Code Changes**

The `docker-compose.local.yml` mounts your source code:

```yaml
volumes:
  - ./app:/app/app  # Live code mounting
```

**Changes to these auto-reload (API):**
- `app/main.py`
- `app/services/*.py`
- Just save the file → API reloads automatically

**Changes that need worker restart:**
- `app/worker_tasks.py`

```bash
docker-compose -f docker-compose.local.yml restart agentlink-worker
```

### **Testing Changes Flow**

1. Edit `app/main.py` or `app/worker_tasks.py`
2. Save the file
3. Check logs in first terminal (you'll see reload message)
4. If worker code changed: `docker-compose -f docker-compose.local.yml restart agentlink-worker`
5. Test the change

### **Rebuild After Dependency Changes**

If you modify `requirements.txt`:

```bash
# Stop services
docker-compose -f docker-compose.local.yml down

# Rebuild with new dependencies
docker-compose -f docker-compose.local.yml build --progress=plain --no-cache

# Start again
docker-compose -f docker-compose.local.yml up
```

---

## 🔧 Common Commands Reference

### **Build Commands**

```bash
# Build with verbose output
docker-compose -f docker-compose.local.yml build --progress=plain

# Build without cache (fresh build)
docker-compose -f docker-compose.local.yml build --no-cache --progress=plain

# Build specific service only
docker-compose -f docker-compose.local.yml build agentlink --progress=plain
```

### **Run Commands**

```bash
# Start all services (foreground, see logs)
docker-compose -f docker-compose.local.yml up

# Start in background (detached)
docker-compose -f docker-compose.local.yml up -d

# Start specific service only
docker-compose -f docker-compose.local.yml up redis

# Start and rebuild if needed
docker-compose -f docker-compose.local.yml up --build
```

### **Stop Commands**

```bash
# Stop all services (keep containers)
docker-compose -f docker-compose.local.yml stop

# Stop and remove containers (keep volumes)
docker-compose -f docker-compose.local.yml down

# Stop, remove containers AND volumes (clean slate)
docker-compose -f docker-compose.local.yml down -v

# Force stop immediately
docker-compose -f docker-compose.local.yml kill
```

### **Restart Commands**

```bash
# Restart all services
docker-compose -f docker-compose.local.yml restart

# Restart specific service
docker-compose -f docker-compose.local.yml restart agentlink-worker

# Restart with rebuild
docker-compose -f docker-compose.local.yml down
docker-compose -f docker-compose.local.yml up --build
```

### **Debug Commands**

```bash
# Execute command in running container
docker-compose -f docker-compose.local.yml exec agentlink bash

# View environment variables
docker-compose -f docker-compose.local.yml exec agentlink env

# Check Python packages installed
docker-compose -f docker-compose.local.yml exec agentlink pip list

# Test Redis connection
docker-compose -f docker-compose.local.yml exec agentlink python -c "import redis; r=redis.from_url('redis://redis:6379/0'); print(r.ping())"
```

---

## 🐛 Troubleshooting

### **Problem: Build fails with network error**

**Solution:**
```bash
# Use plain progress and increase timeout
COMPOSE_HTTP_TIMEOUT=300 docker-compose -f docker-compose.local.yml build --progress=plain
```

### **Problem: Port 8000 already in use**

**Check what's using it:**
```bash
netstat -ano | findstr :8000
```

**Kill the process or change port:**
```yaml
# In docker-compose.local.yml
ports:
  - "8001:8000"  # Use 8001 instead
```

### **Problem: Worker not processing jobs**

**Check worker logs:**
```bash
docker-compose -f docker-compose.local.yml logs agentlink-worker
```

**Restart worker:**
```bash
docker-compose -f docker-compose.local.yml restart agentlink-worker
```

**Verify worker is connected to Redis:**
```bash
docker-compose -f docker-compose.local.yml exec agentlink-worker rq info --url redis://redis:6379/0
```

### **Problem: Redis connection refused**

**Check Redis is running:**
```bash
docker-compose -f docker-compose.local.yml ps redis
```

**Test Redis connection:**
```bash
docker-compose -f docker-compose.local.yml exec redis redis-cli PING
# Should return: PONG
```

**Restart Redis:**
```bash
docker-compose -f docker-compose.local.yml restart redis
```

### **Problem: Changes not reflecting**

**For API changes:**
- Check logs for reload message
- If not auto-reloading: `docker-compose -f docker-compose.local.yml restart agentlink`

**For worker changes:**
```bash
docker-compose -f docker-compose.local.yml restart agentlink-worker
```

**For dependency changes:**
```bash
docker-compose -f docker-compose.local.yml down
docker-compose -f docker-compose.local.yml build --no-cache --progress=plain
docker-compose -f docker-compose.local.yml up
```

### **Problem: Jobs stuck in "processing"**

**Check all services are running:**
```bash
docker-compose -f docker-compose.local.yml ps
```

**Check worker logs for errors:**
```bash
docker-compose -f docker-compose.local.yml logs --tail=100 agentlink-worker
```

**Check job in Redis:**
```bash
docker-compose -f docker-compose.local.yml exec redis redis-cli HGETALL job:YOUR_JOB_ID
```

**Clear stuck jobs:**
```bash
docker-compose -f docker-compose.local.yml exec redis redis-cli FLUSHDB
```

### **Problem: Out of disk space**

**Clean up Docker:**
```bash
# Remove unused containers
docker container prune

# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune

# Remove everything unused
docker system prune -a --volumes
```

---

## 🎯 Testing Scenarios

### **Scenario 1: Basic Functionality**

```bash
# Send request
curl -X POST http://localhost:8000/api/generate-agents-report `
  -H "Content-Type: application/json" `
  -Body '{"suburb": "Bondi", "state": "NSW"}'

# Copy the job_id from response
# Check status every 30 seconds
curl http://localhost:8000/api/job-status/YOUR_JOB_ID

# Wait for "completed" status
# Check Dropbox for PDF
```

**✅ Success criteria:**
- Job completes in 2-5 minutes
- PDF appears in Dropbox
- No errors in logs

### **Scenario 2: Concurrent Requests**

```powershell
# Send 5 requests simultaneously
$jobs = 1..5 | ForEach-Object {
  Start-Job -ScriptBlock {
    Invoke-RestMethod -Method Post `
      -Uri "http://localhost:8000/api/generate-agents-report" `
      -ContentType "application/json" `
      -Body '{"suburb": "Manly", "state": "NSW"}'
  }
}

# Get all job IDs
$results = $jobs | Wait-Job | Receive-Job
$results | ForEach-Object { Write-Host "Job ID: $($_.job_id)" }

# Check all jobs complete
$results | ForEach-Object {
  curl "http://localhost:8000/api/job-status/$($_.job_id)"
}
```

**✅ Success criteria:**
- All 5 return unique job_id
- All eventually complete
- No dropped requests
- All PDFs in Dropbox

### **Scenario 3: Error Handling**

```bash
# Invalid suburb
curl -X POST http://localhost:8000/api/generate-agents-report `
  -H "Content-Type: application/json" `
  -Body '{"suburb": "InvalidPlace123", "state": "NSW"}'

# Check status - should show error
curl http://localhost:8000/api/job-status/YOUR_JOB_ID
```

**✅ Success criteria:**
- Job ID returned
- Status eventually shows "failed"
- Error message present
- Worker keeps running

### **Scenario 4: Commission Report**

```bash
curl -X POST http://localhost:8000/api/generate-agents-report `
  -H "Content-Type: application/json" `
  -Body '{
    "suburb": "Manly",
    "state": "NSW",
    "home_owner_pricing": "$800,000 - $1,000,000",
    "post_code": "2095"
  }'
```

**✅ Success criteria:**
- 2 PDFs generated (agents + commission)
- Both URLs in response
- Both PDFs in Dropbox

---

## 📈 Performance Benchmarks

### **Expected Performance on Local Machine**

| Metric | Expected Value |
|--------|----------------|
| API response time | < 1 second |
| PDF generation time | 2-5 minutes |
| Concurrent requests | 4-5 without queue backup |
| Memory usage (API) | 200-300 MB |
| Memory usage (Worker) | 500-800 MB |
| Memory usage (Redis) | 50-100 MB |
| CPU usage (idle) | < 5% |
| CPU usage (processing) | 50-70% per worker |

---

## 🚀 Quick Start Cheat Sheet

```bash
# 1. Build
docker-compose -f docker-compose.local.yml build --progress=plain

# 2. Start
docker-compose -f docker-compose.local.yml up

# 3. Test (new terminal)
curl -X POST http://localhost:8000/api/generate-agents-report -H "Content-Type: application/json" -Body '{"suburb":"Manly","state":"NSW"}'

# 4. Check status
curl http://localhost:8000/api/job-status/YOUR_JOB_ID

# 5. Watch logs
docker-compose -f docker-compose.local.yml logs -f

# 6. Stop
docker-compose -f docker-compose.local.yml down
```

---

## ✅ Ready for Production

Once local testing is successful:

1. ✅ All tests pass
2. ✅ Concurrent requests work
3. ✅ No errors in logs
4. ✅ PDFs appear in Dropbox

**Deploy to production:**
```bash
# On production server
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

---

**Created:** 2025-10-12  
**Last Updated:** 2025-10-12  
**Status:** ✅ Ready to Use
