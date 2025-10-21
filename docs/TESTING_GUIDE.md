# 🧪 Testing Guide - Local & Production

Complete guide for testing the AgentLink system on both local and production servers.

---

## 🚀 Quick Start

### **Run the Test Script**

```powershell
.\test-concurrent-requests.ps1
```

**You'll see:**
```
============================================
  Docker RQ Concurrent Request Test
  Testing 5 simultaneous requests...
============================================

Select target server:
  1. Local (localhost:8000)
  2. Production (65.108.146.173)

Enter your choice (1 or 2):
```

**Select:**
- **1** - Test local Docker containers
- **2** - Test production server

---

## 🏠 Option 1: Testing Local Server

### **Prerequisites:**

1. **Docker containers running:**
   ```bash
   docker-compose -f docker-compose.local.yml up
   ```

2. **Wait for services to start:**
   ```
   redis_1    | Ready to accept connections
   agentlink_1 | Uvicorn running on http://0.0.0.0:8000
   agentlink-worker_1 | RQ worker started
   ```

### **Run Test:**

```powershell
.\test-concurrent-requests.ps1
# Select: 1 (Local)
```

**Expected Output:**
```
[INFO] Testing LOCAL server: http://localhost:8000
[INFO] Testing API connection...
[OK] API is reachable!

Sending 5 concurrent requests at: 09:30:00
--------------------------------------------
[1] Sending: Greenfields, WA...
[2] Sending: Seaford Rise, SA...
[3] Sending: Kingswood, NSW...
[4] Sending: South Penrith, NSW...
[5] Sending: Winston Hills, NSW...

Waiting for all requests to complete...
```

### **Monitor Local Redis:**

```bash
docker-compose -f docker-compose.local.yml exec redis redis-cli

# Inside Redis:
SMEMBERS rq:workers      # Check active workers
LLEN rq:queue:agentlink-queue  # Check queue
KEYS job:*               # List all jobs
```

---

## 🌐 Option 2: Testing Production Server

### **Prerequisites:**

1. **Production server accessible:**
   ```bash
   ping 65.108.146.173
   ```

2. **Production containers running:**
   ```bash
   ssh root@65.108.146.173
   cd /var/www/fastapi-app/AgentLink
   docker compose ps
   
   # Should show 7 containers running:
   # - nginx
   # - agentlink
   # - agentlink-worker-1
   # - agentlink-worker-2
   # - agentlink-worker-3
   # - agentlink-worker-4
   # - redis
   ```

### **Run Test:**

```powershell
.\test-concurrent-requests.ps1
# Select: 2 (Production)
```

**Expected Output:**
```
[INFO] Testing PRODUCTION server: http://65.108.146.173:8000
[INFO] Testing API connection...
[OK] API is reachable!

Sending 5 concurrent requests at: 09:30:00
--------------------------------------------
[1] Sending: Greenfields, WA...
[2] Sending: Seaford Rise, SA...
[3] Sending: Kingswood, NSW...
[4] Sending: South Penrith, NSW...
[5] Sending: Winston Hills, NSW...
```

### **Monitor Production Redis:**

```bash
# SSH to production
ssh root@65.108.146.173
cd /var/www/fastapi-app/AgentLink

# Check Redis
docker compose exec redis redis-cli

# Inside Redis:
SMEMBERS rq:workers      # Should show 4 workers!
LLEN rq:queue:agentlink-queue
KEYS job:*
```

---

## 📊 What the Test Does

### **Test Sequence:**

1. **Connection Test**
   - Verifies API is reachable
   - Shows error if server is down

2. **Send 5 Concurrent Requests**
   - Sends all 5 requests simultaneously
   - Each request generates agent + commission reports
   - Returns job IDs immediately

3. **Display Results**
   - Shows job IDs for all 5 requests
   - Saves job IDs to `job_ids.json`
   - Provides status check commands

4. **Optional Monitoring**
   - Asks if you want to monitor progress
   - Checks status every 30 seconds
   - Shows real-time progress updates

5. **Final Results**
   - Shows completion status
   - Displays Dropbox URLs
   - Shows Redis monitoring commands

---

## 🔍 Monitoring Job Progress

### **When Prompted:**

```
Would you like to monitor job progress? (Y/N): y
```

**If you select Y:**

```
Starting job monitoring (Press Ctrl+C to stop)...
Checking every 30 seconds...

--------------------------------------------
Check #1 at 09:30:30
--------------------------------------------
[PROC] Greenfields, WA: fetching_agents_data (30%)
[PROC] Seaford Rise, SA: fetching_agents_data (30%)
[PROC] Kingswood, NSW: processing (10%)
[PROC] South Penrith, NSW: processing (10%)
[PROC] Winston Hills, NSW: processing (10%)

Status: 0 completed, 5 processing, 0 failed
--------------------------------------------
Check #2 at 09:31:00
--------------------------------------------
[OK] Greenfields, WA: completed (100%)
  File: Greenfields_Top_Agents_abc123.pdf
[PROC] Seaford Rise, SA: generating_pdf (60%)
...
```

### **Manual Status Check:**

```powershell
# Check individual job
Invoke-RestMethod -Uri "http://localhost:8000/api/job-status/JOB_ID"

# Or for production
Invoke-RestMethod -Uri "http://65.108.146.173:8000/api/job-status/JOB_ID"
```

---

## 📈 Performance Expectations

### **Local (1 Worker):**
- 5 requests: ~6.5 minutes
- Sequential processing

### **Production (4 Workers):**
- 5 requests: ~2.5 minutes  
- 3-4 jobs process simultaneously
- **60% faster!** 🚀

**Timeline for 5 requests on production:**
```
Time 0:00 - Workers start: [Job1] [Job2] [Job3] [Job4]
            Queue: [Job5]

Time 2:00 - First batch done, Job5 starts
            Worker 1: [Job5]
            Workers 2-4: Idle

Time 2:30 - All complete!
```

---

## 🧪 Test Scenarios

### **Scenario 1: Basic Functionality Test**

**What it tests:**
- API accepts concurrent requests
- Jobs queue properly
- Workers process jobs
- PDFs generate successfully
- Dropbox uploads work

**Run:**
```powershell
.\test-concurrent-requests.ps1
# Select server
# Select N (no monitoring)
# Check results after 5-10 minutes
```

### **Scenario 2: Load Test (Production)**

**What it tests:**
- 4 workers handle concurrent load
- No requests dropped
- Queue doesn't back up
- All jobs complete successfully

**Run:**
```powershell
.\test-concurrent-requests.ps1
# Select: 2 (Production)
# Select: Y (monitor)
# Watch 4 workers process jobs
```

### **Scenario 3: Stress Test (Multiple Runs)**

**What it tests:**
- System stability over time
- No memory leaks
- Workers don't crash
- Queue processes all jobs

**Run:**
```powershell
# Run multiple times in succession
.\test-concurrent-requests.ps1  # Run 1
# Wait for completion
.\test-concurrent-requests.ps1  # Run 2
# Wait for completion
.\test-concurrent-requests.ps1  # Run 3
```

---

## 🐛 Troubleshooting

### **Error: Cannot connect to API**

**Local:**
```bash
# Check Docker
docker-compose -f docker-compose.local.yml ps

# If not running:
docker-compose -f docker-compose.local.yml up

# Check logs
docker-compose -f docker-compose.local.yml logs
```

**Production:**
```bash
# SSH to server
ssh root@65.108.146.173

# Check containers
docker compose ps

# If not running:
docker compose up -d

# Check logs
docker compose logs --tail=50
```

### **Jobs Stuck in Queue**

**Check workers:**
```bash
# Local
docker-compose -f docker-compose.local.yml logs agentlink-worker

# Production
ssh root@65.108.146.173
docker compose logs agentlink-worker-1 agentlink-worker-2 agentlink-worker-3 agentlink-worker-4
```

**Check Redis:**
```bash
# Connect to Redis
docker compose exec redis redis-cli

# Check workers
SMEMBERS rq:workers
# Should show active workers

# Check queue
LLEN rq:queue:agentlink-queue
# Should decrease as workers process

# Check if any worker is processing
KEYS rq:wip:*
```

### **Some Jobs Fail**

**Check specific job:**
```bash
# In Redis
HGETALL job:JOB_ID

# Look for error messages
# Common issues:
# - API rate limits (domain.com.au)
# - Network timeout
# - Dropbox upload failure
```

---

## 📁 Output Files

### **job_ids.json**
```json
[
  {
    "name": "Greenfields, WA",
    "job_id": "abc-123-xyz",
    "status": "processing",
    "timestamp": "2025-10-13T09:30:00"
  },
  ...
]
```

**Use this file to:**
- Reference job IDs later
- Check status after script completes
- Debug specific failed jobs

---

## 🎯 Success Criteria

### **Test Passes If:**

✅ All 5 requests accepted (returns job_id)  
✅ All jobs complete successfully  
✅ All 10 PDFs generated (5 agent + 5 commission)  
✅ All PDFs uploaded to Dropbox  
✅ All Dropbox URLs valid  
✅ No errors in logs  
✅ Workers remain running after test  

### **Performance Benchmarks:**

| Server | Workers | Time | Status |
|--------|---------|------|--------|
| Local | 1 | 6-7 min | ✅ Expected |
| Production | 4 | 2-3 min | ✅ Expected |

---

## 🚀 After Testing

### **If Test Passes:**

1. ✅ System ready for production use
2. ✅ Can integrate with Make.com
3. ✅ Can handle 4-8 concurrent users
4. ✅ Stable and reliable

### **If Test Fails:**

1. Check Docker logs
2. Check Redis queue
3. Check worker status
4. Review error messages
5. Consult [REDIS_MONITORING.md](./REDIS_MONITORING.md)

---

## 📚 Related Documentation

- **[TEST_README.md](./TEST_README.md)** - Original test documentation
- **[REDIS_MONITORING.md](./REDIS_MONITORING.md)** - Redis monitoring guide
- **[CAPACITY_ANALYSIS.md](./CAPACITY_ANALYSIS.md)** - Server capacity details
- **[PRODUCTION_DEPLOYMENT.md](./PRODUCTION_DEPLOYMENT.md)** - Deployment guide

---

## 🎉 Summary

**Test Script Features:**
- ✅ Test local OR production server
- ✅ Send 5 concurrent requests
- ✅ Real-time monitoring option
- ✅ Progress tracking
- ✅ Final results with Dropbox URLs
- ✅ Redis monitoring commands
- ✅ Job IDs saved to file

**Usage:**
```powershell
.\test-concurrent-requests.ps1
# Select 1 (Local) or 2 (Production)
# Follow prompts
# Monitor progress
# Verify results
```

**Your system is ready for concurrent load testing!** 🚀
