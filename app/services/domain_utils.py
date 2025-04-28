import os
import requests
import logging
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
load_dotenv()
# Domain.com.au API credentials
DOMAIN_API_KEY = os.getenv("DOMAIN_API_KEY")
DOMAIN_API_SECRET = os.getenv("DOMAIN_API_SECRET")
# Set up logging with more detailed configuration
logger = logging.getLogger("articflow.domain.utils")

def format_price(price):
    """Format a price value as a string with appropriate units (k or m)"""
    if price >= 1000000:
        return f"${price/1000000:.1f}m"
    elif price >= 1000:
        return f"${price/1000:.0f}k"
    else:
        return f"${price:.0f}"

async def check_featured_agent(suburb, state):
    """
    Check for featured agents in a suburb by calling the Make.com webhook
    
    Args:
        suburb: The suburb to check for
        state: The state to check for
        
    Returns:
        List of featured agents for the suburb or None if no agents found.
        Each agent will have an additional 'is_featured_plus' boolean field.
    """
    webhook_url = "https://hook.eu2.make.com/nuedlxjy6fsn398sa31tfh1ca6sgycda"
    
    try:
        # Prepare the data to send to the webhook
        data = {
            "suburb": suburb,
            "state": state
        }
        
        # Make the POST request to the webhook
        response = requests.post(webhook_url, json=data)
        
        # Check if the request was successful
        if response.status_code == 200:
            # Parse the response JSON
            result = response.json()
            
            # Check if we have valid agents data
            if isinstance(result, list) and len(result) > 0:
                # Check if we have an empty agent record (no agents for this suburb)
                first_agent = result[0]
                if not first_agent.get("Name") or first_agent.get("Name").strip() == "":
                    logger.info(f"No featured agents found for {suburb}, {state}")
                    return None
                
                # Process each agent to add is_featured_plus flag
                for agent in result:
                    subscription_type = agent.get("Subscription Type", "")
                    agent["is_featured_plus"] = subscription_type == "Featured Plus"
                    logger.info(f"Agent {agent.get('Name')} has subscription type: {subscription_type}, is_featured_plus: {agent['is_featured_plus']}")
                
                logger.info(f"Found {len(result)} featured agents for {suburb}, {state}")
                return result
            else:
                logger.warning(f"Unexpected response format from featured agent webhook: {result}")
                return None
        else:
            logger.error(f"Failed to check featured agents: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error checking featured agents: {e}")
        return None
    
async def check_standard_subscription(agent_name, suburb, state):
    """
    Check if an agent has a standard subscription by calling the Make.com webhook
    
    Args:
        agent_name: The name of the agent to check
        suburb: The suburb to check for
        state: The state to check for
        
    Returns:
        Boolean indicating whether the agent has a standard subscription
    """
    webhook_url = "https://hook.eu2.make.com/gne36wgwoje49c54gwrz8lnf749mxw3e"
    
    try:
        # Prepare the data to send to the webhook
        data = {
            "agent_name": agent_name,
            "suburb": suburb,
            "state": state
        }
        
        # Make the POST request to the webhook
        response = requests.post(webhook_url, json=data)
        
        # Check if the request was successful
        if response.status_code == 200:
            # Try to parse as JSON first
            try:
                result = response.json()
                
                # Handle different response formats
                if isinstance(result, bool):
                    # If the result is already a boolean, use it directly
                    has_subscription = result
                elif isinstance(result, dict):
                    # If the result is a dictionary, extract the subscription status
                    has_subscription = result.get('standard_subscription', False)
                else:
                    # For any other type, convert to boolean
                    has_subscription = bool(result)
            except ValueError:
                # If JSON parsing fails, try to interpret the text response
                text_response = response.text.strip().lower()
                has_subscription = text_response == 'true'
            
            # Log only once with a more specific message
            logger.info(f"Standard subscription check for agent {agent_name} in {suburb}: {has_subscription}")
            return has_subscription
        else:
            logger.error(f"Failed to check standard subscription status: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error checking standard subscription status: {e}")
        return False

def get_mock_property_data(property_id, agent_id=None, featured_agent_id=None, job_id=None, suburb=None):
    """Generate mock property and agent data for prototype"""
    
    # Create a list of top local agents for Queenscliff (similar to the reference image)
    queenscliff_agents = [
        {
            "id": "agent1",
            "name": "Jonathan Morton",
            "agency": "Raine & Horne",
            "photo": "https://randomuser.me/api/portraits/men/32.jpg",
            "total_sales": 11,
            "avg_days_on_market": 28,
            "median_sold_price": "$1.60m",
            "featured": featured_agent_id == "agent1" or (featured_agent_id is None and suburb != "Brandy Hill")
        },
        {
            "id": "agent2",
            "name": "Adam Moore",
            "agency": "Stone",
            "photo": "https://randomuser.me/api/portraits/men/44.jpg",
            "total_sales": 8,
            "avg_days_on_market": 31,
            "median_sold_price": "$1.80m",
            "featured": False
        },
        {
            "id": "agent3",
            "name": "Anita Wildash",
            "agency": "Cunninghams",
            "photo": "https://randomuser.me/api/portraits/women/65.jpg",
            "total_sales": 4,
            "avg_days_on_market": 8,
            "median_sold_price": "$1.30m",
            "featured": False
        },
        {
            "id": "agent4",
            "name": "Sean King",
            "agency": "Whitehouse",
            "photo": "https://randomuser.me/api/portraits/men/52.jpg",
            "total_sales": 4,
            "avg_days_on_market": 12,
            "median_sold_price": "$1.20m",
            "featured": False
        },
        {
            "id": "agent5",
            "name": "Tim Cullen",
            "agency": "McGrath",
            "photo": "https://randomuser.me/api/portraits/men/22.jpg",
            "total_sales": 3,
            "avg_days_on_market": 20,
            "median_sold_price": "$1.10m",
            "featured": False
        }
    ]
    
    # Create a list of top local agents for Brandy Hill (with same agencies but different agents)
    brandy_hill_agents = [
        {
            "id": "agent6",
            "name": "Sarah Williams",
            "agency": "Raine & Horne",
            "photo": "https://randomuser.me/api/portraits/women/32.jpg",
            "total_sales": 7,
            "avg_days_on_market": 35,
            "median_sold_price": "$950k",
            "featured": False
        },
        {
            "id": "agent7",
            "name": "Michael Chen",
            "agency": "Stone",
            "photo": "https://randomuser.me/api/portraits/men/76.jpg",
            "total_sales": 9,
            "avg_days_on_market": 22,
            "median_sold_price": "$1.05m",
            "featured": False
        },
        {
            "id": "agent8",
            "name": "Rebecca Taylor",
            "agency": "Cunninghams",
            "photo": "https://randomuser.me/api/portraits/women/45.jpg",
            "total_sales": 5,
            "avg_days_on_market": 18,
            "median_sold_price": "$880k",
            "featured": False
        },
        {
            "id": "agent9",
            "name": "David Wilson",
            "agency": "Whitehouse",
            "photo": "https://randomuser.me/api/portraits/men/62.jpg",
            "total_sales": 6,
            "avg_days_on_market": 25,
            "median_sold_price": "$920k",
            "featured": False
        },
        {
            "id": "agent10",
            "name": "Emma Johnson",
            "agency": "McGrath",
            "photo": "https://randomuser.me/api/portraits/women/22.jpg",
            "total_sales": 8,
            "avg_days_on_market": 30,
            "median_sold_price": "$975k",
            "featured": False
        }
    ]
    
    # Choose property and agents based on suburb
    if suburb == "Brandy Hill":
        property_details = {
            "id": property_id,
            "address": "45 River View Road, Brandy Hill NSW 2324",
            "price": "$950,000",
            "bedrooms": 4,
            "bathrooms": 2,
            "parking": 2,
            "propertyType": "House",
            "landSize": "800 sqm",
            "description": "Spacious family home with river views in a peaceful rural setting...",
            "features": [
                "River Views", 
                "Double Garage", 
                "Outdoor Entertainment Area",
                "Solar Panels",
                "Large Garden"
            ],
            "images": [
                "https://picsum.photos/800/600?random=1",
                "https://picsum.photos/800/600?random=2",
            ],
            "suburb": "Brandy Hill"
        }
        top_agents = brandy_hill_agents
    else:
        # Default to Queenscliff
        property_details = {
            "id": property_id,
            "address": "123 Sample Street, Queenscliff NSW 2096",
            "price": "$1,200,000",
            "bedrooms": 1,
            "bathrooms": 1,
            "parking": 1,
            "propertyType": "House",
            "landSize": "450 sqm",
            "description": "Beautiful family home in a prime location...",
            "features": [
                "Air Conditioning", 
                "Built-in Wardrobes", 
                "Close to Schools",
                "Close to Shops",
                "Garden"
            ],
            "images": [
                "https://picsum.photos/800/600",
                "https://picsum.photos/800/600",
            ],
            "suburb": "Queenscliff"
        }
        top_agents = queenscliff_agents
    
    result = {
        "property": property_details,
        "agent": {
            "id": agent_id or "12345",
            "name": "Jane Smith",
            "phone": "0400 123 456",
            "email": "jane.smith@example.com",
            "agency": "Premier Real Estate",
            "photo": "https://randomuser.me/api/portraits/women/44.jpg",
            "bio": "Jane has over 10 years of experience in the Sydney property market...",
        },
        "top_agents": top_agents
    }
    
    # Add job_id to the result if provided
    if job_id:
        result["job_id"] = job_id
    
    return result

async def get_listing_details(listing_id):
    """
    Retrieve details for a specific listing using Domain.com.au API
    """
    if not DOMAIN_API_KEY:
        logger.error("Domain API key not found. Please set DOMAIN_API_KEY environment variable.")
        return None
    
    logger.info(f"Retrieving details for listing ID: {listing_id}")
    
    # API endpoint
    url = f"https://api.domain.com.au/v1/listings/{listing_id}"
    
    # Headers with API key
    headers = {
        "X-Api-Key": DOMAIN_API_KEY,
        "Content-Type": "application/json"
    }
    
    try:
        # Make the API request
        response = requests.get(url, headers=headers)
        
        # Check if the request was successful
        if response.status_code == 200:
            listing_details = response.json()
            logger.info(f"Successfully retrieved details for listing ID: {listing_id}")
            return listing_details
        else:
            logger.error(f"API request failed with status code {response.status_code}: {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error retrieving listing details: {str(e)}")
        return None
async def get_agency_details(agency_id):
    """
    Retrieve details for a specific agency using Domain.com.au API
    """
    if not DOMAIN_API_KEY:
        logger.error("Domain API key not found. Please set DOMAIN_API_KEY environment variable.")
        return None
    
    logger.info(f"Retrieving details for agency ID: {agency_id}")
    
    # API endpoint
    url = f"https://api.domain.com.au/v1/agencies/{agency_id}"
    
    # Headers with API key
    headers = {
        "X-Api-Key": DOMAIN_API_KEY,
        "Content-Type": "application/json"
    }
    
    try:
        # Make the API request
        response = requests.get(url, headers=headers)
        
        # Check if the request was successful
        if response.status_code == 200:
            agency_details = response.json()
            logger.info(f"Successfully retrieved details for agency ID: {agency_id}")
            return agency_details
        else:
            logger.error(f"API request failed with status code {response.status_code}: {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error retrieving agency details: {str(e)}")
        return None


async def check_featured_agent(suburb, state):
    """
    Check for featured agents in a suburb by calling the Make.com webhook
    
    Args:
        suburb: The suburb to check for
        state: The state to check for
        
    Returns:
        List of featured agents for the suburb or None if no agents found
    """
    webhook_url = "https://hook.eu2.make.com/nuedlxjy6fsn398sa31tfh1ca6sgycda"
    
    try:
        # Prepare the data to send to the webhook
        data = {
            "suburb": suburb,
            "state": state
        }
        
        # Make the POST request to the webhook
        response = requests.post(webhook_url, json=data)
        
        # Check if the request was successful
        if response.status_code == 200:
            # Parse the response JSON
            result = response.json()
            
            # Check if we have valid agents data
            if isinstance(result, list) and len(result) > 0:
                # Check if we have an empty agent record (no agents for this suburb)
                first_agent = result[0]
                if not first_agent.get("Name") or first_agent.get("Name").strip() == "":
                    logger.info(f"No featured agents found for {suburb}, {state}")
                    return None
                
                logger.info(f"Found {len(result)} featured agents for {suburb}, {state}")
                return result
            else:
                logger.warning(f"Unexpected response format from featured agent webhook: {result}")
                return None
        else:
            logger.error(f"Failed to check featured agents: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error checking featured agents: {e}")
        return None

async def get_agent_details(agent_name, agency_name=None):
    """
    Get agent details including photo, agency name, and agency logo
    
    Args:
        agent_name: The name of the agent
        agency_name: The name of the agency (optional)
        
    Returns:
        Dictionary with agent photo, agency name, and agency logo
    """
    # Special case for Dan Tape
    if agent_name.lower() == "dan tape":
        return {
            "agent_photo": "https://www.dropbox.com/scl/fi/87s4eusr4a2e7jeqzozwi/Ethico-38.jpg?rlkey=vevzh8xp66zj86ajn2ob7q7aw&st=i2yfzgb1&dl=1",
            "agency_name": "Ethico Estate",
            "agency_logo": "https://www.dropbox.com/scl/fi/4ryjamzs6yy2rdlwndkxs/Burlap-BG.png?rlkey=9wqlf10g8kqat7u98y9kbyxd0&st=24d0lj3x&dl=1"
        }
    
    if not DOMAIN_API_KEY:
        logger.error("Domain API key not found. Please set DOMAIN_API_KEY environment variable.")
        return None
    
    logger.info(f"Searching for agent: {agent_name}")
    
    # Step 1: Search for the agent
    agent_search_url = "https://api.domain.com.au/v1/agents/search"
    headers = {
        "X-Api-Key": DOMAIN_API_KEY,
        "Content-Type": "application/json"
    }
    
    params = {
        "query": agent_name
    }
    
    try:
        # Make the API request to search for agents
        response = requests.get(agent_search_url, headers=headers, params=params)
        
        # Check if the request was successful
        if response.status_code == 200:
            agents = response.json()
            
            # If no agents found, return None
            if not agents:
                logger.warning(f"No agents found for name: {agent_name}")
                return None
            
            # If only one agent found, use that one
            if len(agents) == 1:
                agent = agents[0]
                agent_id = agent.get("agentId")
                agent_photo = agent.get("thumbnail")
                found_agency_name = agent.get("agencyName")
            else:
                # Multiple agents found, try to match by agency name if provided
                found_agent = None
                if agency_name:
                    for agent in agents:
                        if agent.get("agencyName", "").lower() == agency_name.lower():
                            found_agent = agent
                            break
                
                # If no match by agency name or no agency name provided, use the first agent
                if not found_agent:
                    found_agent = agents[0]
                
                agent_id = found_agent.get("agentId")
                agent_photo = found_agent.get("thumbnail")
                found_agency_name = found_agent.get("agencyName")
            
            # Step 2: Get agency details
            agency_search_url = "https://api.domain.com.au/v1/agencies/"
            agency_params = {
                "q": found_agency_name
            }
            
            # Make the API request to search for the agency
            agency_response = requests.get(agency_search_url, headers=headers, params=agency_params)
            
            if agency_response.status_code == 200:
                agencies = agency_response.json()
                
                if agencies:
                    agency_id = agencies[0].get("id")
                    
                    # Step 3: Get agency logo
                    agency_details_url = f"https://api.domain.com.au/v1/agencies/{agency_id}"
                    agency_details_response = requests.get(agency_details_url, headers=headers)
                    
                    if agency_details_response.status_code == 200:
                        agency_details = agency_details_response.json()
                        agency_logo = agency_details.get("profile", {}).get("agencyLogoStandard")
                    else:
                        logger.error(f"Failed to get agency details: {agency_details_response.status_code}")
                        agency_logo = None
                else:
                    logger.warning(f"No agencies found for name: {found_agency_name}")
                    agency_logo = None
            else:
                logger.error(f"Failed to search for agency: {agency_response.status_code}")
                agency_logo = None
            
            # Return the agent details
            return {
                "agent_id": agent_id,
                "agent_photo": agent_photo,
                "agency_name": found_agency_name,
                "agency_logo": agency_logo
            }
        else:
            logger.error(f"Failed to search for agent: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error getting agent details: {str(e)}")
        return None