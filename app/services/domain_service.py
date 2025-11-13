import os
import requests
from dotenv import load_dotenv
import logging
import asyncio
import json
from .domain_utils import (
    format_price, check_featured_agent, check_standard_subscription,
    get_mock_property_data, get_listing_details, get_agency_details,get_agent_details
)
from .agent_commission import (
 get_featured_agent_commission, get_agent_commission ,get_area_type
)
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
    max_land_area: int = None ,
    home_owner_pricing=None
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
    # Add default 'featured' key to all agents
    for agent in agents_list:
        agent['featured'] = False
        agent['featured_plus'] = False
    print("\n===== AGENTS LIST =====")
    print(agents_list)
    # Check for featured agents in the suburb
    print("\n===== CHECKING FOR FEATURED AGENTS =====")
    featured_agents_data = await check_featured_agent(suburb, state)
    print(f"Featured agents data: {featured_agents_data}")
    
    
    # Get the Area Type
    print("\n===== CHECKING FOR AREA TYPE =====")
    area_type = get_area_type(post_code, suburb)
    print(f"Area type for {suburb}: {area_type}")
    # Process featured agents if any were found
    if featured_agents_data:
        print(f"Found {len(featured_agents_data)} featured agents for {suburb}, {state}")
        
        for featured_agent_info in featured_agents_data:
            # Check if this is a manually entered agent (Manual Pull Data = Yes)
            if featured_agent_info.get("Manully Pull Data", "").strip().lower() == "yes":
                print(f"Processing manually entered featured agent: {featured_agent_info.get('Name')}")
                
                # Extract agent data from the response
                agent_name = featured_agent_info.get("Name", "").strip()
                agency_name = featured_agent_info.get("Agency", "").strip()
                agent_total_sales = int(featured_agent_info.get("Total Sales", "0").replace(",", ""))
                agent_median_sold_price = featured_agent_info.get("Median Sold Price", "$0")
                agent_sale_value = featured_agent_info.get("Total Sales Value", "$0")
                
                # Check if this is a Featured Plus agent
                is_featured_plus = featured_agent_info.get("Subscription Type", "").strip() == "Featured Plus"
                print(f"Agent {agent_name} is Featured Plus: {is_featured_plus}")
                
                # Check if agent photo and agency photo are provided
                agent_photo = featured_agent_info.get("Agent Photo", "").strip()
                agency_photo = featured_agent_info.get("Agency Photo", "").strip()
                
                # Convert Dropbox URLs from dl=0 to dl=1 to make them downloadable
                if agent_photo and agent_photo.endswith("dl=0"):
                    agent_photo = agent_photo[:-1] + "1"
                
                if agency_photo and agency_photo.endswith("dl=0"):
                    agency_photo = agency_photo[:-1] + "1"
                
                # Only call get_agent_details if photos are not provided
                agent_details = None
                if not (agent_photo and agency_photo):
                    agent_details = await get_agent_details(agent_name, agency_name)
                
                # Get featured agent commission rate and discount
                featured_agent_commission = get_featured_agent_commission(agent_name, home_owner_pricing, suburb, state)
                featured_agent_commission_rate = featured_agent_commission.get("commission_rate", "")
                featured_agent_discount = featured_agent_commission.get("discount", "")
                featured_agent_marketing = featured_agent_commission.get("marketing", "")
                
                
                # Debug: Print the commission values for this agent
                print(f"DEBUG - Featured agent commission for {agent_name}: rate='{featured_agent_commission_rate}', discount='{featured_agent_discount}', marketing='{featured_agent_marketing}'")
                print(f"DEBUG - home_owner_pricing value: '{home_owner_pricing}'")
                # Create a new agent entry
                # Create a new agent entry
                new_agent = {
                    "name": agent_name,
                    "total_sales": agent_total_sales,
                    "median_sold_price": agent_median_sold_price,
                    "total_value": agent_sale_value,
                    "featured": True,
                    "featured_plus": is_featured_plus,
                    "photo": agent_photo if agent_photo else (agent_details.get("agent_photo", "N/A") if agent_details else "N/A"),
                    "agency": agency_name if agency_name else (agent_details.get("agency_name", "N/A") if agent_details else "N/A"),
                    "agency_logo": agency_photo if agency_photo else (agent_details.get("agency_logo", "N/A") if agent_details else "N/A"),
                    "agent_id": agent_details.get("agent_id", "N/A") if agent_details else "N/A",
                    "properties": {},  # Empty properties dictionary
                    "commission_rate": featured_agent_commission_rate,
                    "discount": featured_agent_discount,
                    "marketing": featured_agent_marketing
                }
                # Debug: Print the agent object to verify commission values were added
                print(f"DEBUG - New agent object commission values: rate='{new_agent['commission_rate']}', discount='{new_agent['discount']}', marketing='{new_agent['marketing']}'")
                
                # Check if this agent already exists in the list
                existing_agent = None
                for idx, agent in enumerate(agents_list):
                    if agent['name'].strip().lower() == agent_name.lower():
                        existing_agent = idx
                        break
                
                if existing_agent is not None:
                    # Update the existing agent instead of adding a duplicate
                    print(f"Agent {agent_name} already exists in list at index {existing_agent}. Updating instead of adding duplicate.")
                    agents_list[existing_agent].update(new_agent)
                    print(f"Updated existing agent to featured: {agent_name}")
                else:
                    # Add the new agent to the agents list
                    agents_list.append(new_agent)
                    print(f"Added manually entered featured agent: {agent_name}")
            else:
                # For non-manual agents, check if they match any existing agents
                agent_name = featured_agent_info.get("Name", "").strip().lower()
                
                print(f"Checking for existing agent match: {agent_name}")
                
                # Look for a match in our existing agents list
                found_match = False
                for agent in agents_list:
                    if agent["name"].strip().lower() == agent_name:
                        agent["featured"] = True
                        # Check if this is a Featured Plus agent
                        agent["featured_plus"] = featured_agent_info.get("Subscription Type", "").strip() == "Featured Plus"
                        print(f"Agent {agent['name']} is Featured Plus: {agent['featured_plus']}")
                        # Get featured agent commission rate and discount
                        featured_agent_commission = get_featured_agent_commission(agent["name"], home_owner_pricing, suburb, state)
                        agent["commission_rate"] = featured_agent_commission.get("commission_rate", "")
                        agent["discount"] = featured_agent_commission.get("discount", "")
                        agent["marketing"] = featured_agent_commission.get("marketing", "")
                        
                        # Debug: Print the commission values for this agent
                        print(f"DEBUG - Existing agent commission for {agent['name']}: rate='{agent['commission_rate']}', discount='{agent['discount']}', marketing='{agent['marketing']}'")
                        print(f"DEBUG - home_owner_pricing value: '{home_owner_pricing}'")
                        
                        found_match = True
                        print(f"Matched existing agent as featured: {agent['name']}")
                        break
                
                if not found_match:
                    print(f"No match found for featured agent: {agent_name}")
    else:
        print(f"No featured agents found for {suburb}, {state}")
        
    # If no featured agents were found, get the standard commission rate
    if not featured_agents_data:
        print(f"No featured agents found for {suburb}, {state}")
        # Get standard agent commission rate
        agent_commission = get_agent_commission(home_owner_pricing, area_type , state)
        agent_commission_rate = agent_commission.get("commission_rate", "")
        agent_marketing = agent_commission.get("marketing", "")
        # Debug: Print the standard commission values
        print(f"DEBUG - Standard commission rate: '{agent_commission_rate}', marketing: '{agent_marketing}'")
        print(f"DEBUG - home_owner_pricing value: '{home_owner_pricing}'")
        
        # Create a cache for standard subscription status to avoid duplicate API calls
        std_sub_status_cache = {}
        # Check for standard subscription for non-featured agents
        for agent in agents_list:
            agent_name = agent['name']
            # Skip featured agents - they already have highest priority
            if agent['featured']:
                continue
                
            # Check if we already have the subscription status for this agent in the cache
            if agent_name in std_sub_status_cache:
                agent['standard_subscription'] = std_sub_status_cache[agent_name]
                logger.info(f"Using cached standard subscription status for {agent_name}: {agent['standard_subscription']}")
            else:
                # If not in cache, make the API call
                has_std_subscription = await check_standard_subscription(agent_name, suburb, state)
                agent['standard_subscription'] = has_std_subscription
                # Store in cache for future use
                std_sub_status_cache[agent_name] = has_std_subscription
                if has_std_subscription:
                    logger.info(f"Agent {agent_name} has standard subscription")
            # Add commission rate for non-featured agents - changed condition to not check featured_agents_data is None
            if not agent.get('featured', False) and 'commission_rate' not in agent:
                agent['commission_rate'] = agent_commission_rate
                agent['discount'] = None
                agent['marketing'] = agent_marketing
                print(f"DEBUG - Added standard commission to agent {agent_name}: rate='{agent_commission_rate}', marketing='{agent_marketing}'")
    else:
        # Create a cache for standard subscription status to avoid duplicate API calls
        std_sub_status_cache = {}
        # Check for standard subscription for non-featured agents
        for agent in agents_list:
            agent_name = agent['name']
            # Skip featured agents - they already have highest priority
            if agent['featured']:
                continue
                
            # Check if we already have the subscription status for this agent in the cache
            if agent_name in std_sub_status_cache:
                agent['standard_subscription'] = std_sub_status_cache[agent_name]
                logger.info(f"Using cached standard subscription status for {agent_name}: {agent['standard_subscription']}")
            else:
                # If not in cache, make the API call
                has_std_subscription = await check_standard_subscription(agent_name, suburb, state)
                agent['standard_subscription'] = has_std_subscription
                # Store in cache for future use
                std_sub_status_cache[agent_name] = has_std_subscription
                if has_std_subscription:
                    logger.info(f"Agent {agent_name} has standard subscription")
    
    # Final deduplication step - ensure no duplicates make it to the final list
    print("\n===== FINAL DEDUPLICATION BEFORE CATEGORIZATION =====")
    print(f"Total agents before final deduplication: {len(agents_list)}")
    
    final_unique_agents = {}
    for agent in agents_list:
        agent_name = agent['name'].strip().lower()
        agent_key = agent_name  # Use just the name as key for final deduplication
        
        if agent_key in final_unique_agents:
            # Duplicate found - keep the one with featured status, or the one with more data
            existing = final_unique_agents[agent_key]
            print(f"Duplicate found: {agent['name']} (Featured: {agent.get('featured', False)}) vs existing (Featured: {existing.get('featured', False)})")
            
            # Prioritize featured agents
            if agent.get('featured', False) and not existing.get('featured', False):
                print(f"  Keeping new agent (featured)")
                final_unique_agents[agent_key] = agent
            elif not agent.get('featured', False) and existing.get('featured', False):
                print(f"  Keeping existing agent (featured)")
                # Keep existing
            elif agent.get('featured', False) and existing.get('featured', False):
                # Both are featured, merge the data and keep the one with more complete information
                print(f"  Both are featured - merging data")
                # Use the one with more sales data, or manual data if available
                if agent.get('total_sales', 0) > existing.get('total_sales', 0):
                    final_unique_agents[agent_key] = agent
                # Keep existing if it has equal or more sales
            else:
                # Neither is featured, keep the one with more sales
                if agent.get('total_sales', 0) > existing.get('total_sales', 0):
                    print(f"  Keeping new agent (higher sales)")
                    final_unique_agents[agent_key] = agent
                else:
                    print(f"  Keeping existing agent (higher or equal sales)")
        else:
            final_unique_agents[agent_key] = agent
    
    agents_list = list(final_unique_agents.values())
    print(f"Total agents after final deduplication: {len(agents_list)}")
    print("=" * 50)
    
    # Separate agents into three categories: featured, standard subscription, and regular
    featured_agents = [agent for agent in agents_list if agent['featured']]
    std_sub_agents = [agent for agent in agents_list if not agent['featured'] and agent.get('standard_subscription', False)]
    regular_agents = [agent for agent in agents_list if not agent['featured'] and not agent.get('standard_subscription', False)]
    
    # Sort standard subscription and regular agents by total sales (descending)
    std_sub_agents.sort(key=lambda x: x['total_sales'], reverse=True)
    regular_agents.sort(key=lambda x: x['total_sales'], reverse=True)
    
    # Combine agents in priority order: featured first, then standard subscription, then regular
    # Calculate how many agents we need from each category to make up to 5 total
    if featured_agents:
        logger.info(f"Found {len(featured_agents)} featured agents in {suburb}")
        remaining_spots = 5 - len(featured_agents)
        
        if std_sub_agents and remaining_spots > 0:
            logger.info(f"Found {len(std_sub_agents)} standard subscription agents in {suburb}")
            std_sub_needed = min(remaining_spots, len(std_sub_agents))
            remaining_spots -= std_sub_needed
            
            # Calculate how many regular agents we need
            regular_needed = min(remaining_spots, len(regular_agents)) if remaining_spots > 0 else 0
            
            # Combine all categories
            top_agents = featured_agents + std_sub_agents[:std_sub_needed] + regular_agents[:regular_needed]
        else:
            # No standard subscription agents, just use regular agents to fill remaining spots
            top_agents = featured_agents + regular_agents[:remaining_spots]
    elif std_sub_agents:
        logger.info(f"No featured agents found, but found {len(std_sub_agents)} standard subscription agents in {suburb}")
        # No featured agents, but we have standard subscription agents
        std_sub_needed = min(5, len(std_sub_agents))
        remaining_spots = 5 - std_sub_needed
        
        # Calculate how many regular agents we need
        regular_needed = min(remaining_spots, len(regular_agents)) if remaining_spots > 0 else 0
        
        # Combine standard subscription and regular agents
        top_agents = std_sub_agents[:std_sub_needed] + regular_agents[:regular_needed]
    else:
        logger.info(f"No featured or standard subscription agents found in {suburb}")
        # No featured or standard subscription agents, just take top 5 regular agents
        top_agents = regular_agents[:5] if len(regular_agents) > 5 else regular_agents
    

    # Format the top agents data for the PDF
    formatted_top_agents = []
    for agent in top_agents:
        # Use the combined total value (primary + joint sales)
        total_value = agent.get('total_sales_value_combined', 0)
        
        # For manually entered agents, use the total_value directly
        if agent.get('featured', False) and len(agent.get('properties', {})) == 0 and agent.get('total_value'):
            formatted_total = agent.get('total_value')
        else:
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
            "featured": agent.get('featured', False),
            "featured_plus": agent.get('featured_plus', False), 
            "commission_rate": agent.get('commission_rate', ''),
            "discount": agent.get('discount', ''),
            "marketing": agent.get('marketing', '')
        }
        formatted_top_agents.append(formatted_agent)
    logger.info(f"TOP AGENTS ALL DATA:{formatted_top_agents}")
    result = {
        "top_agents": formatted_top_agents,
        "suburb": suburb,
        "agent_commission": agent_commission_rate if not featured_agents_data else None,
        "discount": None  # Default value for non-featured agents
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
