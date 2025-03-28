# Standard library imports
import asyncio
import logging
import os
import glob
import shutil
from pathlib import Path
import uuid
from datetime import datetime
from typing import Optional

# Third-party imports
import uvicorn
from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

# Local application imports
from app.services.domain_service import fetch_property_data
from app.services.domain_agency_service import fetch_rented_property_data  # Import the function from domain_agency_service
from app.services.dropbox_service import upload_to_dropbox
from app.services.html_pdf_service import generate_pdf_with_weasyprint

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

# In-memory job storage (replace with a database in production)
jobs = {}
logger.info("In-memory job storage initialized")

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

class JobResponse(BaseModel):
    job_id: str
    status: str

class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    progress: int = 0
    dropbox_url: Optional[str] = None
    filename: Optional[str] = None  # Add this line to include filename in response
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
            
@app.post("/api/generate-pdf", response_model=JobResponse)
async def generate_pdf_endpoint(request: PropertyRequest, background_tasks: BackgroundTasks):
    # Generate a unique job ID
    job_id = str(uuid.uuid4())
    logger.info(f"New job created: {job_id}")
    logger.info(f"Request details: suburb={request.suburb}, state={request.state}, agent_id={request.agent_id}, featured_agent_id={request.featured_agent_id}, property_types={request.property_types}")
    
    # Store job in the jobs dictionary with initial status
    jobs[job_id] = {
        "status": "processing",
        "suburb": request.suburb,  # Store suburb in job data
        "dropbox_url": None,
        "error": None
    }
    logger.info(f"Job {job_id} initialized with status 'processing'")
    
    # Start background task to process the job - fixed parameter order to match function signature
    background_tasks.add_task(
        process_agents_report_job, 
        job_id,
        request.suburb,
        request.state,
        request.property_types
    )
    logger.info(f"Background task started for job {job_id}")
    
    return {"job_id": job_id, "status": "processing"}

@app.get("/api/job-status/{job_id}", response_model=JobStatusResponse)
async def job_status_endpoint(job_id: str):
    logger.info(f"Status check for job {job_id}")
    
    if job_id not in jobs:
        logger.warning(f"Job {job_id} not found")
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    logger.info(f"Current status for job {job_id}: {job['status']}")
    
    # Calculate progress based on status
    progress = 0
    if job["status"] == "processing":
        progress = 10
    elif job["status"] == "fetching_property_data":
        progress = 30
    elif job["status"] == "generating_pdf":
        progress = 60
    elif job["status"] == "uploading_to_dropbox":
        progress = 85
    elif job["status"] == "completed":
        progress = 100
    elif job["status"] == "failed":
        progress = 0
    
    # Ensure error is always a string
    error = job.get("error", "")
    if error is None:
        error = ""
    
    logger.info(f"Progress for job {job_id}: {progress}%")
    
    return {
        "job_id": job_id,
        "status": job["status"],
        "progress": progress,
        "dropbox_url": job.get("dropbox_url"),
        "filename": job.get("filename"),  # Include the filename in the response
        "error": error
    }

# Add this after initializing the FastAPI app
templates = Jinja2Templates(directory="app/templates")

# Add this new endpoint
# Fix the generate-agents-report endpoint to use AgentsReportRequest
@app.post("/api/generate-agents-report", response_model=JobResponse)
async def generate_agents_report(request: AgentsReportRequest, background_tasks: BackgroundTasks):
    clear_temp_pdfs()
    # Generate a unique job ID
    job_id = str(uuid.uuid4())
    logger.info(f"New agents report job created: {job_id}")
    logger.info(f"Request details: suburb={request.suburb}, state={request.state}, property_types={request.property_types}")
    
    # Store job in the jobs dictionary with initial status
    jobs[job_id] = {
        "status": "processing",
        "suburb": request.suburb,  # Store suburb in job data
        "dropbox_url": None,
        "error": None
    }
    logger.info(f"Agents report job {job_id} initialized with status 'processing'")
    
    # Start background task to process the job with all filter parameters
    background_tasks.add_task(
        process_agents_report_job, 
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
        min_land_area=request.min_land_area,  # Added parameter
        max_land_area=request.max_land_area   # Added parameter
    )
    logger.info(f"Background task started for agents report job {job_id}")
    
    return {"job_id": job_id, "status": "processing"}

async def process_agents_report_job(
    job_id: str, 
    suburb: str = "Queenscliff", 
    state: str = "NSW",
    property_types: list = None,
    min_bedrooms: int = 1,
    max_bedrooms: int = None,
    min_bathrooms: int = 1,
    max_bathrooms: int = None,
    min_carspaces: int = 1,
    max_carspaces: int = None,
    include_surrounding_suburbs: bool = False,
    post_code: str = None,
    region: str = None,
    area: str = None,
    featured_agent_id: str = None,
    min_land_area: int = None,  # Added parameter
    max_land_area: int = None   # Added parameter
):
    try:
        logger.info(f"Starting to process agents report job {job_id}")
        
        # Update status to show we're fetching data
        jobs[job_id]["status"] = "fetching_agents_data"
        logger.info(f"Job {job_id}: Fetching agents data for suburb={suburb}")
        
        # Add a delay to simulate API call to Domain.com.au
        await asyncio.sleep(3)
        logger.info(f"Job {job_id}: API call simulation completed")
        
        # Step 1: Fetch agents data from Domain.com.au API with all filter parameters
        agents_data = await fetch_property_data(
            property_id="not_used",  # Not needed for agents report
            job_id=job_id,
            suburb=suburb,
            state=state,
            property_types=property_types,
            min_bedrooms=min_bedrooms,
            max_bedrooms=max_bedrooms,
            min_bathrooms=min_bathrooms,
            max_bathrooms=max_bathrooms,
            min_carspaces=min_carspaces,
            max_carspaces=max_carspaces,
            include_surrounding_suburbs=include_surrounding_suburbs,
            post_code=post_code,
            region=region,
            area=area,
            min_land_area=min_land_area,  # Added parameter
            max_land_area=max_land_area   # Added parameter
        )
        logger.info(f"Job {job_id}: Agents data fetched successfully")
        
        # Update status to show we're generating PDF
        jobs[job_id]["status"] = "generating_pdf"
        logger.info(f"Job {job_id}: Starting agents report PDF generation")
        
        # Add a delay to simulate PDF generation
        await asyncio.sleep(5)
        
        # Step 2: Generate PDF with the agents data using WeasyPrint
        # Create a context for the template with the suburb and agents
        context = {
            "suburb": suburb,
            "agents": agents_data["top_agents"]
        }
        
        # Generate the PDF using the agents_report.html template
        pdf_path = await generate_pdf_with_weasyprint(
            context, 
            job_id=job_id,
            template_name="agents_report.html"  # Specify the template to use
        )
        logger.info(f"Job {job_id}: Agents report PDF generated successfully at {pdf_path}")
        
        # Update status to show we're uploading to Dropbox
        jobs[job_id]["status"] = "uploading_to_dropbox"
        logger.info(f"Job {job_id}: Starting Dropbox upload")
        
        # Add a delay to simulate Dropbox upload
        await asyncio.sleep(4)
        
        # Step 3: Upload PDF to Dropbox with proper filename and folder path
        # In the process_agents_report_job function, after creating the filename
        filename = f"{suburb}_Top_Agents_{job_id}.pdf"  # Create a meaningful filename
        dropbox_folder = "/Suburbs Top Agents"  # Specify the target folder in Dropbox
        dropbox_url = await upload_to_dropbox(pdf_path, filename, folder_path=dropbox_folder)
        logger.info(f"Job {job_id}: PDF uploaded to Dropbox successfully to folder {dropbox_folder}")
        logger.info(f"Job {job_id}: Dropbox URL: {dropbox_url}")
        
        # Update job status - add the filename to the job data
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["dropbox_url"] = dropbox_url
        jobs[job_id]["filename"] = filename  # Store the filename in the job data
        logger.info(f"Job {job_id}: Completed successfully")
        
        # Clean up the temporary PDF file
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
            logger.info(f"Job {job_id}: Temporary PDF file removed")
            
    except Exception as e:
        # Update job with error
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)
        logger.error(f"Error processing agents report job {job_id}: {str(e)}", exc_info=True)
        print(f"Error processing agents report job {job_id}: {str(e)}")




# Add after the generate-agents-report endpoint
# Update the generate-agency-report endpoint to use AgencyReportRequest
@app.post("/api/generate-agency-report", response_model=JobResponse)
async def generate_agency_report(request: AgencyReportRequest, background_tasks: BackgroundTasks):
    clear_temp_pdfs()
    # Generate a unique job ID
    job_id = str(uuid.uuid4())
    logger.info(f"New agency report job created: {job_id}")
    logger.info(f"Request details: suburb={request.suburb}, state={request.state}, property_types={request.property_types}")
    
    # Store job in the jobs dictionary with initial status
    jobs[job_id] = {
        "status": "processing",
        "suburb": request.suburb,  # Store suburb in job data
        "dropbox_url": None,
        "error": None
    }
    logger.info(f"Agency report job {job_id} initialized with status 'processing'")
    
    # Start background task to process the job with all filter parameters
    background_tasks.add_task(
        process_agency_report_job, 
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
        min_land_area=request.min_land_area,  # Added parameter
        max_land_area=request.max_land_area   # Added parameter
    )
    logger.info(f"Background task started for agency report job {job_id}")
    
    return {"job_id": job_id, "status": "processing"}

# Add after process_agents_report_job function
async def process_agency_report_job(
    job_id: str, 
    suburb: str = "Queenscliff", 
    state: str = "NSW",
    property_types: list = None,
    min_bedrooms: int = 1,
    max_bedrooms: int = None,
    min_bathrooms: int = 1,
    max_bathrooms: int = None,
    min_carspaces: int = 1,
    max_carspaces: int = None,
    include_surrounding_suburbs: bool = False,
    post_code: str = None,
    region: str = None,
    area: str = None,
    featured_agency_id: str = None,
    min_land_area: int = None,  # Added parameter
    max_land_area: int = None   # Added parameter
):
    try:
        logger.info(f"Starting to process agency report job {job_id}")
        
        # Update status to show we're fetching data
        jobs[job_id]["status"] = "fetching_agency_data"
        logger.info(f"Job {job_id}: Fetching agency data for suburb={suburb}")
        
        # Add a delay to simulate API call to Domain.com.au
        await asyncio.sleep(3)
        logger.info(f"Job {job_id}: API call simulation completed")
        
        # Step 1: Fetch agency data from Domain.com.au API with all filter parameters
        agency_data = await fetch_rented_property_data(
            property_id="not_used",  # Not needed for agency report
            job_id=job_id,
            suburb=suburb,
            state=state,
            property_types=property_types,
            min_bedrooms=min_bedrooms,
            max_bedrooms=max_bedrooms,
            min_bathrooms=min_bathrooms,
            max_bathrooms=max_bathrooms,
            min_carspaces=min_carspaces,
            max_carspaces=max_carspaces,
            include_surrounding_suburbs=include_surrounding_suburbs,
            post_code=post_code,
            region=region,
            area=area,
            min_land_area=min_land_area,  # Added parameter
            max_land_area=max_land_area   # Added parameter
        )
        logger.info(f"Job {job_id}: Agency data fetched successfully")
        
        # Update status to show we're generating PDF
        jobs[job_id]["status"] = "generating_pdf"
        logger.info(f"Job {job_id}: Starting agency report PDF generation")
        
        # Add a delay to simulate PDF generation
        await asyncio.sleep(5)
        
        # In the process_agency_report_job function, before generating the PDF
        # Step 2: Generate PDF with the agency data using WeasyPrint
        # Create a context for the template with the suburb and agencies
        context = {
            "suburb": suburb,
            "agencies": agency_data["top_agencies"]
        }
        
        # Debug: Print the actual data being passed to the template
        print("\nData being passed to the template:")
        for i, agency in enumerate(agency_data["top_agencies"]):
            print(f"Agency #{i+1}: {agency['name']}")
            print(f"  - logoUrl: {agency.get('logoUrl', 'None')}")
            print(f"  - totalPropertiesLeased: {agency.get('totalPropertiesLeased', 0)}")
            print(f"  - totalPropertiesForLease: {agency.get('totalPropertiesForLease', 0)}")
            print(f"  - totalRentedProperties: {agency.get('totalRentedProperties', 0)}")
            print(f"  - leasingEfficiency: {agency.get('leasingEfficiency', 0)}")
        
        # Generate the PDF using the agency_report.html template
        pdf_path = await generate_pdf_with_weasyprint(
            context, 
            job_id=job_id,
            template_name="agency_report.html"  # Specify the template to use
        )
        logger.info(f"Job {job_id}: Agency report PDF generated successfully at {pdf_path}")
        
        # Update status to show we're uploading to Dropbox
        jobs[job_id]["status"] = "uploading_to_dropbox"
        logger.info(f"Job {job_id}: Starting Dropbox upload")
        
        # Add a delay to simulate Dropbox upload
        await asyncio.sleep(4)
        
        # Step 3: Upload PDF to Dropbox with proper filename and folder path
        filename = f"{suburb}_Top_Rental_Agencies_{job_id}.pdf"  # Create a meaningful filename
        dropbox_folder = "/Suburbs Top Rental Agencies"  # Specify the target folder in Dropbox
        dropbox_url = await upload_to_dropbox(pdf_path, filename, folder_path=dropbox_folder)
        logger.info(f"Job {job_id}: PDF uploaded to Dropbox successfully to folder {dropbox_folder}")
        logger.info(f"Job {job_id}: Dropbox URL: {dropbox_url}")
        
        # Update job status - add the filename to the job data
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["dropbox_url"] = dropbox_url
        jobs[job_id]["filename"] = filename  # Store the filename in the job data
        logger.info(f"Job {job_id}: Completed successfully")
        
        # Clean up the temporary PDF file
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
            logger.info(f"Job {job_id}: Temporary PDF file removed")
            
    except Exception as e:
        # Update job with error
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)
        logger.error(f"Error processing agency report job {job_id}: {str(e)}", exc_info=True)
        print(f"Error processing agency report job {job_id}: {str(e)}")

if __name__ == "__main__":
    # Add a test log message to verify logging is working
    logger.info("Starting the application server")
    print("Direct print: Starting the application server")  # Direct print for testing
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)