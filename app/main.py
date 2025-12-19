# Standard library imports
import logging
import os
import glob
import uuid
from datetime import datetime
from typing import Optional
from pathlib import Path

# Third-party imports
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

# Local application imports - RQ worker tasks
from app.worker_tasks import (
    process_agents_report_task, 
    process_agency_report_task, 
    queue, 
    get_job_status, 
    update_job_status
)

# Configure logging with date and time in filename
log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
os.makedirs(log_dir, exist_ok=True)

# Create a log file with a more readable date and time format
current_datetime = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
log_file = os.path.join(log_dir, f"ArticFlow_{current_datetime}.log")

# Configure logging - MODIFIED to ensure console output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()  # This should send logs to console
    ]
)

# Get the root logger - REMOVED reference to DailyLogHandler
root_logger = logging.getLogger()
# No need to add handlers that don't exist

logger = logging.getLogger("articflow")

# Load environment variables
load_dotenv()
logger.info("Environment variables loaded")

app = FastAPI(title="Property PDF Generator API")
logger.info("FastAPI application initialized")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
logger.info("CORS middleware configured")

# Job storage is now in Redis via worker_tasks.py
logger.info("Using Redis for job storage")

class PropertyRequest(BaseModel):
    property_id: str
    agent_id: str = None
    featured_agent_id: str = None
    suburb: str = "Queenscliff"
    state: str = "NSW"
    property_types: Optional[list] = None
    
class AgentsReportRequest(BaseModel):
    featured_agent_id: str = None
    suburb: str = "Queenscliff"
    state: str = "NSW"
    property_types: Optional[list] = None
    min_bedrooms: Optional[int] = 1
    max_bedrooms: Optional[int] = None
    min_bathrooms: Optional[int] = 1
    max_bathrooms: Optional[int] = None
    min_carspaces: Optional[int] = 1
    max_carspaces: Optional[int] = None
    include_surrounding_suburbs: Optional[bool] = False
    post_code: Optional[str] = None
    region: Optional[str] = None
    area: Optional[str] = None
    min_land_area: Optional[int] = None  # Added parameter for minimum land size
    max_land_area: Optional[int] = None  # Added parameter for maximum land size
    home_owner_pricing: Optional[str] = None  

class AgencyReportRequest(BaseModel):
    featured_agency_id: str = None
    suburb: str = "Queenscliff"
    state: str = "NSW"
    property_types: Optional[list] = None
    min_bedrooms: Optional[int] = 1
    max_bedrooms: Optional[int] = None
    min_bathrooms: Optional[int] = 1
    max_bathrooms: Optional[int] = None
    min_carspaces: Optional[int] = 1
    max_carspaces: Optional[int] = None
    include_surrounding_suburbs: Optional[bool] = False
    post_code: Optional[str] = None
    region: Optional[str] = None
    area: Optional[str] = None
    min_land_area: Optional[int] = None  # Added parameter for minimum land size
    max_land_area: Optional[int] = None  # Added parameter for maximum land size
    home_owner_pricing: Optional[str] = None

class JobResponse(BaseModel):
    job_id: str
    status: str

class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    progress: int = 0
    dropbox_url: Optional[str] = None
    filename: Optional[str] = None  
    commission_dropbox_url: Optional[str] = None  
    commission_filename: Optional[str] = None  
    commission_rate: Optional[str] = ""  
    discount: Optional[str] = ""  
    completed_pdf_url: Optional[str] = ""  
    completed_filename: Optional[str] = ""  
    error: Optional[str] = ""  # Changed from None to empty string as default



def clear_temp_pdfs(temp_dir=None):
    """Clear temporary PDF files from the specified directory."""
    if temp_dir is None:
        # Use default temp directory if none specified
        temp_dir = Path("app/temp")
    
    # Create the directory if it doesn't exist
    os.makedirs(temp_dir, exist_ok=True)
    
    # Remove all PDF files in the temp directory
    for pdf_file in glob.glob(os.path.join(temp_dir, "*.pdf")):
        try:
            os.remove(pdf_file)
        except Exception as e:
            print(f"Error removing file {pdf_file}: {e}")
            
            
@app.get("/api/job-status/{job_id}", response_model=JobStatusResponse)
async def job_status_endpoint(job_id: str):
    logger.info(f"Status check for job {job_id}")
    
    # Get job status from Redis
    job = get_job_status(job_id)
    
    if not job:
        logger.warning(f"Job {job_id} not found")
        raise HTTPException(status_code=404, detail="Job not found")
    
    logger.info(f"Current status for job {job_id}: {job.get('status')}")
    
    # Calculate progress based on status
    progress = 0
    status = job.get("status", "processing")
    if status == "processing":
        progress = 10
    elif status == "fetching_property_data" or status == "fetching_agents_data" or status == "fetching_agency_data":
        progress = 30
    elif status == "generating_commission_pdf":
        progress = 45  
    elif status == "generating_pdf":
        progress = 60
    elif status == "uploading_to_dropbox":
        progress = 85
    elif status == "creating_completed_pdf":
        progress = 92
    elif status == "completed":
        progress = 100
    elif status == "failed":
        progress = 0
    
    # Ensure error is always a string
    error = job.get("error", "")
    if error is None:
        error = ""
    
    logger.info(f"Progress for job {job_id}: {progress}%")
    
    return {
        "job_id": job_id,
        "status": status,
        "progress": progress,
        "dropbox_url": job.get("dropbox_url", ""),
        "filename": job.get("filename", ""),
        "commission_dropbox_url": job.get("commission_dropbox_url", ""),
        "commission_filename": job.get("commission_filename", ""),
        "commission_rate": job.get("commission_rate", ""),
        "discount": job.get("discount", ""),
        "completed_pdf_url": job.get("completed_pdf_url", ""),
        "completed_filename": job.get("completed_filename", ""),
        "error": error
    }

# Add this after initializing the FastAPI app
templates = Jinja2Templates(directory="app/templates")

# Add this new endpoint
# Fix the generate-agents-report endpoint to use AgentsReportRequest
@app.post("/api/generate-agents-report", response_model=JobResponse)
async def generate_agents_report(request: AgentsReportRequest):
    clear_temp_pdfs()
    # Generate a unique job ID
    job_id = str(uuid.uuid4())
    logger.info(f"New agents report job created: {job_id}")
    logger.info(f"Request details: suburb={request.suburb}, state={request.state}, property_types={request.property_types}")
    
    # Initialize job status in Redis
    update_job_status(job_id, "processing", suburb=request.suburb)
    logger.info(f"Agents report job {job_id} initialized with status 'processing'")
    
    # Enqueue task to RQ worker
    rq_job = queue.enqueue(
        process_agents_report_task,
        job_id, 
        request.suburb,
        request.state,
        request.property_types,
        min_bedrooms=request.min_bedrooms,
        max_bedrooms=request.max_bedrooms,
        min_bathrooms=request.min_bathrooms,
        max_bathrooms=request.max_bathrooms,
        min_carspaces=request.min_carspaces,
        max_carspaces=request.max_carspaces,
        include_surrounding_suburbs=request.include_surrounding_suburbs,
        post_code=request.post_code,
        region=request.region,
        area=request.area,
        featured_agent_id=request.featured_agent_id,
        min_land_area=request.min_land_area,
        max_land_area=request.max_land_area,
        home_owner_pricing=request.home_owner_pricing,
        job_timeout='10m'  # 10 minute timeout for PDF generation
    )
    logger.info(f"RQ task enqueued for agents report job {job_id}, RQ Job ID: {rq_job.id}")
    
    return {"job_id": job_id, "status": "processing"}


@app.post("/api/generate-agency-report", response_model=JobResponse)
async def generate_agency_report(request: AgencyReportRequest):
    clear_temp_pdfs()
    # Generate a unique job ID
    job_id = str(uuid.uuid4())
    logger.info(f"New agency report job created: {job_id}")
    logger.info(f"Request details: suburb={request.suburb}, state={request.state}, property_types={request.property_types}")
    
    # Initialize job status in Redis
    update_job_status(job_id, "processing", suburb=request.suburb)
    logger.info(f"Agency report job {job_id} initialized with status 'processing'")
    
    # Enqueue task to RQ worker
    rq_job = queue.enqueue(
        process_agency_report_task,
        job_id, 
        request.suburb,
        request.state,
        request.property_types,
        min_bedrooms=request.min_bedrooms,
        max_bedrooms=request.max_bedrooms,
        min_bathrooms=request.min_bathrooms,
        max_bathrooms=request.max_bathrooms,
        min_carspaces=request.min_carspaces,
        max_carspaces=request.max_carspaces,
        include_surrounding_suburbs=request.include_surrounding_suburbs,
        post_code=request.post_code,
        region=request.region,
        area=request.area,
        featured_agency_id=request.featured_agency_id,
        min_land_area=request.min_land_area,
        max_land_area=request.max_land_area,
        job_timeout='10m'  # 10 minute timeout for PDF generation
    )
    logger.info(f"RQ task enqueued for agency report job {job_id}, RQ Job ID: {rq_job.id}")
    
    return {"job_id": job_id, "status": "processing"}


if __name__ == "__main__":
    # Add a test log message to verify logging is working
    logger.info("Starting the application server")
    print("Direct print: Starting the application server")  # Direct print for testing
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)