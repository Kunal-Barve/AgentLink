# 🔍 Redis Monitoring Guide

## Quick Access to Redis

### **Step 1: Connect to Redis CLI**

Open a **new terminal** and run:

```bash
docker-compose -f docker-compose.local.yml exec redis redis-cli
```

You'll see:
```
127.0.0.1:6379>
```

---

## 📊 Useful Redis Commands

### **Check All Jobs**

```redis
KEYS job:*
```

**Output:**
```
1) "job:abc-123-xyz"
2) "job:def-456-uvw"
3) "job:ghi-789-rst"
```

### **Get Job Details**

```redis
HGETALL job:abc-123-xyz
```

**Output:**
```
1) "status"
2) "completed"
3) "suburb"
4) "Greenfields"
5) "dropbox_url"
6) "https://www.dropbox.com/..."
7) "filename"
8) "Greenfields_Top_Agents_abc-123-xyz.pdf"
9) "updated_at"
10) "2025-10-12T17:45:30.123456"
```

### **Check Queue Length**

```redis
LLEN rq:queue:agentlink-queue
```

**Output:**
```
(integer) 3
```

This shows **3 jobs** are waiting in the queue.

### **List Jobs in Queue**

```redis
LRANGE rq:queue:agentlink-queue 0 -1
```

**Output:**
```
1) "job_id_1"
2) "job_id_2"
3) "job_id_3"
```

### **Check Processing Jobs**

```redis
KEYS rq:wip:*
```

**Output:**
```
1) "rq:wip:worker123"
```

Shows which worker is processing which job.

### **Count All Jobs**

```redis
DBSIZE
```

**Output:**
```
(integer) 15
```

Total number of keys in Redis (includes jobs, queue data, etc.)

### **Redis Statistics**

```redis
INFO stats
```

**Output:**
```
# Stats
total_connections_received:45
total_commands_processed:1234
instantaneous_ops_per_sec:12
...
```

### **Memory Usage**

```redis
INFO memory
```

**Output:**
```
# Memory
used_memory:1234567
used_memory_human:1.18M
used_memory_peak:2345678
used_memory_peak_human:2.24M
...
```

### **Check Specific Job Status**

```redis
HGET job:abc-123-xyz status
```

**Output:**
```
"completed"
```

### **Clear All Jobs (⚠️ Careful!)**

```redis
FLUSHDB
```

**Warning:** This deletes ALL data in the current database!

### **Exit Redis CLI**

```redis
EXIT
```

---

## 🎯 Monitoring During Test

### **Terminal Setup (3 terminals)**

**Terminal 1: Docker Logs**
```bash
docker-compose -f docker-compose.local.yml logs -f
```

**Terminal 2: Redis CLI**
```bash
docker-compose -f docker-compose.local.yml exec redis redis-cli
```

**Terminal 3: Test Script**
```powershell
.\test-concurrent-requests.ps1
```

---

## 📋 Quick Monitoring Workflow

### **Before Running Test**

```redis
# Check Redis is empty
KEYS *
# Should be empty or minimal keys

# Check queue is empty
LLEN rq:queue:agentlink-queue
# Should be 0
```

### **During Test (Immediate After Sending Requests)**

```redis
# Check queue length
LLEN rq:queue:agentlink-queue
# Should show 4-5 (if worker is processing 1, others waiting)

# List all jobs
KEYS job:*
# Should show 5 job keys

# Check first job status
HGET job:FIRST_JOB_ID status
# Should show "processing" or "fetching_agents_data"
```

### **Monitor Progress**

Run this every 30 seconds:

```redis
# Check queue (should decrease)
LLEN rq:queue:agentlink-queue

# Check job statuses
HGET job:JOB_ID_1 status
HGET job:JOB_ID_2 status
HGET job:JOB_ID_3 status
HGET job:JOB_ID_4 status
HGET job:JOB_ID_5 status
```

### **After All Complete**

```redis
# Verify all jobs done
KEYS job:*
# Shows 5 jobs

# Check they're all completed
HGET job:JOB_ID_1 status
# Should be "completed" for all

# Check queue is empty
LLEN rq:queue:agentlink-queue
# Should be 0
```

---

## 🔧 Advanced Redis Commands

### **Watch Queue in Real-Time**

```bash
# In terminal (not Redis CLI)
watch -n 1 'docker-compose -f docker-compose.local.yml exec redis redis-cli LLEN rq:queue:agentlink-queue'
```

### **Monitor All Job Statuses**

```bash
# Get all job IDs and their statuses
docker-compose -f docker-compose.local.yml exec redis redis-cli KEYS "job:*" | while read key; do
  echo "$key:"
  docker-compose -f docker-compose.local.yml exec redis redis-cli HGET "$key" status
done
```

### **Check Worker Activity**

```redis
# See active workers
KEYS rq:worker:*

# Get worker info
SMEMBERS rq:workers
```

### **Check Failed Jobs**

```redis
# List failed jobs
LRANGE rq:queue:failed 0 -1

# Count failed jobs
LLEN rq:queue:failed
```

---

## 📈 Performance Metrics

### **Jobs Per Minute**

```redis
# Run before test
SET test_start_count 0

# After test
DBSIZE
# Subtract test_start_count to get jobs created
```

### **Queue Wait Time**

Monitor `LLEN rq:queue:agentlink-queue` over time:
- High number = jobs backing up
- Decreasing = worker processing
- Zero = all caught up

---

## 🎓 What to Look For

### **✅ Good Signs**

```redis
# All jobs accepted
KEYS job:*
# Returns 5 keys

# Queue processing
LLEN rq:queue:agentlink-queue
# Decreases over time (5 → 4 → 3 → 2 → 1 → 0)

# Jobs completing
HGET job:abc-123 status
# Changes: processing → fetching_agents_data → generating_pdf → uploading_to_dropbox → completed

# No failed jobs
LLEN rq:queue:failed
# Returns 0
```

### **❌ Bad Signs**

```redis
# Queue not decreasing
LLEN rq:queue:agentlink-queue
# Stays at 5 (worker not running!)

# Jobs stuck
HGET job:abc-123 status
# Stays at "processing" for > 10 minutes

# Failed jobs accumulating
LLEN rq:queue:failed
# Returns > 0

# No jobs created
KEYS job:*
# Returns empty (API not reaching worker)
```

---

## 🐛 Troubleshooting with Redis

### **Problem: No Jobs Created**

```redis
KEYS job:*
# Returns empty
```

**Cause:** API not connected to Redis

**Fix:** Check `REDIS_URL` environment variable

### **Problem: Jobs Stuck in Queue**

```redis
LLEN rq:queue:agentlink-queue
# Returns 5 (doesn't decrease)
```

**Cause:** Worker not running

**Fix:** 
```bash
docker-compose -f docker-compose.local.yml ps agentlink-worker
docker-compose -f docker-compose.local.yml restart agentlink-worker
```

### **Problem: Jobs Stuck in Processing**

```redis
HGET job:abc-123 status
# Returns "processing" for > 10 minutes
```

**Cause:** Worker crashed during processing

**Fix:** 
```bash
docker-compose -f docker-compose.local.yml logs agentlink-worker --tail=50
docker-compose -f docker-compose.local.yml restart agentlink-worker
```

---

## 🎯 Complete Test Monitoring Script

```bash
#!/bin/bash
# Run in separate terminal while test is running

echo "=== Redis Monitoring ==="
echo ""

while true; do
    clear
    echo "Time: $(date '+%H:%M:%S')"
    echo "======================================"
    
    # Queue length
    QUEUE=$(docker-compose -f docker-compose.local.yml exec redis redis-cli LLEN rq:queue:agentlink-queue)
    echo "Queue Length: $QUEUE"
    
    # Total jobs
    JOBS=$(docker-compose -f docker-compose.local.yml exec redis redis-cli KEYS "job:*" | wc -l)
    echo "Total Jobs: $JOBS"
    
    # Failed jobs
    FAILED=$(docker-compose -f docker-compose.local.yml exec redis redis-cli LLEN rq:queue:failed)
    echo "Failed Jobs: $FAILED"
    
    echo "======================================"
    echo "Press Ctrl+C to stop monitoring"
    
    sleep 5
done
```

---

## 📝 Quick Reference Card

| Command | Purpose |
|---------|---------|
| `KEYS job:*` | List all jobs |
| `HGETALL job:ID` | Get job details |
| `LLEN rq:queue:agentlink-queue` | Check queue length |
| `LRANGE rq:queue:agentlink-queue 0 -1` | List queued jobs |
| `HGET job:ID status` | Get job status |
| `DBSIZE` | Total keys in Redis |
| `INFO stats` | Redis statistics |
| `FLUSHDB` | ⚠️ Delete all data |
| `EXIT` | Quit Redis CLI |

---

**Pro Tip:** Keep Redis CLI open in a separate terminal during testing for quick status checks!
