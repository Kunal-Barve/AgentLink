import os
import requests
import logging
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from supabase import create_client
load_dotenv()
# Domain.com.au API credentials
DOMAIN_API_KEY = os.getenv("DOMAIN_API_KEY")
DOMAIN_API_SECRET = os.getenv("DOMAIN_API_SECRET")
# Set up logging with more detailed configuration
logger = logging.getLogger("articflow.domain.utils")

_supabase_client = None

def _get_supabase():
    global _supabase_client
    if _supabase_client is None:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        _supabase_client = create_client(url, key)
    return _supabase_client

# Maps normalized price range string -> (comm column, mkt column) in agent_subscriptions
PRICE_RANGE_COL_MAP = {
    "Less than $500k": ("comm_less_500k",  "mkt_less_500k"),
    "$500k-$1m":       ("comm_500k_1m",    "mkt_500k_1m"),
    "$1m-$1.5m":       ("comm_1m_1_5m",    "mkt_1m_1_5m"),
    "$1.5m-$2m":       ("comm_1_5m_2m",    "mkt_1_5m_2m"),
    "$2m-$2.5m":       ("comm_2m_2_5m",    "mkt_2m_2_5m"),
    "$2.5m-$3m":       ("comm_2_5m_3m",    "mkt_2_5m_3m"),
    "$3m-$3.5m":       ("comm_3m_3_5m",    "mkt_3m_3_5m"),
    "$3.5m-$4m":       ("comm_3_5m_4m",    "mkt_3_5m_4m"),
    "$4m-$6m":         ("comm_4m_6m",      "mkt_4m_6m"),
    "$6m-$8m":         ("comm_6m_8m",      "mkt_6m_8m"),
    "$8m-$10m":        ("comm_8m_10m",     "mkt_8m_10m"),
    "$10m+":           ("comm_10m_plus",   "mkt_10m_plus"),
}


def normalize_home_owner_pricing(home_owner_pricing):
    """
    Normalize home_owner_pricing to the expected format.
    Handles multiple formats:
    - JotForm: "Less than $500k"
    - Meta form: "less_than_$500k"
    - N8N: "$3-$3.5m" (missing 'm' on first number)
    
    Args:
        home_owner_pricing: Price range string in any format
        
    Returns:
        Normalized price range string in the expected format
    """
    if not home_owner_pricing:
        return home_owner_pricing
    
    import re
    
    # Fix n8n format: $3-$3.5m → $3m-$3.5m (add missing 'm' on first number)
    # Pattern: $X-$Y.Ym or $X-$Ym where first number is missing the 'm'
    pattern = r'\$(\d+(?:\.\d+)?)-\$(\d+(?:\.\d+)?)m'
    match = re.match(pattern, home_owner_pricing)
    if match:
        first_num = match.group(1)
        second_num = match.group(2)
        home_owner_pricing = f"${first_num}m-${second_num}m"
    
    # Mapping from Meta form format to expected format
    normalization_map = {
        "less_than_$500k": "Less than $500k",
        "$500k_$1m": "$500k-$1m",
        "$1m_$1.5m": "$1m-$1.5m",
        "$1.5m_$2m": "$1.5m-$2m",
        "$2m_$2.5m": "$2m-$2.5m",
        "$2.5m_$3m": "$2.5m-$3m",
        "$3m_$3.5m": "$3m-$3.5m",
        "$3.5m_$4m": "$3.5m-$4m",
        "$4m_$6m": "$4m-$6m",
        "$6m_$8m": "$6m-$8m",
        "$8m_$10m": "$8m-$10m",
        "$10m+": "$10m+"
    }
    
    # Try direct mapping first (for Meta form format)
    if home_owner_pricing in normalization_map:
        return normalization_map[home_owner_pricing]
    
    # If already in correct format, return as-is
    return home_owner_pricing


def get_featured_agent_commission(agent_name, home_owner_pricing, suburb, state):
    """
    Get commission rates for a featured agent from Supabase agent_subscriptions table.

    Args:
        agent_name: Name of the agent
        home_owner_pricing: Price range of the property
        suburb: Suburb name
        state: State code (e.g., NSW)

    Returns:
        Dictionary containing commission_rate, discount, and marketing
    """
    try:
        home_owner_pricing = normalize_home_owner_pricing(home_owner_pricing)
        print(f"DEBUG - get_featured_agent_commission called with: agent_name='{agent_name}', home_owner_pricing='{home_owner_pricing}', suburb='{suburb}', state='{state}'")

        if not home_owner_pricing:
            logger.warning("No home_owner_pricing provided")
            return {"commission_rate": "", "discount": "", "marketing": ""}

        col_pair = PRICE_RANGE_COL_MAP.get(home_owner_pricing)
        if not col_pair:
            logger.warning(f"Unknown price range '{home_owner_pricing}', falling back to standard rates")
            return get_agent_commission(home_owner_pricing, state=state)

        comm_col, mkt_col = col_pair

        # Query agent_subscriptions by name — state may be NULL (uniform rates) or per-state
        sb = _get_supabase()
        name_norm = agent_name.strip()
        rows = sb.table("agent_subscriptions").select(
            f"name,state,{comm_col},{mkt_col}"
        ).ilike("name", name_norm).execute().data

        print(f"DEBUG - Supabase returned {len(rows)} row(s) for agent '{name_norm}'")

        commission_rate = ""
        marketing = ""

        if rows:
            state_upper = (state or "").strip().upper()
            # Prefer a row matching the state, fall back to state=NULL (uniform rates)
            state_match = next((r for r in rows if (r.get("state") or "").strip().upper() == state_upper), None)
            best_row = state_match or rows[0]
            commission_rate = best_row.get(comm_col) or ""
            marketing       = best_row.get(mkt_col)  or ""
            print(f"DEBUG - Found values from Supabase: commission_rate='{commission_rate}', marketing='{marketing}'")

        # Fall back to standard rates if either value is missing
        if not commission_rate or not marketing:
            logger.warning(f"No commission data for '{agent_name}' in Supabase, falling back to standard rates")
            standard_values = get_agent_commission(home_owner_pricing, state=state)
            if not commission_rate:
                commission_rate = standard_values.get("commission_rate", "")
            if not marketing:
                marketing = standard_values.get("marketing", "")

        # Calculate discount from commission_rate
        discount = ""
        if commission_rate:
            try:
                lowest_rate = float(commission_rate.split("-")[0].strip().replace("%", ""))
                price_ranges = {
                    "Less than $500k": 500000,
                    "$500k-$1m":       500000,
                    "$1m-$1.5m":       1000000,
                    "$1.5m-$2m":       1500000,
                    "$2m-$2.5m":       2000000,
                    "$2.5m-$3m":       2500000,
                    "$3m-$3.5m":       3000000,
                    "$3.5m-$4m":       3000000,
                    "$3m-$4m":         3000000,
                    "$4m-$6m":         4000000,
                    "$6m-$8m":         6000000,
                    "$8m-$10m":        8000000,
                    "$10m+":           10000000,
                }
                lowest_price = price_ranges.get(home_owner_pricing, 0)
                if lowest_price > 0:
                    raw_discount    = lowest_price * (lowest_rate / 100) * 0.2 * 0.25
                    rounded_discount = round(raw_discount / 250) * 250
                    rounded_discount = max(500, min(10000, rounded_discount))
                    discount = f"${rounded_discount:,.0f}"
                    logger.info(f"Calculated discount for {agent_name}: {discount}")
            except Exception as e:
                logger.error(f"Error calculating discount: {str(e)}")

        result = {"commission_rate": commission_rate, "discount": discount, "marketing": marketing}
        print(f"DEBUG - Returning result: {result}")
        return result

    except Exception as e:
        logger.error(f"Error getting featured agent commission: {str(e)}")
        print(f"DEBUG - Error getting featured agent commission: {str(e)}")
        return {"commission_rate": "", "discount": "", "marketing": ""}

def get_agent_commission(home_owner_pricing, area_type="suburb", state=None):
    """
    Get standard commission rates based on state, home owner pricing and area type
    
    Args:
        home_owner_pricing: Price range of the property
        area_type: Type of area (suburb, rural, inner_city)
        state: State code (e.g., NSW, VIC, QLD)
        
    Returns:
        Dictionary containing commission_rate and marketing
    """
    try:
        # Normalize home_owner_pricing to handle different input formats
        home_owner_pricing = normalize_home_owner_pricing(home_owner_pricing)
        
        # Debug: Print input parameters
        print(f"DEBUG - get_agent_commission called with: home_owner_pricing='{home_owner_pricing}', area_type='{area_type}', state='{state}'")
        
        # First try to get commission rates from the webhook if state code is provided
        if state and home_owner_pricing:
            # Debug: Attempting to fetch rates from webhook
            print(f"DEBUG - Attempting to fetch rates from webhook for state '{state}' and price '{home_owner_pricing}'")
            
            # Prepare the request parameters
            params = {
                "state_code": state,
                "home_owner_pricing": home_owner_pricing
            }
            
            # Make the API request
            url = "https://hook.eu2.make.com/wrkwzgqpensv34xlw14mcuzzcu79ohs9"
            try:
                response = requests.get(url, params=params)
                
                # Debug: Print response status
                print(f"DEBUG - API response status: {response.status_code}")
                
                # Check if the request was successful
                if response.status_code == 200:
                    data = response.json()
                    
                    # Debug: Print raw response data
                    print(f"DEBUG - API response data: {json.dumps(data, indent=2)}")
                    
                    # If we got data back
                    if data and isinstance(data, list) and len(data) > 0:
                        commission_data = data[0]
                        
                        # Map home_owner_pricing to the corresponding keys
                        commission_key = f"{home_owner_pricing} Commission"
                        marketing_key = f"{home_owner_pricing} Marketing"
                        
                        # Debug: Print the keys we're looking for
                        print(f"DEBUG - Looking for keys: commission_key='{commission_key}', marketing_key='{marketing_key}'")
                        
                        # Get the commission rate and marketing value for the specified price range
                        commission_rate = commission_data.get(commission_key, "")
                        marketing = commission_data.get(marketing_key, "")
                        
                        # Debug: Print the values found
                        print(f"DEBUG - Found webhook values: commission_rate='{commission_rate}', marketing='{marketing}'")
                        
                        # If both values are found, return them
                        if commission_rate and marketing:
                            logger.info(f"Using state-based rates from webhook for state {state}")
                            print(f"DEBUG - Using state-based rates from webhook")
                            return {
                                "commission_rate": commission_rate,
                                "marketing": marketing
                            }
                        else:
                            logger.warning(f"Incomplete data from webhook for state {state}, price {home_owner_pricing}. Falling back to area-type based rates.")
                            print(f"DEBUG - Incomplete data from webhook. Falling back to area-type based rates")
                    else:
                        logger.warning(f"No data from webhook for state {state}, price {home_owner_pricing}. Falling back to area-type based rates.")
                        print(f"DEBUG - No data from webhook. Falling back to area-type based rates")
                else:
                    logger.error(f"API request failed with status code {response.status_code}: {response.text}")
                    print(f"DEBUG - API request failed with status code {response.status_code}: {response.text}")
            except Exception as e:
                logger.error(f"Error fetching from webhook: {str(e)}")
                print(f"DEBUG - Error fetching from webhook: {str(e)}")
        
        # Fallback to area-type based rates
        print(f"DEBUG - Using fallback area-type based rates for area_type '{area_type}'")
        
        # Define standard commission rates for different price ranges in suburbs
        suburb_rates = {
            "Less than $500k": "1.98-2.20%",
            "$500k-$1m": "1.90-2.10%",
            "$1m-$1.5m": "1.80-1.98%",
            "$1.5m-$2m": "1.80-1.98%",
            "$2m-$2.5m": "1.75-1.95%",
            "$2.5m-$3m": "1.65-1.87%",
            "$3m-$3.5m": "1.55-1.705%",  # Split from $3m-$4m
            "$3.5m-$4m": "1.55-1.705%",  # Split from $3m-$4m
            "$4m-$6m": "1.50-1.75%",
            "$6m-$8m": "1.45-1.65%",
            "$8m-$10m": "1.25-1.50%",
            "$10m+": "1.25-1.50%"
        }
        
        # Define rural commission rates
        rural_rates = {
            "Less than $500k": "2.25-2.75%",
            "$500k-$1m": "2.25-2.75%",
            "$1m-$1.5m": "1.98-2.20%",
            "$1.5m-$2m": "1.90-2.02%",
            "$2m-$2.5m": "1.85-1.95%",
            "$2.5m-$3m": "1.75-1.87%",
            "$3m-$3.5m": "1.65-1.705%",  # Split from $3m-$4m
            "$3.5m-$4m": "1.65-1.705%",  # Split from $3m-$4m
            "$4m-$6m": "1.55-1.75%",
            "$6m-$8m": "1.50-1.65%",
            "$8m-$10m": "1.25-1.50%",
            "$10m+": "1.25-1.50%"
        }
        
        # Define inner city commission rates
        inner_city_rates = {
            "Less than $500k": "1.75-2.10%",
            "$500k-$1m": "1.75-2.00%",
            "$1m-$1.5m": "1.70-1.95%",
            "$1.5m-$2m": "1.65-1.85%",
            "$2m-$2.5m": "1.55-1.80%",
            "$2.5m-$3m": "1.50-1.75%",
            "$3m-$3.5m": "1.50-1.75%",  # Split from $3m-$4m
            "$3.5m-$4m": "1.50-1.75%",  # Split from $3m-$4m
            "$4m-$6m": "1.45-1.75%",
            "$6m-$8m": "1.35-1.65%",
            "$8m-$10m": "1.25-1.50%",
            "$10m+": "1.25-1.50%"
        }
        
        # Define standard marketing costs for different price ranges in suburbs
        suburb_marketing = {
            "Less than $500k": "$6,000-$7,500",
            "$500k-$1m": "$6,000-$8,000",
            "$1m-$1.5m": "$6,500-$8,500",
            "$1.5m-$2m": "$7,000-$9,000",
            "$2m-$2.5m": "$7,000-$9,000",
            "$2.5m-$3m": "$7,500-$9,500",
            "$3m-$3.5m": "$8,000-$10,000",  # Split from $3m-$4m
            "$3.5m-$4m": "$8,000-$10,000",  # Split from $3m-$4m
            "$4m-$6m": "$9,000-$11,500",
            "$6m-$8m": "$9,000-$11,500",
            "$8m-$10m": "$10,000-$12,000",
            "$10m+": "$10,000-$12,000"
        }
        
        # Define rural marketing costs
        rural_marketing = {
            "Less than $500k": "$2,000-$4,000",
            "$500k-$1m": "$2,500-$4,500",
            "$1m-$1.5m": "$3,000-$5,000",
            "$1.5m-$2m": "$3,500-$5,500",
            "$2m-$2.5m": "$4,000-$6,000",
            "$2.5m-$3m": "$4,500-$6,500",
            "$3m-$3.5m": "$5,000-$7,000",  # Split from $3m-$4m
            "$3.5m-$4m": "$5,000-$7,000",  # Split from $3m-$4m
            "$4m-$6m": "$5,500-$7,500",
            "$6m-$8m": "$6,000-$8,000",
            "$8m-$10m": "$6,500-$8,500",
            "$10m+": "$7,000-$9,000+"
        }
        
        # Define inner city marketing costs
        inner_city_marketing = {
            "Less than $500k": "$6,000-$7,500",
            "$500k-$1m": "$6,000-$8,000",
            "$1m-$1.5m": "$6,500-$8,500",
            "$1.5m-$2m": "$7,000-$9,000",
            "$2m-$2.5m": "$7,000-$9,000",
            "$2.5m-$3m": "$7,500-$9,500",
            "$3m-$3.5m": "$8,000-$10,000",  # Split from $3m-$4m
            "$3.5m-$4m": "$8,000-$10,000",  # Split from $3m-$4m
            "$4m-$6m": "$9,000-$11,500",
            "$6m-$8m": "$9,000-$11,500",
            "$8m-$10m": "$10,000-$12,000",
            "$10m+": "$10,000-$12,000"
        }
        
        # If home_owner_pricing is not provided, return empty values
        if not home_owner_pricing:
            logger.warning("No home_owner_pricing provided")
            return {"commission_rate": "", "marketing": ""}
        
        # Select the appropriate rate and marketing dictionaries based on area type
        if area_type.lower() == "rural":
            rates = rural_rates
            marketing_costs = rural_marketing
        elif area_type.lower() == "inner_city":
            rates = inner_city_rates
            marketing_costs = inner_city_marketing
        else:  # Default to suburb
            rates = suburb_rates
            marketing_costs = suburb_marketing
        
        # Get the commission rate and marketing cost for the specified price range
        commission_rate = rates.get(home_owner_pricing, "")
        marketing = marketing_costs.get(home_owner_pricing, "")
        
        return {
            "commission_rate": commission_rate,
            "marketing": marketing
        }
        
    except Exception as e:
        logger.error(f"Error getting standard agent commission: {str(e)}")
        return {"commission_rate": "", "marketing": ""}
    
def get_area_type(post_code, suburb):
    """
    Determine the area type (suburb, rural, inner_city) by making a request to Make.com webhook
    
    Args:
        post_code: The postal code of the area
        suburb: The suburb name
        
    Returns:
        String representing the area type (suburb, rural, inner_city)
    """
    try:
        # Prepare the request parameters
        params = {
            "post_code": post_code,
            "suburb": suburb
        }
        
        # Log the request
        logger.info(f"Getting area type for suburb: {suburb}, post code: {post_code}")
        print(f"DEBUG - Getting area type for suburb: {suburb}, post code: {post_code}")
        
        # Make the API request
        url = "https://hook.eu2.make.com/vq5xn04nnc9iio7nzjnkwu6ahkbtlizp"
        response = requests.get(url, params=params)
        
        # Check if the request was successful
        if response.status_code == 200:
            # Get the response data
            data = response.json()
            
            # Debug: Print raw response data
            print(f"DEBUG - Area type API response: {data}")
            
            # Map the numeric codes to area types
            # 0: not found, 1: inner_city, 2: suburb, 3: rural
            area_type_map = {
                "0": "suburb",  # Default to suburb if not found
                "1": "inner_city",
                "2": "suburb",
                "3": "rural",
                0: "suburb",
                1: "inner_city",
                2: "suburb",
                3: "rural"
            }
            
            # Convert data to string if it's a number
            if isinstance(data, (int, float)):
                area_type_code = data
            else:
                area_type_code = str(data)
            
            # Map the code to an area type
            area_type = area_type_map.get(area_type_code, "suburb")
            
            logger.info(f"Area type for {suburb} ({post_code}): {area_type} (code: {area_type_code})")
            print(f"DEBUG - Mapped area type code {area_type_code} to {area_type}")
            
            return area_type
        else:
            # If API request failed, default to suburb
            logger.error(f"API request for area type failed with status code {response.status_code}: {response.text}")
            return "suburb"
            
    except Exception as e:
        # If any error occurs, default to suburb
        logger.error(f"Error getting area type: {str(e)}")
        return "suburb"