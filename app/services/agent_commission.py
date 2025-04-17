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


def get_featured_agent_commission(agent_name, home_owner_pricing, suburb, state):
    """
    Get commission rates for a featured agent by making a request to Make.com webhook
    
    Args:
        agent_name: Name of the agent
        home_owner_pricing: Price range of the property
        suburb: Suburb name
        state: State code (e.g., NSW)
        
    Returns:
        Dictionary containing commission_rate, discount, and marketing
    """
    try:
        # Debug: Print input parameters
        print(f"DEBUG - get_featured_agent_commission called with: agent_name='{agent_name}', home_owner_pricing='{home_owner_pricing}', suburb='{suburb}', state='{state}'")
        
        # Prepare the request parameters
        params = {
            "agent_name": agent_name,
            "suburb": suburb,
            "state_code": state
        }
        
        # Debug: Print request parameters
        print(f"DEBUG - API request params: {params}")
        
        # Make the API request
        url = "https://hook.eu2.make.com/4d6cv0gxrw8aok5becjj1odpb55mpiqw"
        response = requests.get(url, params=params)
        
        # Debug: Print response status and headers
        print(f"DEBUG - API response status: {response.status_code}")
        print(f"DEBUG - API response headers: {response.headers}")
        
        # Check if the request was successful
        if response.status_code == 200:
            data = response.json()
            
            # Debug: Print raw response data
            print(f"DEBUG - API response data: {json.dumps(data, indent=2)}")
            
            # If no data returned or empty list
            if not data or len(data) == 0:
                logger.warning(f"No commission data found for agent {agent_name} in {suburb}, {state}")
                print(f"DEBUG - No commission data found for agent {agent_name} in {suburb}, {state}")
                # Fall back to standard commission rates
                return get_agent_commission(home_owner_pricing)
            
            # Get the first item from the response
            commission_data = data[0]
            
            # Debug: Print commission data keys
            print(f"DEBUG - Commission data keys: {list(commission_data.keys())}")
            
            # If home_owner_pricing is not provided, return empty values
            if not home_owner_pricing:
                logger.warning("No home_owner_pricing provided")
                print("DEBUG - No home_owner_pricing provided")
                return {"commission_rate": "", "discount": "", "marketing": ""}
            
            # Map home_owner_pricing to the corresponding commission key
            commission_key = f"{home_owner_pricing} Commission"
            # Map home_owner_pricing to the corresponding marketing key
            marketing_key = f"{home_owner_pricing} Marketing"
            
            # Debug: Print the keys we're looking for
            print(f"DEBUG - Looking for keys: commission_key='{commission_key}', marketing_key='{marketing_key}'")
            
            # Get the commission rate and marketing value for the specified price range
            commission_rate = commission_data.get(commission_key, "")
            marketing = commission_data.get(marketing_key, "")
            
            # Debug: Print the values found
            print(f"DEBUG - Found values: commission_rate='{commission_rate}', marketing='{marketing}'")
            
            # If commission rate is empty, fall back to standard rates
            if not commission_rate or not marketing:
                logger.warning(f"Empty commission rate or marketing for {agent_name} in {suburb}, {state} with price range {home_owner_pricing}")
                print(f"DEBUG - Empty commission rate or marketing, falling back to standard rates")
                standard_values = get_agent_commission(home_owner_pricing)
                
                # Only use standard values if our values are empty
                if not commission_rate:
                    commission_rate = standard_values.get("commission_rate", "")
                    print(f"DEBUG - Using standard commission rate: {commission_rate}")
                
                if not marketing:
                    marketing = standard_values.get("marketing", "")
                    print(f"DEBUG - Using standard marketing: {marketing}")
            
            # Calculate discount if commission rate is available
            discount = ""
            if commission_rate:
                # Extract the lowest commission rate from the range (e.g., "1.65-1.85%" -> 1.65)
                try:
                    lowest_rate = float(commission_rate.split("-")[0].strip().replace("%", ""))
                    
                    # Debug: Print the extracted rate
                    print(f"DEBUG - Extracted lowest rate: {lowest_rate}")
                    
                    # Extract the lowest price from the range
                    price_ranges = {
                        "Less than $500k": 500000,
                        "$500k-$1m": 500000,
                        "$1m-$1.5m": 1000000,
                        "$1.5m-$2m": 1500000,
                        "$2m-$2.5m": 2000000,
                        "$2.5m-$3m": 2500000,
                        "$3m-$4m": 3000000,
                        "$4m-$6m": 4000000,
                        "$6m-$8m": 6000000,
                        "$8m-$10m": 8000000,
                        "$10m+": 10000000
                    }
                    
                    lowest_price = price_ranges.get(home_owner_pricing, 0)
                    
                    # Debug: Print the extracted price
                    print(f"DEBUG - Extracted lowest price: ${lowest_price:,}")
                    
                    if lowest_price > 0:
                        # Calculate discount: price × lowest_rate × 20% × 30%
                        raw_discount = lowest_price * (lowest_rate / 100) * 0.2 * 0.3
                        
                        # Debug: Print the raw discount
                        print(f"DEBUG - Raw discount calculation: ${raw_discount:,.2f}")
                        
                        # Round to nearest 500
                        rounded_discount = round(raw_discount / 500) * 500
                        
                        # Debug: Print the rounded discount
                        print(f"DEBUG - Rounded discount: ${rounded_discount:,.0f}")
                        
                        # Format as currency
                        discount = f"${rounded_discount:,.0f}"
                        
                        logger.info(f"Calculated discount for {agent_name}: {discount}")
                    else:
                        logger.warning(f"Invalid home_owner_pricing: {home_owner_pricing}")
                        print(f"DEBUG - Invalid home_owner_pricing: {home_owner_pricing}")
                except Exception as e:
                    logger.error(f"Error calculating discount: {str(e)}")
                    print(f"DEBUG - Error calculating discount: {str(e)}")
            
            result = {
                "commission_rate": commission_rate,
                "discount": discount,
                "marketing": marketing
            }
            
            # Debug: Print the final result
            print(f"DEBUG - Returning result: {result}")
            
            return result
        else:
            logger.error(f"API request failed with status code {response.status_code}: {response.text}")
            print(f"DEBUG - API request failed with status code {response.status_code}: {response.text}")
            return {"commission_rate": "", "discount": "", "marketing": ""}
            
    except Exception as e:
        logger.error(f"Error getting featured agent commission: {str(e)}")
        print(f"DEBUG - Error getting featured agent commission: {str(e)}")
        return {"commission_rate": "", "discount": "", "marketing": ""}

def get_agent_commission(home_owner_pricing):
    """
    Get standard commission rates based on home owner pricing
    
    Args:
        home_owner_pricing: Price range of the property
        
    Returns:
        Dictionary containing commission_rate and marketing
    """
    try:
        # Define standard commission rates for different price ranges
        standard_rates = {
            "Less than $500k": "1.80-2.00%",
            "$500k-$1m": "1.80-2.00%",
            "$1m-$1.5m": "1.65-1.85%",
            "$1.5m-$2m": "1.60-1.80%",
            "$2m-$2.5m": "1.50-1.75%",
            "$2.5m-$3m": "1.50-1.75%",
            "$3m-$4m": "1.50-1.75%",
            "$4m-$6m": "1.50-1.75%",
            "$6m-$8m": "1.45-1.65%",
            "$8m-$10m": "1.35-1.55%",
            "$10m+": "1.30-1.50%"
        }
        
        # Define standard marketing costs for different price ranges
        standard_marketing = {
            "Less than $500k": "$7,000-$8,000",
            "$500k-$1m": "$7,000-$8,000",
            "$1m-$1.5m": "$8,000-$9,000",
            "$1.5m-$2m": "$8,000-$9,000",
            "$2m-$2.5m": "$9,000-$10,000",
            "$2.5m-$3m": "$9,000-$10,000",
            "$3m-$4m": "$9,000-$10,000",
            "$4m-$6m": "$9,000-$10,000",
            "$6m-$8m": "$9,000-$10,000",
            "$8m-$10m": "$10,000+",
            "$10m+": "$10,000+"
        }
        
        # If home_owner_pricing is not provided, return empty values
        if not home_owner_pricing:
            logger.warning("No home_owner_pricing provided")
            return {"commission_rate": "", "marketing": ""}
        
        # Get the commission rate and marketing cost for the specified price range
        commission_rate = standard_rates.get(home_owner_pricing, "")
        marketing = standard_marketing.get(home_owner_pricing, "")
        
        return {
            "commission_rate": commission_rate,
            "marketing": marketing
        }
        
    except Exception as e:
        logger.error(f"Error getting standard agent commission: {str(e)}")
        return {"commission_rate": "", "marketing": ""}