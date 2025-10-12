# 🧪 Concurrent Request Test

## What This Test Does

Sends **5 simultaneous requests** to test if your Docker RQ setup can handle concurrent PDF generation without dropping requests.

**Test Locations:**
1. Greenfields, WA ($1m-$1.5m)
2. Seaford Rise, SA ($500k-$1m)
3. Kingswood, NSW ($500k-$1m)
4. South Penrith, NSW ($1m-$1.5m)
5. Winston Hills, NSW ($1.5m-$2m)

---

## 🚀 How to Run the Test

### **Step 1: Start Docker Services**

```bash
docker-compose -f docker-compose.local.yml up
```

**Wait until you see:**
```
redis_1    | Ready to accept connections
agentlink_1 | Uvicorn running on http://0.0.0.0:8000
agentlink-worker_1 | RQ worker started
```

### **Step 2: Run the Test Script**

Open a **new terminal** and run:

```powershell
.\test-concurrent-requests.ps1
```

### **Step 3: Watch the Results**

The script will:
1. ✅ Send all 5 requests simultaneously
2. ✅ Show which requests succeeded
3. ✅ Display job IDs for tracking
4. ✅ Optionally monitor progress every 30 seconds
5. ✅ Show final results with Dropbox links

---

## 📊 Expected Results

### **✅ SUCCESS - All Requests Accepted**

```
============================================
           REQUEST RESULTS
============================================

✓ Greenfields, WA
  Job ID: abc-123-xyz
  Status: processing
  Time: 17:30:01

✓ Seaford Rise, SA
  Job ID: def-456-uvw
  Status: processing
  Time: 17:30:01

✓ Kingswood, NSW
  Job ID: ghi-789-rst
  Status: processing
  Time: 17:30:01

✓ South Penrith, NSW
  Job ID: jkl-012-opq
  Status: processing
  Time: 17:30:01

✓ Winston Hills, NSW
  Job ID: mno-345-lmn
  Status: processing
  Time: 17:30:02

============================================
Summary: 5 succeeded, 0 failed
============================================
```

**This means: ✅ RQ is working! All 5 requests were queued successfully.**

### **❌ FAILURE - Requests Dropped**

```
============================================
           REQUEST RESULTS
============================================

✓ Greenfields, WA
  Job ID: abc-123-xyz
  Status: processing

✗ Seaford Rise, SA
  Error: Connection refused

✗ Kingswood, NSW
  Error: Timeout

============================================
Summary: 1 succeeded, 4 failed
============================================
```

**This means: ❌ Problem with Docker setup or API not handling concurrent requests.**

---

## 🔍 Monitoring Redis (In Another Terminal)

While the test is running, open a **3rd terminal**:

```bash
# Connect to Redis
docker-compose -f docker-compose.local.yml exec redis redis-cli
```

**Inside Redis CLI, run:**

```redis
# Check how many jobs are waiting
LLEN rq:queue:agentlink-queue

# List all jobs
KEYS job:*

# Check specific job status
HGET job:abc-123-xyz status

# Exit
EXIT
```

**See full Redis commands in:** `REDIS_MONITORING.md`

---

## 📈 What to Watch For

### **In Docker Logs (Terminal 1):**

```
agentlink-worker_1 | 17:30:02 agentlink-queue: app.worker_tasks.process_agents_report_task(abc-123-xyz, ...)
agentlink-worker_1 | 17:30:02 INFO: Worker: Starting to process agents report job abc-123-xyz
agentlink-worker_1 | 17:30:05 INFO: Job abc-123-xyz: Fetching agents data for suburb=Greenfields
```

**Good signs:**
- ✅ Worker picks up jobs immediately
- ✅ Logs show "Starting to process" for each job
- ✅ Status changes from processing → fetching → generating → uploading → completed

### **In Redis CLI (Terminal 3):**

```redis
# Right after test starts
127.0.0.1:6379> LLEN rq:queue:agentlink-queue
(integer) 4

# After 2 minutes
127.0.0.1:6379> LLEN rq:queue:agentlink-queue
(integer) 3

# After 5 minutes
127.0.0.1:6379> LLEN rq:queue:agentlink-queue
(integer) 1

# After 10 minutes
127.0.0.1:6379> LLEN rq:queue:agentlink-queue
(integer) 0
```

**Good signs:**
- ✅ Queue length decreases over time
- ✅ Jobs move from queue to worker
- ✅ Eventually queue becomes empty

---

## ⏱️ Expected Timing

| Event | Time |
|-------|------|
| All 5 requests sent | 0:00 - 0:02 |
| All requests accepted | 0:02 |
| First job starts | 0:02 |
| Second job starts (if 2 workers) | 0:02 |
| Or waits in queue (if 1 worker) | 0:02 |
| First job completes | 2:00 - 5:00 |
| All jobs complete (1 worker) | 10:00 - 25:00 |
| All jobs complete (2 workers) | 5:00 - 15:00 |

---

## 🎯 Success Criteria

### ✅ **Test Passes If:**

1. **All 5 requests accepted** → Script shows "5 succeeded, 0 failed"
2. **All 5 jobs have unique IDs** → Each gets different job_id
3. **No errors in logs** → Worker processes without crashes
4. **All jobs eventually complete** → Status changes to "completed"
5. **All PDFs in Dropbox** → Each job has dropbox_url
6. **Commission reports generated** → Each has commission_dropbox_url (since all have home_owner_pricing)

### ❌ **Test Fails If:**

1. **Any request rejected** → Script shows "X failed"
2. **Jobs not in Redis** → `KEYS job:*` returns < 5
3. **Worker errors** → Logs show crashes or exceptions
4. **Jobs stuck** → Status stays "processing" for > 15 minutes
5. **Missing PDFs** → Status "completed" but no dropbox_url

---

## 🐛 Troubleshooting

### **Problem: "Cannot connect to API"**

**Solution:**
```bash
# Check Docker is running
docker-compose -f docker-compose.local.yml ps

# If not running, start:
docker-compose -f docker-compose.local.yml up
```

### **Problem: "Request succeeded but job not processing"**

**Check worker logs:**
```bash
docker-compose -f docker-compose.local.yml logs agentlink-worker --tail=50
```

**Restart worker:**
```bash
docker-compose -f docker-compose.local.yml restart agentlink-worker
```

### **Problem: "Jobs stuck in queue"**

**Check Redis:**
```bash
docker-compose -f docker-compose.local.yml exec redis redis-cli LLEN rq:queue:agentlink-queue
```

**If queue has jobs but worker isn't processing:**
```bash
# Check worker is running
docker-compose -f docker-compose.local.yml ps agentlink-worker

# Restart if needed
docker-compose -f docker-compose.local.yml restart agentlink-worker
```

### **Problem: "Some requests timed out"**

**This is normal if:**
- First time running (downloading data takes longer)
- API is warming up
- Network is slow

**Run the test again - it should be faster the second time.**

---

## 📊 Files Created by Test

### **job_ids.json**
Contains all job IDs for later reference:
```json
[
  {
    "name": "Greenfields, WA",
    "job_id": "abc-123-xyz"
  },
  {
    "name": "Seaford Rise, SA",
    "job_id": "def-456-uvw"
  }
]
```

**Use this to check status later:**
```powershell
$jobs = Get-Content job_ids.json | ConvertFrom-Json
foreach ($job in $jobs) {
    Write-Host $job.name
    Invoke-RestMethod -Uri "http://localhost:8000/api/job-status/$($job.job_id)"
}
```

---

## 🎓 Understanding the Results

### **If You See 5/5 Succeeded:**
✅ **Your RQ implementation is working perfectly!**
- API can handle concurrent requests
- Jobs are properly queued in Redis
- Worker is processing jobs from queue
- No requests are dropped

### **What Happens Behind the Scenes:**

1. **Request 1-5 arrive** → All accepted immediately (< 1 second each)
2. **All jobs stored in Redis** → Persistent queue
3. **Worker 1 picks Job 1** → Starts processing (2-5 min)
4. **Jobs 2-5 wait in queue** → Not dropped, just waiting
5. **Worker 1 finishes Job 1** → Picks Job 2
6. **Process continues** → Until all 5 complete

**This is exactly what we wanted!** 🎉

---

## 📝 Next Steps After Test

### **If Test Passes:**
1. ✅ RQ is working correctly
2. ✅ Ready to deploy to production
3. ✅ Can handle 4-5 concurrent users

**Deploy to production:**
```bash
# On production server
cd /path/to/project
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### **If Test Fails:**
1. Check logs: `docker-compose -f docker-compose.local.yml logs`
2. Check Redis: See `REDIS_MONITORING.md`
3. Restart services: `docker-compose -f docker-compose.local.yml restart`
4. Rebuild if needed: `docker-compose -f docker-compose.local.yml build --no-cache`
5. Run test again

---

## 🔗 Related Files

- **Test Script:** `test-concurrent-requests.ps1`
- **Redis Guide:** `REDIS_MONITORING.md`
- **Docker Guide:** `LOCAL_DOCKER_GUIDE.md`
- **Deployment Guide:** `DEPLOYMENT_GUIDE.md`

---

**Ready to test? Run:**
```powershell
.\test-concurrent-requests.ps1
```

**Good luck! 🚀**
