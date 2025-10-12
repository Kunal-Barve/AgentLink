# RQ Worker Deployment Guide

## 🎯 What We Did

Converted your AgentLink application from single-worker FastAPI background tasks to **RQ (Redis Queue)** with dedicated worker processes. This allows handling **4-5 concurrent PDF generation requests** on your CX22 server.

---

## 📦 Changes Made

### 1. **New Dependencies**
- `redis==5.0.1` - Redis client for Python
- `rq==1.15.1` - Redis Queue for background jobs

### 2. **New Services in Docker Compose**
- **redis** - In-memory data store for job queue
- **agentlink-worker** - Dedicated PDF generation worker

### 3. **New File**
- `app/worker_tasks.py` - Contains all RQ tasks for PDF generation

### 4. **Modified Files**
- `requirements.txt` - Added Redis and RQ
- `docker-compose.yml` - Added Redis and worker services
- `app/main.py` - Updated to use RQ instead of background tasks

---

## 🚀 Deployment Steps

### **Step 1: SSH into Your Server**
```bash
ssh root@65.108.146.173
cd /var/www/fastapi-app/AgentLink  # Or your project path
```

### **Step 2: Pull Latest Code**
```bash
git pull origin main  # Or however you deploy
```

### **Step 3: Stop Current Containers**
```bash
docker-compose down
```

### **Step 4: Rebuild Images**
```bash
docker-compose build --no-cache
```

### **Step 5: Start All Services**
```bash
docker-compose up -d
```

### **Step 6: Verify Services Are Running**
```bash
docker-compose ps
```

You should see **4 containers**:
- `agentlink` (FastAPI)
- `agentlink-worker` (RQ Worker)
- `redis` (Redis Server)
- `nginx` (Reverse Proxy)

### **Step 7: Check Logs**
```bash
# Check API logs
docker-compose logs -f agentlink

# Check worker logs
docker-compose logs -f agentlink-worker

# Check Redis logs
docker-compose logs -f redis
```

---

## ✅ Testing

### **Test 1: Single Request**
```bash
curl -X POST http://65.108.146.173/api/generate-agents-report \
  -H "Content-Type: application/json" \
  -d '{
    "suburb": "Manly",
    "state": "NSW",
    "min_bedrooms": 2,
    "property_types": ["House", "Apartment"]
  }'
```

Expected response:
```json
{
  "job_id": "abc-123-xyz",
  "status": "processing"
}
```

### **Test 2: Check Job Status**
```bash
curl http://65.108.146.173/api/job-status/abc-123-xyz
```

Expected response (processing):
```json
{
  "job_id": "abc-123-xyz",
  "status": "fetching_agents_data",
  "progress": 30,
  "dropbox_url": "",
  "filename": "",
  "error": ""
}
```

Expected response (completed):
```json
{
  "job_id": "abc-123-xyz",
  "status": "completed",
  "progress": 100,
  "dropbox_url": "https://www.dropbox.com/s/...",
  "filename": "Manly_Top_Agents_abc-123-xyz.pdf",
  "error": ""
}
```

### **Test 3: Multiple Concurrent Requests**
Open 4-5 terminal windows and run the same POST request simultaneously. Each should:
1. Get a unique job_id
2. Process independently
3. Complete successfully without dropping requests

---

## 📊 Monitoring

### **View Worker Status**
```bash
docker exec -it make-integration-agentlink-worker-1 rq info --url redis://redis:6379/0
```

Output shows:
- Number of workers
- Jobs queued
- Jobs processing
- Jobs completed/failed

### **View Redis Keys**
```bash
docker exec -it make-integration-redis-1 redis-cli
> KEYS job:*
> HGETALL job:abc-123-xyz
> EXIT
```

### **Resource Usage**
```bash
docker stats
```

Expected usage on CX22 (2 vCPU, 4 GB RAM):
- **agentlink**: ~200-300 MB RAM, 10-20% CPU (idle)
- **agentlink-worker**: ~500-800 MB RAM per worker, 50-80% CPU (processing)
- **redis**: ~50-100 MB RAM, minimal CPU
- **nginx**: ~10-20 MB RAM, minimal CPU

---

## 🔧 Configuration Tuning

### **Increase Worker Concurrency** (if server allows)

Edit `docker-compose.yml`:
```yaml
agentlink-worker:
  # ... existing config ...
  command: rq worker --url redis://redis:6379/0 agentlink-queue --burst
  deploy:
    replicas: 2  # Run 2 worker containers
```

Then:
```bash
docker-compose up -d --scale agentlink-worker=2
```

### **Adjust Job Timeout**

In `app/main.py`, modify the enqueue calls:
```python
rq_job = queue.enqueue(
    process_agents_report_task,
    # ... parameters ...
    job_timeout='15m'  # Increase from 10m to 15m if needed
)
```

### **Redis Persistence**

The `docker-compose.yml` already includes persistence:
```yaml
redis:
  command: redis-server --appendonly yes
  volumes:
    - redis-data:/data
```

Jobs persist across Redis restarts! ✅

---

## 🐛 Troubleshooting

### **Problem: Jobs not processing**
```bash
# Check worker logs
docker-compose logs agentlink-worker

# Check if worker is running
docker-compose ps agentlink-worker

# Restart worker
docker-compose restart agentlink-worker
```

### **Problem: Redis connection errors**
```bash
# Check Redis is running
docker-compose ps redis

# Test Redis connection
docker exec -it make-integration-redis-1 redis-cli PING
# Should return: PONG

# Check Redis URL in environment
docker-compose exec agentlink env | grep REDIS_URL
```

### **Problem: Jobs stuck in "processing"**
```bash
# Check if worker died
docker-compose logs agentlink-worker --tail=50

# Restart worker
docker-compose restart agentlink-worker

# Clear stuck jobs (if needed)
docker exec -it make-integration-redis-1 redis-cli
> KEYS job:*
> DEL job:stuck-job-id
```

### **Problem: High memory usage**
```bash
# Check container stats
docker stats

# Reduce worker concurrency
# In docker-compose.yml, add:
agentlink-worker:
  environment:
    RQ_WORKER_NUM: 1  # Reduce from default
```

### **Problem: Jobs failing**
```bash
# Check job status
curl http://65.108.146.173/api/job-status/{job_id}

# Check worker logs for error
docker-compose logs agentlink-worker | grep ERROR

# Check failed jobs in Redis
docker exec -it make-integration-redis-1 rq info --url redis://redis:6379/0
```

---

## 📈 Scaling Beyond 4-5 Requests

### **Option 1: Upgrade Server (Recommended)**
- **CX32** (4 vCPU, 8 GB RAM) = 8-10 concurrent requests
- **CX42** (8 vCPU, 16 GB RAM) = 15-20 concurrent requests

### **Option 2: Add Multiple Workers**
Current setup: 1 worker container

To add more workers:
```bash
docker-compose up -d --scale agentlink-worker=3
```

This runs 3 worker containers, each handling 1-2 requests.

### **Option 3: Horizontal Scaling**
Add another server and point both to the same Redis instance (requires Redis on separate server or managed Redis service).

---

## 🎯 Performance Expectations

### **With Current Setup (1 Worker)**
- **Concurrent Requests**: 1-2 simultaneously
- **Queue Capacity**: Unlimited (jobs wait in queue)
- **Throughput**: 1 PDF every 2-5 minutes
- **RAM Usage**: ~2-3 GB total

### **With 2 Workers (Scaled)**
```bash
docker-compose up -d --scale agentlink-worker=2
```
- **Concurrent Requests**: 2-4 simultaneously
- **Queue Capacity**: Unlimited
- **Throughput**: 2 PDFs every 2-5 minutes
- **RAM Usage**: ~3-4 GB total (near limit of CX22)

### **Recommendation**
Current setup with 1 worker is **optimal for CX22**. For more than 4-5 concurrent users, upgrade to CX32.

---

## 🔐 Security Notes

1. **Redis is exposed on port 6379** (only within Docker network)
2. **No Redis password** - Add one if exposing externally:
   ```yaml
   redis:
     command: redis-server --appendonly yes --requirepass YOUR_PASSWORD
   ```

3. **Job data expires** after 1 hour (configurable in `worker_tasks.py`)

---

## 📝 Backup & Recovery

### **Backup Redis Data**
```bash
docker exec make-integration-redis-1 redis-cli BGSAVE
docker cp make-integration-redis-1:/data/dump.rdb ./redis-backup.rdb
```

### **Restore Redis Data**
```bash
docker-compose down
docker cp ./redis-backup.rdb make-integration-redis-1:/data/dump.rdb
docker-compose up -d
```

---

## 🎉 Success Criteria

After deployment, you should be able to:
✅ Send 5 requests back-to-back without any being dropped
✅ Track each job's progress independently
✅ See all jobs complete successfully
✅ Find all PDFs uploaded to Dropbox
✅ Check job status even after server restart (Redis persistence)

---

## 📞 Quick Commands Reference

```bash
# Deploy updates
git pull && docker-compose down && docker-compose build --no-cache && docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Restart specific service
docker-compose restart agentlink-worker

# Scale workers
docker-compose up -d --scale agentlink-worker=2

# Check Redis
docker exec -it make-integration-redis-1 redis-cli INFO

# Monitor resources
docker stats

# Clean up old images
docker image prune -a
```

---

**Deployment Date**: 2025-10-11  
**Deployed By**: DevOps Team  
**Server**: Hetzner CX22 (65.108.146.173)  
**Status**: ✅ Ready for Production
