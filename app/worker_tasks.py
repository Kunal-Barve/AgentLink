"""
RQ Worker Tasks for AgentLink
This file contains all background tasks that will be processed by RQ workers
"""
import os
import asyncio
import logging
from datetime import datetime
import redis
from rq import Queue

from app.services.domain_service import fetch_property_data
from app.services.domain_agency_service import fetch_rented_property_data
from app.services.dropbox_service import upload_to_dropbox
from app.services.html_pdf_service import generate_pdf_with_weasyprint
from app.services.agent_commission import get_agent_commission, get_area_type

# Set up logging
logger = logging.getLogger("articflow.worker")

# Redis connection
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
redis_conn = redis.from_url(REDIS_URL)

# Create RQ queue
queue = Queue('agentlink-queue', connection=redis_conn)


def update_job_status(job_id: str, status: str, **kwargs):
    """Update job status in Redis"""
    job_data = {
        "status": status,
        "updated_at": datetime.now().isoformat()
    }
    job_data.update(kwargs)
    redis_conn.hset(f"job:{job_id}", mapping=job_data)
    redis_conn.expire(f"job:{job_id}", 3600)  # Expire after 1 hour
    logger.info(f"Job {job_id} status updated to: {status}")


def get_job_status(job_id: str) -> dict:
    """Get job status from Redis"""
    data = redis_conn.hgetall(f"job:{job_id}")
    if not data:
        return None
    # Decode bytes to strings
    return {k.decode(): v.decode() for k, v in data.items()}


async def get_commission_rate_async(agents_data, job_id, suburb, home_owner_pricing, post_code, state):
    """
    Generate a commission report PDF based on agent data and upload it to Dropbox.
    """
    try:
        logger.info(f"Job {job_id}: Starting commission report generation")
        
        # Check if we have any featured agents
        has_featured_agent = any(agent.get('featured', False) for agent in agents_data["top_agents"])
        has_featured_plus_agent = any(agent.get('featured_plus', False) for agent in agents_data["top_agents"])
        
        commission_rate = ""
        discount = ""
        marketing_cost = ""
        
        if agents_data["top_agents"]:
            if has_featured_agent:
                featured_agent = next((agent for agent in agents_data["top_agents"] if agent.get('featured', False)), None)
                if featured_agent:
                    commission_rate = featured_agent.get("commission_rate", "")
                    discount = featured_agent.get("discount", "")
                    marketing_cost = featured_agent.get("marketing", "")
            else:
                commission_rate = agents_data["top_agents"][0].get("commission_rate", "")
                marketing_cost = agents_data["top_agents"][0].get("marketing", "")
                
        if (not commission_rate or not marketing_cost) and home_owner_pricing:
            area_type = get_area_type(post_code, suburb)
            standard_rates = get_agent_commission(home_owner_pricing, area_type, state)
            commission_rate = standard_rates.get("commission_rate", "")
            marketing_cost = standard_rates.get("marketing", "")
        
        context = {
            "suburb": suburb,
            "commission_rate": commission_rate,
            "discount": discount,
            "marketing_cost": marketing_cost,
            "has_featured_agent": has_featured_agent,
            "has_featured_plus_agent": has_featured_plus_agent
        }
        
        pdf_path = await generate_pdf_with_weasyprint(
            context, 
            job_id=job_id,
            template_name="commission_report.html"
        )
        
        filename = f"{suburb}_Commission_{job_id}.pdf"
        dropbox_folder = "/Commission Rate"
        dropbox_url = await upload_to_dropbox(pdf_path, filename, folder_path=dropbox_folder)
        
        # Clean up temporary file
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
            
        return dropbox_url, filename, commission_rate, discount
        
    except Exception as e:
        logger.error(f"Error generating commission report for job {job_id}: {str(e)}", exc_info=True)
        return None, None, "", ""


def process_agents_report_task(
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
    min_land_area: int = None,
    max_land_area: int = None,
    home_owner_pricing: str = None
):
    """
    RQ Task: Process agents report generation
    This runs in a separate worker process
    """
    try:
        logger.info(f"Worker: Starting to process agents report job {job_id}")
        update_job_status(job_id, "fetching_agents_data", suburb=suburb)
        
        # Use asyncio.run to execute async functions
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Step 1: Fetch agents data
        agents_data = loop.run_until_complete(fetch_property_data(
            property_id="not_used",
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
            min_land_area=min_land_area,
            max_land_area=max_land_area,
            home_owner_pricing=home_owner_pricing
        ))
        
        logger.info(f"Job {job_id}: Agents data fetched successfully")
        
        # Generate commission report if needed
        commission_dropbox_url = None
        commission_filename = None
        commission_rate = ""
        discount = ""
        if home_owner_pricing:
            update_job_status(job_id, "generating_commission_pdf")
            commission_dropbox_url, commission_filename, commission_rate, discount = loop.run_until_complete(
                get_commission_rate_async(agents_data, job_id, suburb, home_owner_pricing, post_code, state)
            )
            logger.info(f"Job {job_id}: Commission report generated: {commission_dropbox_url}")
        
        # Step 2: Generate PDF
        update_job_status(job_id, "generating_pdf")
        
        context = {
            "suburb": suburb,
            "agents": agents_data["top_agents"]
        }
        
        template_name = "not_found.html" if not agents_data["top_agents"] else "agents_report.html"
        
        pdf_path = loop.run_until_complete(generate_pdf_with_weasyprint(
            context, 
            job_id=job_id,
            template_name=template_name
        ))
        
        logger.info(f"Job {job_id}: PDF generated at {pdf_path}")
        
        # Step 3: Upload to Dropbox
        update_job_status(job_id, "uploading_to_dropbox")
        
        filename = f"{suburb}_Top_Agents_{job_id}.pdf"
        dropbox_folder = "/Suburbs Top Agents"
        dropbox_url = loop.run_until_complete(upload_to_dropbox(pdf_path, filename, folder_path=dropbox_folder))
        
        logger.info(f"Job {job_id}: PDF uploaded to Dropbox: {dropbox_url}")
        
        # Clean up
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
        
        # Update final status
        update_job_status(
            job_id, 
            "completed",
            dropbox_url=dropbox_url,
            filename=filename,
            commission_dropbox_url=commission_dropbox_url or "",
            commission_filename=commission_filename or "",
            commission_rate=commission_rate,
            discount=discount,
            error=""
        )
        
        loop.close()
        logger.info(f"Job {job_id}: Completed successfully")
        
    except Exception as e:
        logger.error(f"Error processing agents report job {job_id}: {str(e)}", exc_info=True)
        update_job_status(job_id, "failed", error=str(e))


def process_agency_report_task(
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
    min_land_area: int = None,
    max_land_area: int = None
):
    """
    RQ Task: Process agency report generation
    This runs in a separate worker process
    """
    try:
        logger.info(f"Worker: Starting to process agency report job {job_id}")
        update_job_status(job_id, "fetching_agency_data", suburb=suburb)
        
        # Use asyncio.run to execute async functions
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Step 1: Fetch agency data
        agency_data = loop.run_until_complete(fetch_rented_property_data(
            property_id="not_used",
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
            min_land_area=min_land_area,
            max_land_area=max_land_area
        ))
        
        logger.info(f"Job {job_id}: Agency data fetched successfully")
        
        # Step 2: Generate PDF
        update_job_status(job_id, "generating_pdf")
        
        context = {
            "suburb": suburb,
            "agencies": agency_data["top_agencies"]
        }
        
        pdf_path = loop.run_until_complete(generate_pdf_with_weasyprint(
            context, 
            job_id=job_id,
            template_name="agency_report.html"
        ))
        
        logger.info(f"Job {job_id}: Agency PDF generated at {pdf_path}")
        
        # Step 3: Upload to Dropbox
        update_job_status(job_id, "uploading_to_dropbox")
        
        filename = f"{suburb}_Top_Rental_Agencies_{job_id}.pdf"
        dropbox_folder = "/Suburbs Top Rental Agencies"
        dropbox_url = loop.run_until_complete(upload_to_dropbox(pdf_path, filename, folder_path=dropbox_folder))
        
        logger.info(f"Job {job_id}: PDF uploaded to Dropbox: {dropbox_url}")
        
        # Clean up
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
        
        # Update final status
        update_job_status(
            job_id, 
            "completed",
            dropbox_url=dropbox_url,
            filename=filename,
            error=""
        )
        
        loop.close()
        logger.info(f"Job {job_id}: Completed successfully")
        
    except Exception as e:
        logger.error(f"Error processing agency report job {job_id}: {str(e)}", exc_info=True)
        update_job_status(job_id, "failed", error=str(e))
