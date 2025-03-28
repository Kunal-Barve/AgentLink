import logging
import requests
from datetime import datetime, timedelta
import os
from typing import Dict, List, Optional, Any

# Set up logging
logger = logging.getLogger(__name__)

# Get API key from environment variable
DOMAIN_API_KEY = os.environ.get("DOMAIN_API_KEY")

async def search_rental_listings_by_suburb(
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
    Search for rental listings in a specific suburb using Domain.com.au API
    
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
    
    logger.info(f"Searching for rental listings in {suburb}, {state}")
    
    # Store user's requested property types for post-filtering
    user_requested_property_types = property_types
    
    # Always use all property types in the API request
    all_property_types = ["AcreageSemiRural", "ApartmentUnitFlat", "Aquaculture", "BlockOfUnits", "CarSpace", "DairyFarming", "DevelopmentSite", "Duplex", "Farm", "FishingForestry", "NewHomeDesigns", "House", "NewHouseLand", "IrrigationServices", "NewLand", "Livestock", "NewApartments", "Penthouse", "RetirementVillage", "Rural", "SemiDetached", "SpecialistFarm", "Studio", "Terrace", "Townhouse", "VacantLand", "Villa", "Cropping", "Viticulture", "MixedFarming", "Grazing", "Horticulture", "Equine", "Farmlet", "Orchard", "RuralLifestyle"
]
     # Calculate date one year ago for filtering
    one_year_ago = datetime.now() - timedelta(days=365)
    one_year_ago_str = one_year_ago.strftime("%Y-%m-%d")
    # Prepare the search request payload
    payload = {
        "listingType": "Rent",
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
        "pageSize": 100,
        "listedSince": one_year_ago_str
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
            logger.info(f"Found {len(listings)} rental listings in {suburb}")
            print(f"Found {len(listings)} rental listings in {suburb}, {state}")  # Add this print statement
            
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
            return listings
        else:
            logger.error(f"API request failed with status code {response.status_code}: {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error searching for rental listings: {str(e)}")
        return None

async def fetch_agency_address(agency_id):
    """
    Fetch agency details including address from Domain.com.au API
    
    Args:
        agency_id: The ID of the agency to fetch details for
        
    Returns:
        Formatted address string or None if the request fails
    """
    if not DOMAIN_API_KEY:
        logger.error("Domain API key not found. Please set DOMAIN_API_KEY environment variable.")
        return None
    
    logger.info(f"Fetching agency details for agency ID: {agency_id}")
    
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
            agency_data = response.json()
            
            # Extract address components
            details = agency_data.get("details", {})
            street_address1 = details.get("streetAddress1", "")
            street_address2 = details.get("streetAddress2", "")
            suburb = details.get("suburb", "")
            state = details.get("state", "")
            postcode = details.get("postcode", "")
            
            # Construct the full address
            address_parts = []
            if street_address1:
                address_parts.append(street_address1)
            if street_address2:
                address_parts.append(street_address2)
            if suburb:
                address_parts.append(suburb)
            if state:
                address_parts.append(state)
            if postcode:
                address_parts.append(postcode)
            
            full_address = ", ".join([part for part in address_parts if part])
            
            logger.info(f"Successfully fetched address for agency {agency_id}: {full_address}")
            return full_address
        else:
            logger.error(f"API request failed with status code {response.status_code}: {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error fetching agency details: {str(e)}")
        return None

# Now update the process_agency_rental_data function to use real addresses for top agencies
async def process_agency_rental_data(suburb, state="NSW"):
    """
    Process rental listings data to create a dictionary of agencies and their rental properties
    
    Args:
        suburb: The suburb to analyze
        state: The state (default: NSW)
        
    Returns:
        Dictionary with agencies and their rental statistics
    """
    logger.info(f"Processing agency rental data for {suburb}, {state}")
    
    # Step 1: Get rental listings for the suburb
    listings = await search_rental_listings_by_suburb(suburb, state)
    if not listings:
        logger.error(f"No rental listings found for {suburb}")
        return {}
    
    logger.info(f"Found {len(listings)} rental listings to process")
    
    # Step 2: Create the agency data structure - now just counting appearances
    agency_counts = {}
    
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
        if agency_id not in agency_counts:
            agency_counts[agency_id] = {
                "id": agency_id,
                "name": agency_name,
                "logoUrl": agency_logo,
                "count": 0,
                # Add dummy address for now - will be updated for top agencies
                "address": f"{agency_name} Office, {suburb}, {state} 2000"
            }
        
        # Increment the count for this agency
        agency_counts[agency_id]["count"] += 1
    
    # Log summary of processed data
    total_agencies = len(agency_counts)
    
    logger.info(f"Processed data summary: {total_agencies} agencies found in {suburb}")
    print(f"Processed data summary: {total_agencies} agencies found in {suburb}")
    
    # Add detailed agency information for debugging
    for agency_id, agency_data in agency_counts.items():
        print(f"Agency: {agency_data['name']}")
        print(f"  - Listing count: {agency_data['count']}")
        print(f"  - Address: {agency_data['address']}")
    
    return agency_counts

async def get_top_rental_agencies(suburb, state="NSW", limit=5):
    """
    Get the top rental agencies in a suburb based on the number of listings
    
    Args:
        suburb: The suburb to analyze
        state: The state (default: NSW)
        limit: Maximum number of agencies to return (default: 5)
        
    Returns:
        List of top agencies with their metrics
    """
    # Get all agency data
    agency_counts = await process_agency_rental_data(suburb, state)
    
    # Convert to list and sort by count in descending order
    agencies_list = list(agency_counts.values())
    agencies_list.sort(key=lambda x: x["count"], reverse=True)
    
    # Get the top N agencies
    top_agencies = agencies_list[:limit]
    
    # Fetch real addresses for top agencies
    for agency in top_agencies:
        agency_id = agency["id"]
        print(f"Fetching address for agency ID: {agency_id} ({agency['name']})")  # Add debug print
        real_address = await fetch_agency_address(agency_id)
        if real_address:
            print(f"  - Got address: {real_address}")  # Add debug print
            agency["address"] = real_address
        else:
            print(f"  - Failed to get address, using default: {agency['address']}")  # Add debug print
    
    # Print top agencies information
    print(f"\nTop {limit} Rental Agencies in {suburb}, {state}:")
    for i, agency in enumerate(top_agencies):
        print(f"{i+1}. {agency['name']}")
        print(f"   - Listing count: {agency['count']}")
        print(f"   - Address: {agency['address']}")
        print(f"   - Logo URL: {agency['logoUrl']}")
    
    # Return the top N agencies
    return top_agencies

async def fetch_rented_property_data(
    property_id, 
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
    min_land_area=None,
    max_land_area=None
):
    """
    Fetch rental property data from Domain.com.au API
    
    Args:
        property_id: Not used for agency report, but kept for API consistency
        job_id: Optional job ID to include in the result
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
        Dictionary with agency data and metrics
    """
    logger.info(f"Fetching rental property data for job {job_id}, suburb={suburb}")
    
    # Get top rental agencies with all filter parameters
    top_agencies = await get_top_rental_agencies(suburb, state)
    
    # Verify each agency has an address before creating the result
    for agency in top_agencies:
        if "address" not in agency or not agency["address"]:
            logger.warning(f"Agency {agency['name']} is missing an address, using default")
            agency["address"] = f"{agency['name']} Office, {suburb}, {state} 2000"
    
    # Create the result structure - simplified for new design
    result = {
        "top_agencies": top_agencies,
        "suburb": suburb,
        "state": state,
    }
    
    # Print summary information with explicit address check
    print(f"\nSummary for {suburb}, {state}:")
    print(f"Top Agencies: {len(top_agencies)}")
    print("\nData being passed to the template:")
    for i, agency in enumerate(top_agencies):
        print(f"Agency #{i+1}: {agency['name']}")
        print(f"  - logoUrl: {agency['logoUrl']}")
        print(f"  - address: {agency.get('address', 'NO ADDRESS FOUND')}")  # Use get() with default
        print(f"  - totalPropertiesLeased: 0")
        print(f"  - totalPropertiesForLease: 0")
        print(f"  - totalRentedProperties: 0")
        print(f"  - leasingEfficiency: 0")
    
    # Add job_id to the result if provided
    if job_id:
        result["job_id"] = job_id
    
    return result