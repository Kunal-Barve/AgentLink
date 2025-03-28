import os
import requests
from dotenv import load_dotenv
import logging
import asyncio
import json

load_dotenv()

# Domain.com.au API credentials
DOMAIN_API_KEY = os.getenv("DOMAIN_API_KEY")
DOMAIN_API_SECRET = os.getenv("DOMAIN_API_SECRET")

# Set up logging with more detailed configuration
logger = logging.getLogger("articflow.domain")

# Configure basic logging for both standalone testing and when imported
if not logger.handlers:
    # Create a file handler
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    from datetime import datetime
    log_filename = os.path.join(log_dir, f"ArticFlow_Domain_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log")
    
    file_handler = logging.FileHandler(log_filename)
    file_handler.setLevel(logging.DEBUG)
    
    # Create a console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Create a formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add the handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # Set the logger level to the lowest level of any handler
    logger.setLevel(logging.DEBUG)
    
    logger.info("Domain service logger initialized")

# Configure additional logging for standalone testing
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger.info("Running domain_service.py as main script")

async def fetch_property_data(
    property_id, 
    agent_id=None, 
    featured_agent_id=None, 
    job_id=None, 
    suburb="Queenscliff", 
    state="NSW", 
    property_types=None,
    min_bedrooms=1,
    max_bedrooms=None,
    min_bathrooms=1,
    max_bathrooms=None,
    min_carspaces=1,
    max_carspaces=None,
    include_surrounding_suburbs=False,
    post_code=None,
    region=None,
    area=None,
    min_land_area: int = None,  # Added parameter
    max_land_area: int = None 
):
    """
    Fetch property data from Domain.com.au API
    
    Args:
        property_id: The ID of the property to fetch
        agent_id: The ID of the agent to fetch
        featured_agent_id: The ID of the featured agent
        job_id: The ID of the job
        suburb: The suburb to search in
        state: The state to search in
        property_types: List of property types to filter by
        min_bedrooms: Minimum number of bedrooms
        max_bedrooms: Maximum number of bedrooms
        min_bathrooms: Minimum number of bathrooms
        max_bathrooms: Maximum number of bathrooms
        min_carspaces: Minimum number of car spaces
        max_carspaces: Maximum number of car spaces
        include_surrounding_suburbs: Whether to include surrounding suburbs
        post_code: The post code to filter by
        region: The region to filter by
        area: The area to filter by
        
    Returns:
        Dictionary with property data
    """
    logger.info(f"Fetching top agents for suburb={suburb}, state={state}")
    
    # Get top agents for the suburb
    logger.info(f"Getting top agents for {suburb}, {state}")
    agencies_data = await get_agent_performance_metrics(
        suburb, 
        state, 
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
    
    
    # Convert the nested dictionary structure to a flat list of agents for display
    agents_list = []
    for agency_id, agency_data in agencies_data.items():
        agency_name = agency_data['name']
        agency_logo = agency_data.get('logo', 'N/A')
        
        for agent_id, agent_data in agency_data['agents'].items():
            if agent_data['total_sales'] > 0:  # Only include agents with sales
                # Add agency info to the agent data
                agent_data['agency'] = agency_name
                agent_data['agency_logo'] = agency_logo
                agents_list.append(agent_data)
    
    # Handle duplicate agents - keep only the record with the most complete data
        # Handle duplicate agents - keep only the record with the most complete data
        # Create a dictionary to track unique agents by name and agency
    print("\n===== AGENT DEDUPLICATION PROCESS =====")
    print(f"Total agents before deduplication: {len(agents_list)}")
    unique_agents = {}
    
    # First pass: Group agents by name only to identify potential duplicates across branches
    agents_by_name = {}
    for agent in agents_list:
        agent_name = agent['name'].strip().lower()
        if agent_name not in agents_by_name:
            agents_by_name[agent_name] = []
        agents_by_name[agent_name].append(agent)
    
    # Second pass: Process each agent name group
    for agent_name, agent_group in agents_by_name.items():
        print(f"\nProcessing agent group: {agent_name} ({len(agent_group)} occurrences)")
        
        # If only one occurrence, add directly
        if len(agent_group) == 1:
            agent = agent_group[0]
            agency_name = agent['agency'].strip().lower()
            agent_key = f"{agent_name}_{agency_name}"
            print(f"  Single occurrence - Adding agent: {agent['name']} from {agent['agency']}")
            print(f"  Agent key: '{agent_key}'")
            unique_agents[agent_key] = agent
            continue
        
        # Improved agency name normalization to handle different office formats
        # Extract the main agency name by removing location identifiers
        normalized_agencies = {}
        for a in agent_group:
            agency_full = a['agency'].strip().lower()
            
            # Handle hyphenated format: "Agency Name - Location"
            if ' - ' in agency_full:
                main_agency = agency_full.split(' - ')[0]
            else:
                # Handle space-separated format: "Agency Name Location"
                # Try to identify common agency names
                parts = agency_full.split()
                if len(parts) > 1:
                    # For agencies like "Belle Property Dee Why", extract "Belle Property"
                    # Common real estate franchise patterns
                    common_franchises = ["belle property", "ray white", "lj hooker", "century 21", 
                                        "mcgrath", "raine & horne", "first national", "harcourts"]
                    
                    # Check if any common franchise name is in the agency name
                    found_franchise = False
                    for franchise in common_franchises:
                        if franchise in agency_full:
                            main_agency = franchise
                            found_franchise = True
                            break
                    
                    # If no known franchise, use first two words as the main agency name
                    if not found_franchise:
                        main_agency = " ".join(parts[:2])
                else:
                    main_agency = agency_full
            
            # Store the normalized agency name
            if main_agency not in normalized_agencies:
                normalized_agencies[main_agency] = []
            normalized_agencies[main_agency].append(a)
            
            print(f"  Normalized '{agency_full}' to '{main_agency}'")
        
        # Process each normalized agency group
        for main_agency, agency_agents in normalized_agencies.items():
            if len(agency_agents) == 1:
                # Only one occurrence for this normalized agency
                agent = agency_agents[0]
                agency_name = agent['agency'].strip().lower()
                agent_key = f"{agent_name}_{main_agency}"
                print(f"  Adding agent: {agent['name']} from {agent['agency']} (normalized to {main_agency})")
                print(f"  Agent key: '{agent_key}'")
                unique_agents[agent_key] = agent
            else:
                # Multiple occurrences for the same agent at the same normalized agency
                print(f"  Same agent across different branches of {main_agency}")
                
                # Merge the data from all branches
                merged_agent = agency_agents[0].copy()  # Start with the first occurrence
                merged_agent['branches'] = []  # Track all branches
                
                # Sum up the sales and values
                total_sales = 0
                joint_sales = 0
                total_value = 0
                joint_sales_value = 0
                all_properties = {}
                
                for branch_agent in agency_agents:
                    branch_name = branch_agent['agency']
                    merged_agent['branches'].append(branch_name)
                    
                    # Add sales counts
                    total_sales += branch_agent.get('total_sales', 0)
                    joint_sales += branch_agent.get('joint_sales', 0)
                    total_value += branch_agent.get('total_value', 0)
                    joint_sales_value += branch_agent.get('joint_sales_value', 0)
                    
                    # Merge properties
                    for prop_id, prop_data in branch_agent.get('properties', {}).items():
                        all_properties[prop_id] = prop_data
                    
                    print(f"  Merged branch: {branch_name} - Sales: {branch_agent.get('total_sales', 0)}")
                
                # Update the merged agent with combined data
                merged_agent['total_sales'] = total_sales
                merged_agent['joint_sales'] = joint_sales
                merged_agent['total_value'] = total_value
                merged_agent['joint_sales_value'] = joint_sales_value
                merged_agent['properties'] = all_properties
                merged_agent['agency'] = f"{main_agency}"  # Use the normalized agency name
                
                # Use the main agency name for the key
                agent_key = f"{agent_name}_{main_agency}"
                print(f"  Created merged agent with key: '{agent_key}'")
                print(f"  Total sales after merge: {total_sales}")
                unique_agents[agent_key] = merged_agent
    
    # Print summary of unique agents
    print("\n===== DEDUPLICATION SUMMARY =====")
    print(f"Reduced {len(agents_list)} agents to {len(unique_agents)} unique agents")
    print("Unique agent keys:")
    for key in unique_agents.keys():
        print(f"  - '{key}'")
    
    # Convert back to a list
    agents_list = list(unique_agents.values())
    # Create a cache for featured agent status to avoid duplicate API calls
    featured_status_cache = {}
    # Check if each agent is a featured agent using the webhook
    for agent in agents_list:
        agent_name = agent['name']
        # Check if we already have the featured status for this agent in the cache
        if agent_name in featured_status_cache:
            agent['featured'] = featured_status_cache[agent_name]
            logger.info(f"Using cached featured status for {agent_name}: {agent['featured']}")
        else:
            # If not in cache, make the API call
            is_featured = await check_featured_agent(agent_name, suburb, state)
            agent['featured'] = is_featured
            # Store in cache for future use
            featured_status_cache[agent_name] = is_featured
    
    
    # Separate featured and non-featured agents
    featured_agents = [agent for agent in agents_list if agent['featured']]
    non_featured_agents = [agent for agent in agents_list if not agent['featured']]
    
    # Sort non-featured agents by total sales (descending)
    non_featured_agents.sort(key=lambda x: x['total_sales'], reverse=True)
    
    # Combine featured agents first, then non-featured agents
    # If we have featured agents, they go first, then we add non-featured agents to make up to 5 total
    # If no featured agents, we just take the top 5 non-featured agents
    if featured_agents:
        logger.info(f"Found {len(featured_agents)} featured agents in {suburb}")
        # Calculate how many non-featured agents we need to make up to 5 total
        num_non_featured_needed = 5 - len(featured_agents)
        top_agents = featured_agents + non_featured_agents[:num_non_featured_needed]
    else:
        logger.info(f"No featured agents found in {suburb}")
        # Get top 5 agents or all if less than 5
        top_agents = non_featured_agents[:5] if len(non_featured_agents) > 5 else non_featured_agents
    
    # Format the top agents data for the PDF
    formatted_top_agents = []
    for agent in top_agents:
        # Use the combined total value (primary + joint sales)
        total_value = agent.get('total_sales_value_combined', 0)
        # Determine if we should show the total value or "Not disclosed"
        # Only show "Not disclosed" if ALL properties have no price
        valid_prices = [p["sold_price"] for p in agent["properties"].values() 
                       if p["sold_price"] is not None]
        
        if valid_prices:  # If we have at least one property with price
            formatted_total = format_price(total_value)
        else:  # If none of the properties have price data
            formatted_total = "Not disclosed"
            
        # Ensure agent name has first letter capitalized
        agent_name = agent['name']
        if agent_name:
            # Split the name by spaces and capitalize each part
            name_parts = agent_name.split()
            capitalized_name = ' '.join(word.capitalize() for word in name_parts)
        else:
            capitalized_name = agent_name
            
        formatted_agent = {
            "name": capitalized_name,  # Use the capitalized name
            "agency": agent['agency'],
            "photo_url": agent.get('photo', 'N/A'),
            "agency_logo_url": agent.get('agency_logo', 'N/A'),
            "total_sales": agent['total_sales'],  # Primary sales count
            "joint_sales": agent.get('joint_sales', 0),  # Include joint sales count
            "median_sold_price": agent['median_sold_price'],
            "total_sales_value": formatted_total,  # This now includes both primary and joint sales
            "joint_sales_value": agent.get('joint_sales_value_formatted', "$0"),  # Include joint sales value
            "featured": agent.get('featured', False)
        }
        formatted_top_agents.append(formatted_agent)
    
    result = {
        "top_agents": formatted_top_agents,
        "suburb": suburb
    }
    
    # Add job_id to the result if provided
    if job_id:
        result["job_id"] = job_id
    
    return result

async def check_featured_agent(agent_name, suburb, state):
    """
    Check if an agent is a featured agent by calling the Make.com webhook
    
    Args:
        agent_name: The name of the agent to check
        suburb: The suburb to check for
        state: The state to check for
        
    Returns:
        Boolean indicating if the agent is featured
    """
    webhook_url = "https://hook.eu2.make.com/nuedlxjy6fsn398sa31tfh1ca6sgycda"
    
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
            # Parse the response JSON
            result = response.json()
            
            # Handle different response formats
            if isinstance(result, bool):
                # If the result is already a boolean, use it directly
                is_featured = result
            elif isinstance(result, dict):
                # If the result is a dictionary, extract the featured status
                is_featured = result.get('featured', False)
            else:
                # For any other type, convert to boolean
                is_featured = bool(result)
            
            logger.info(f"Agent {agent_name} in {suburb} featured status: {is_featured}")
            return is_featured
        else:
            logger.error(f"Failed to check featured agent status: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error checking featured agent status: {e}")
        return False

# Keep the existing get_mock_property_data function as is
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

async def search_sold_listings_by_suburb(
    suburb, 
    state="NSW", 
    property_types=None, 
    min_bedrooms=1, 
    max_bedrooms=None,
    min_bathrooms=1, 
    max_bathrooms=None,
    min_carspaces=1,
    max_carspaces=None,
    include_surrounding_suburbs=False,
    post_code=None,
    region=None,
    area=None,
    min_land_area=None,
    max_land_area=None
):
    """
    Search for sold listings in a specific suburb using Domain.com.au API
    
    Args:
        suburb: The suburb to search in
        state: The state to search in
        property_types: List of property types to filter by
        min_bedrooms: Minimum number of bedrooms
        max_bedrooms: Maximum number of bedrooms
        min_bathrooms: Minimum number of bathrooms
        max_bathrooms: Maximum number of bathrooms
        min_carspaces: Minimum number of car spaces
        max_carspaces: Maximum number of car spaces
        include_surrounding_suburbs: Whether to include surrounding suburbs
        post_code: The post code to filter by
        region: The region to filter by
        area: The area to filter by
        min_land_area: Minimum land area in square meters
        max_land_area: Maximum land area in square meters
        
    Returns:
        List of listings matching the criteria
    """
    if not DOMAIN_API_KEY:
        logger.error("Domain API key not found. Please set DOMAIN_API_KEY environment variable.")
        return None
    
    logger.info(f"Searching for sold listings in {suburb}, {state}")
    
    # Store user's requested property types for post-filtering
    user_requested_property_types = property_types
    
    # Always use all property types in the API request
    all_property_types = ["AcreageSemiRural", "ApartmentUnitFlat", "Aquaculture", "BlockOfUnits", "CarSpace", "DairyFarming", "DevelopmentSite", "Duplex", "Farm", "FishingForestry", "NewHomeDesigns", "House", "NewHouseLand", "IrrigationServices", "NewLand", "Livestock", "NewApartments", "Penthouse", "RetirementVillage", "Rural", "SemiDetached", "SpecialistFarm", "Studio", "Terrace", "Townhouse", "VacantLand", "Villa", "Cropping", "Viticulture", "MixedFarming", "Grazing", "Horticulture", "Equine", "Farmlet", "Orchard", "RuralLifestyle"
]
    
    # Calculate one year ago date in ISO 8601 format
    from datetime import datetime, timedelta
    one_year_ago = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%dT00:00:00Z")
    
    # Prepare the search request payload
    payload = {
        "listingType": "Sold",
        "propertyTypes": all_property_types,  # Always request all property types
        "locations": [
            {
                "state": state,
                "suburb": suburb,
                "includeSurroundingSuburbs": include_surrounding_suburbs
            }
        ],
        "minBedrooms": min_bedrooms,
        "minBathrooms": min_bathrooms,
        "minCarspaces": min_carspaces,
        "listedSince": one_year_ago,
        "pageSize": 100
    }
    # Add optional parameters if provided
    if max_bedrooms is not None:
        payload["maxBedrooms"] = max_bedrooms
    if max_bathrooms is not None:
        payload["maxBathrooms"] = max_bathrooms
    if max_carspaces is not None:
        payload["maxCarspaces"] = max_carspaces
    if post_code:
        payload["locations"][0]["postCode"] = post_code
    if region:
        payload["locations"][0]["region"] = region
    if area:
        payload["locations"][0]["area"] = area
    
    # Add land area parameters if provided
    if min_land_area is not None:
        payload["minLandArea"] = min_land_area
    if max_land_area is not None:
        payload["maxLandArea"] = max_land_area
    
    # API endpoint
    url = "https://api.domain.com.au/v1/listings/residential/_search"
    
    # Headers with API key
    headers = {
        "X-Api-Key": DOMAIN_API_KEY,
        "Content-Type": "application/json"
    }
    
    try:
        # Make the API request
        response = requests.post(url, headers=headers, json=payload)
        
        # Check if the request was successful
        if response.status_code == 200:
            listings = response.json()
            logger.info(f"Found {len(listings)} sold listings in {suburb}")
            
            # Filter listings by user's requested property types if specified
            if user_requested_property_types:
                filtered_listings = []
                for listing in listings:
                    if ("listing" in listing and 
                        "propertyDetails" in listing["listing"] and 
                        "propertyType" in listing["listing"]["propertyDetails"]):
                        
                        property_type = listing["listing"]["propertyDetails"]["propertyType"]
                        if property_type in user_requested_property_types:
                            filtered_listings.append(listing)
                
                logger.info(f"Filtered to {len(filtered_listings)} listings matching requested property types")
                return filtered_listings
            
            # Return all listings if no property type filter was specified
            print("Returning All Listings /n *************")
            return listings
        else:
            logger.error(f"API request failed with status code {response.status_code}: {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error searching for listings: {str(e)}")
        return None

async def process_agent_sales_data(suburb, state="NSW"):
    """
    Process sold listings data to create a nested dictionary of agencies, agents, and their sales
    
    Returns:
        Dictionary with agencies, their agents, and sales data
    """
    logger.info(f"Processing agent sales data for {suburb}, {state}")
    
    # Step 1: Get sold listings for the suburb
    listings = await search_sold_listings_by_suburb(suburb, state)
    if not listings:
        logger.error(f"No sold listings found for {suburb}")
        return {}
    
    logger.info(f"Found {len(listings)} sold listings to process")
    
    # Step 2: Create the nested dictionary structure
    result = {}
    
    for listing in listings:
        # Skip if listing doesn't have the required structure
        if not all(key in listing for key in ["type", "listing"]):
            continue
        
        listing_data = listing["listing"]
        
        # Skip if advertiser info is missing
        if "advertiser" not in listing_data:
            continue
        
        advertiser = listing_data["advertiser"]
        
        # Skip if not an agency or missing required fields
        if advertiser.get("type") != "Agency" or "id" not in advertiser or "name" not in advertiser:
            continue
        
        agency_id = advertiser["id"]
        agency_name = advertiser["name"]
        agency_logo = advertiser.get("logoUrl", "")
        
        # Initialize agency in result if not already present
        if agency_id not in result:
            result[agency_id] = {
                "name": agency_name,
                "logoUrl": agency_logo,
                "agents": {}
            }
        
        # Process agents for this listing
        if "contacts" not in advertiser or not advertiser["contacts"]:
            continue
        
        # Get sold price if available
        sold_price = None
        if "soldData" in listing_data and "soldPrice" in listing_data["soldData"]:
            sold_price = listing_data["soldData"]["soldPrice"]
        
        listing_id = listing_data.get("id", "unknown")
        
        # Process each agent in the listing
        for contact in advertiser["contacts"]:
            if "name" not in contact:
                continue
            
            agent_name = contact["name"]
            agent_photo = contact.get("photoUrl", "")
            
            # Initialize agent in result if not already present
            if agent_name not in result[agency_id]["agents"]:
                result[agency_id]["agents"][agent_name] = {
                    "name": agent_name,
                    "photoUrl": agent_photo,
                    "propertiesSold": 0,
                    "properties": {}
                }
            
            # Update agent's sales data
            agent = result[agency_id]["agents"][agent_name]
            
            # Only count this listing if we have a sold price
            if sold_price is not None:
                agent["propertiesSold"] += 1
                agent["properties"][str(listing_id)] = sold_price
    
    # Log summary of processed data
    total_agencies = len(result)
    total_agents = sum(len(agency_data["agents"]) for agency_data in result.values())
    total_properties = sum(
        sum(agent["propertiesSold"] for agent in agency_data["agents"].values())
        for agency_data in result.values()
    )
    
    logger.info(f"Processed data summary: {total_agencies} agencies, {total_agents} agents, {total_properties} properties")
    
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

async def get_agent_performance_metrics(
    suburb, 
    state="NSW", 
    months=12, 
    property_types=None,
    min_bedrooms=1,
    max_bedrooms=None,
    min_bathrooms=1,
    max_bathrooms=None,
    min_carspaces=1,
    max_carspaces=None,
    include_surrounding_suburbs=False,
    post_code=None,
    region=None,
    area=None,
    min_land_area=None,
    max_land_area=None
):
    """
    Calculate performance metrics for agents in a specific suburb
    
    Args:
        suburb: The suburb to analyze
        state: The state (default: NSW)
        months: Number of months to look back (default: 12)
        property_types: Optional list of property types to filter by
        min_bedrooms: Minimum number of bedrooms
        max_bedrooms: Maximum number of bedrooms
        min_bathrooms: Minimum number of bathrooms
        max_bathrooms: Maximum number of bathrooms
        min_carspaces: Minimum number of car spaces
        max_carspaces: Maximum number of car spaces
        include_surrounding_suburbs: Whether to include surrounding suburbs
        post_code: The post code to filter by
        region: The region to filter by
        area: The area to filter by
        
    Returns:
        Dictionary of agencies with their agents and performance metrics
    """
    logger.info(f"Calculating agent performance metrics for {suburb}, {state}")
    
    # Step 1: Search for sold listings in the suburb
    print(f"\nStep 1: Searching for sold listings in {suburb}...")
    logger.info(f"Step 1: Searching for sold listings in {suburb}...")
    listings = await search_sold_listings_by_suburb(
        suburb, 
        state, 
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
    )
    if not listings:
        logger.error(f"No listings found for {suburb}")
        print(f"No listings found for {suburb}")
        return {}
    
    print(f"Found {len(listings)} listings in {suburb}")
    logger.info(f"Found {len(listings)} listings in {suburb}")
    
    # Step 2: Extract agency IDs from the listings and get agency details
    print(f"\nStep 2: Extracting agency IDs from listings and getting agency details...")
    logger.info(f"Step 2: Extracting agency IDs from listings and getting agency details...")
    agencies_data = {}  # Main dictionary to store all data
    
    for listing in listings:
        if "listing" in listing and "advertiser" in listing["listing"] and "id" in listing["listing"]["advertiser"]:
            agency_id = listing["listing"]["advertiser"]["id"]
            
            # Skip if we already processed this agency
            if agency_id in agencies_data:
                continue
                
            # Get agency details
            print(f"Getting details for agency ID: {agency_id}")
            logger.info(f"Getting details for agency ID: {agency_id}")
            agency_details = await get_agency_details(agency_id)
            
            if not agency_details:
                print(f"Failed to retrieve details for agency ID: {agency_id}")
                logger.warning(f"Failed to retrieve details for agency ID: {agency_id}")
                # Initialize with minimal info
                agencies_data[agency_id] = {
                    "id": agency_id,
                    "name": f"Agency {agency_id}",
                    "logo": listing["listing"]["advertiser"].get("logoUrl") if "listing" in listing and "advertiser" in listing["listing"] else None,
                    "agents": {}
                }
            else:
                # Store agency details
                agencies_data[agency_id] = {
                    "id": agency_id,
                    "name": agency_details.get("name", f"Agency {agency_id}"),
                    "logo": agency_details.get("logo") or (listing["listing"]["advertiser"].get("logoUrl") if "listing" in listing and "advertiser" in listing["listing"] else None),
                    "agents": {}
                }
                print(f"Added agency: {agencies_data[agency_id]['name']}")
                logger.info(f"Added agency: {agencies_data[agency_id]['name']}")
    
    print(f"Found {len(agencies_data)} unique agencies in {suburb}")
    logger.info(f"Found {len(agencies_data)} unique agencies in {suburb}")
    
    # Modified: Skip agency listings retrieval and directly extract agent info from the sold listings
    print(f"\nStep 3: Extracting agent information directly from sold listings...")
    logger.info(f"Step 3: Extracting agent information directly from sold listings...")
    
    # Process each listing to extract agent information
    for listing in listings:
        if "listing" not in listing or "advertiser" not in listing["listing"]:
            continue
            
        advertiser = listing["listing"]["advertiser"]
        agency_id = advertiser.get("id")
        
        # Skip if agency not found in our data
        if agency_id not in agencies_data:
            continue
            
        # Extract agent information from contacts
        if "contacts" in advertiser:
            # Get listing ID and sold price
            listing_id = listing["listing"].get("id")
            
            # Extract sold price and date from soldData instead of soldDetails
            sold_price = None
            sold_date = None
            if "soldData" in listing["listing"]:
                sold_price = listing["listing"]["soldData"].get("soldPrice")
                sold_date = listing["listing"]["soldData"].get("soldDate")
            
            # Process each contact/agent based on their position in the contacts list
            for index, contact in enumerate(advertiser["contacts"]):
                if "name" not in contact or not contact["name"] or contact["name"].strip() == "":
                    logger.info(f"Skipping contact with missing or empty name for listing ID: {listing_id}")
                    continue
                    
                agent_name = contact["name"]
                agent_photo = contact.get("photoUrl", "")
                
                # Use name as ID since we don't have actual agent IDs
                agent_id = agent_name
                
                # Initialize agent in result if not already present
                if agent_id not in agencies_data[agency_id]["agents"]:
                    agencies_data[agency_id]["agents"][agent_id] = {
                        "id": agent_id,
                        "name": agent_name,
                        "photo": agent_photo,
                        "properties": {},  # Changed from sales[] to properties dict
                        "total_sales": 0,  # Primary sales (agent is first in contacts)
                        "joint_sales": 0,  # New field for joint sales (agent is not first)
                        "total_value": 0,  # Value of primary sales
                        "joint_sales_value": 0,  # Value of joint sales
                    }
                
                # Store property data if we have a listing ID
                if listing_id:
                    agencies_data[agency_id]["agents"][agent_id]["properties"][listing_id] = {
                        "sold_price": sold_price,
                        "sold_date": sold_date,
                        "is_primary": index == 0  # Track if this was a primary or joint sale
                    }
                    
                    # Update sales counts and values based on agent position
                    if index == 0:  # Primary agent (first in contacts list)
                        agencies_data[agency_id]["agents"][agent_id]["total_sales"] += 1
                        if sold_price:
                            agencies_data[agency_id]["agents"][agent_id]["total_value"] += sold_price
                    else:  # Joint agent (not first in contacts list)
                        agencies_data[agency_id]["agents"][agent_id]["joint_sales"] += 1
                        if sold_price:
                            agencies_data[agency_id]["agents"][agent_id]["joint_sales_value"] += sold_price
    
        # Step 4: Calculate final metrics for each agent
    print(f"\nStep 4: Calculating final metrics for each agent...")
    
    # Process each agent to calculate metrics and handle edge cases properly
    for agency_id, agency_data in agencies_data.items():
        for agent_id, agent_data in list(agency_data["agents"].items()):
            # Skip agents with no sales at all
            if agent_data["total_sales"] == 0 and agent_data["joint_sales"] == 0:
                print(f"Skipping agent {agent_data['name']} ({agent_id}) - no sales at all")
                continue
                
            # Get all valid prices from both primary and joint sales
            valid_prices = [p["sold_price"] for p in agent_data["properties"].values() 
                           if p["sold_price"] is not None]
            
            # Calculate median sold price (include both primary and joint sales with prices)
            median_sold_price = 0
            if valid_prices:
                sorted_prices = sorted(valid_prices)
                mid = len(sorted_prices) // 2
                if len(sorted_prices) % 2 == 0 and len(sorted_prices) > 0:
                    median_sold_price = (sorted_prices[mid-1] + sorted_prices[mid]) / 2
                elif len(sorted_prices) > 0:
                    median_sold_price = sorted_prices[mid]
            
            # Format the metrics based on whether we have any price data
            if valid_prices:  # If we have at least one property with price
                formatted_median_price = format_price(median_sold_price)
            else:  # If none of the properties have price data
                formatted_median_price = "Not disclosed"
            
            # Calculate combined sales value (primary + joint)
            total_sales_value = agent_data.get("total_value", 0) + agent_data.get("joint_sales_value", 0)
            
            # Format joint sales value
            joint_sales_value = agent_data.get("joint_sales_value", 0)
            if joint_sales_value > 0:
                formatted_joint_value = format_price(joint_sales_value)
            else:
                formatted_joint_value = "$0"
            
            # Update agent data with calculated metrics
            agent_data["median_sold_price"] = formatted_median_price
            agent_data["median_sold_price_value"] = median_sold_price
            agent_data["joint_sales_value_formatted"] = formatted_joint_value
            agent_data["total_sales_value_combined"] = total_sales_value
            
            # Count total properties (both with and without prices)
            total_properties = len(agent_data["properties"])
            properties_with_prices = len(valid_prices)
            
            # Log the breakdown for debugging
            print(f"Agent {agent_data['name']} metrics:")
            print(f"  Total Properties: {total_properties}")
            print(f"  Properties with prices: {properties_with_prices}")
            print(f"  Properties without prices: {total_properties - properties_with_prices}")
            print(f"  Primary Sales: {agent_data['total_sales']}")
            print(f"  Joint Sales: {agent_data['joint_sales']}")
            print(f"  Median Sold Price (All Sales): {agent_data['median_sold_price']}")
            
            # Format values with M/K suffixes for better readability
            primary_value = agent_data['total_value']
            joint_value = agent_data['joint_sales_value']
            combined_value = total_sales_value
            
            primary_formatted = format_price(primary_value)
            joint_formatted = format_price(joint_value)
            combined_formatted = format_price(combined_value)
            
            print(f"  Total Sales Value (Primary): {primary_formatted}")
            print(f"  Joint Sales Value: {joint_formatted}")
            print(f"  Combined Sales Value: {combined_formatted}")
    
    # Step 5: Mark the top agent as featured
    print(f"\nStep 5: Marking top agents as featured...")
    
    # Find all agents across all agencies
    all_agents = []
    for agency_id, agency_data in agencies_data.items():
        for agent_id, agent_data in agency_data["agents"].items():
            if agent_data["total_sales"] > 0:  # Only include agents with sales
                all_agents.append((agency_id, agent_id, agent_data["total_sales"]))
    
    # Sort by total sales (descending)
    all_agents.sort(key=lambda x: x[2], reverse=True)
    
    # Mark the top agent as featured
    if all_agents:
        top_agency_id, top_agent_id, _ = all_agents[0]
        agencies_data[top_agency_id]["agents"][top_agent_id]["featured"] = True
        agent_name = agencies_data[top_agency_id]["agents"][top_agent_id]["name"]
        print(f"\nMarked {agent_name} as featured agent")
    
    logger.info(f"Calculated metrics for agents in {suburb}")
    
    # Print summary
    total_agents = sum(len(agency_data["agents"]) for agency_data in agencies_data.values())
    print(f"\nFinal result: {len(agencies_data)} agencies with {total_agents} agents in {suburb}")
    
    return agencies_data

async def get_agent_sales_metrics(suburb, state="NSW"):
    """
    Get comprehensive sales metrics for agents in a specific suburb
    
    Returns:
        Dictionary with agencies, agents, and their sales metrics
    """
    logger.info(f"Getting agent sales metrics for {suburb}, {state}")
    
    # Get the raw sales data
    sales_data = await process_agent_sales_data(suburb, state)
    if not sales_data:
        logger.error(f"No sales data found for {suburb}")
        return {}
    
    # Calculate additional metrics for each agent
    for agency_id, agency_data in sales_data.items():
        for agent_name, agent_data in agency_data["agents"].items():
            # Skip if no properties sold
            if agent_data["propertiesSold"] == 0:
                continue
            
            # Calculate total sales value
            total_value = sum(agent_data["properties"].values())
            agent_data["totalSalesValue"] = total_value
            
            # Calculate average sale price
            avg_price = total_value / agent_data["propertiesSold"]
            agent_data["averageSalePrice"] = avg_price
            
            # Calculate median sale price
            if agent_data["properties"]:
                prices = list(agent_data["properties"].values())
                prices.sort()
                mid = len(prices) // 2
                if len(prices) % 2 == 0:
                    median_price = (prices[mid-1] + prices[mid]) / 2
                else:
                    median_price = prices[mid]
                agent_data["medianSalePrice"] = median_price
            else:
                agent_data["medianSalePrice"] = 0
            
            # Format prices for display
            agent_data["formattedTotalValue"] = format_price(total_value)
            agent_data["formattedAvgPrice"] = format_price(avg_price)
            agent_data["formattedMedianPrice"] = format_price(agent_data["medianSalePrice"])
    
    return sales_data

def format_price(price):
    """Format a price value as a string with appropriate units (k or m)"""
    if price >= 1000000:
        return f"${price/1000000:.1f}m"
    elif price >= 1000:
        return f"${price/1000:.0f}k"
    else:
        return f"${price:.0f}"

async def main():
    print("Starting Domain.com.au API test...")
    
    # Test the API with a suburb search
    suburb = "Bayview"
    print(f"Searching for sold listings in {suburb}...")
    
    # Test the new agent sales metrics function
    print("\n" + "="*50)
    print(f"Getting agent sales metrics for {suburb}...")
    sales_metrics = await get_agent_sales_metrics(suburb)
    
    if sales_metrics:
        print(f"\nFound {len(sales_metrics)} agencies with sales in {suburb}")
        
        # Print summary of each agency and their top agents
        for agency_id, agency_data in sales_metrics.items():
            print(f"\nAgency: {agency_data['name']}")
            print(f"Logo URL: {agency_data['logoUrl']}")
            
            # Get agents sorted by number of properties sold
            agents = list(agency_data["agents"].values())
            agents.sort(key=lambda x: x["propertiesSold"], reverse=True)
            
            print(f"Top agents ({len(agents)} total):")
            for i, agent in enumerate(agents[:3]):  # Show top 3 agents
                print(f"  {i+1}. {agent['name']}")
                print(f"     Photo: {agent['photoUrl']}")
                print(f"     Properties Sold: {agent['propertiesSold']}")
                print(f"     Total Sales Value: {agent.get('formattedTotalValue', 'N/A')}")
                print(f"     Median Sale Price: {agent.get('formattedMedianPrice', 'N/A')}")
                print(f"     Average Sale Price: {agent.get('formattedAvgPrice', 'N/A')}")
    else:
        print(f"No sales metrics found for {suburb}")
    
    print("Domain.com.au API test completed")
    
    # Now test the agent performance metrics
    print("\n" + "="*50)
    print(f"Calculating agent performance metrics for {suburb}...")
    agencies_data = await get_agent_performance_metrics(suburb)
    
    if agencies_data:
        # Convert the nested dictionary structure to a flat list of agents for display
        agents_list = []
        for agency_id, agency_data in agencies_data.items():
            agency_name = agency_data['name']
            for agent_id, agent_data in agency_data['agents'].items():
                if agent_data['total_sales'] > 0:  # Only include agents with sales
                    # Add agency name to the agent data for display
                    agent_data['agency'] = agency_name
                    agents_list.append(agent_data)
        
        # Sort agents by total sales (descending)
        agents_list.sort(key=lambda x: x['total_sales'], reverse=True)
        # Print the full dictionary structure in a readable format
        print("\n" + "="*50)
        print("Full data structure (formatted):")
        print(json.dumps(agencies_data, indent=2, default=str))
        print(f"\nFound {len(agents_list)} agents with sales in {suburb}")
        print("\nTop agents by sales volume:")
        
        # Display top 5 agents or all if less than 5
        top_agents = agents_list[:5] if len(agents_list) > 5 else agents_list
        
        for i, agent in enumerate(top_agents):
            print(f"{i+1}. {agent['name']} ({agent['agency']})")
            # Use the combined sales count (primary + joint)
            print(f"   Total Sales: {agent['total_sales'] }")
            print(f"   Joint Sales: {agent.get('joint_sales', 0)}")  # Display joint sales count
            print(f"   Median Sold Price: {agent['median_sold_price']}")
            
            # Use the combined sales value for display
            combined_value = agent.get('total_sales_value_combined', 0)
            if combined_value > 0:
                formatted_combined = f"${combined_value/1000000:.1f}m" if combined_value >= 1000000 else f"${combined_value/1000:.0f}k"
            else:
                formatted_combined = "Not disclosed"
                
            print(f"   Total Sales Value: {formatted_combined}")
            print(f"   Joint Sales Value: {agent.get('joint_sales_value_formatted', '$0')}")  # Display joint sales value
            print(f"   Photo URL: {agent.get('photo', 'N/A')}")
            
            # Find the agency logo URL for this agent
            agency_name = agent['agency']
            agency_logo = "N/A"
            for agency_id, agency_data in agencies_data.items():
                if agency_data['name'] == agency_name:
                    agency_logo = agency_data.get('logo', 'N/A')
                    break
            
            print(f"   Agency Logo URL: {agency_logo}")
            print()
        
        
    else:
        print(f"No agent data found for {suburb}")
    
    print("Domain.com.au API test completed")
# Run the main function if this file is executed directly
if __name__ == "__main__":
    asyncio.run(main())


