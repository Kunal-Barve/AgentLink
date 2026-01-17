"""
Commission Leasing Service
Handles webhook calls to determine commission sheet and PDF selection for leasing reports
"""
import logging
import requests
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

WEBHOOK_URL = "https://n8n.srv1165267.hstgr.cloud/webhook/property-area-type"

# Commission folder mapping
COMMISSION_FOLDERS = {
    "1": "commission_inner_city",
    "2": "commission_suburbs",
    "3": "commission_rural"
}

# Valid rental values from Jotform
JOTFORM_RENTAL_VALUES = [
    "Less than $500pw",
    "$500-$1000pw",
    "$1000-$1500pw",
    "$1500-$2000pw",
    "$2000+pw"  # Jotform format
]

# Mapping from Jotform format to PDF filename format
RENTAL_VALUE_MAPPING = {
    "Less than $500pw": "Less than $500pw",
    "$500-$1000pw": "$500-$1000pw",
    "$1000-$1500pw": "$1000-$1500pw",
    "$1500-$2000pw": "$1500-$2000pw",
    "$2000+pw": "$2000pw+"  # Map Jotform format to PDF filename format
}


def call_area_type_webhook(suburb: str, state: str, post_code: str) -> Optional[str]:
    """
    Call the property area type webhook to get commission sheet number
    
    Args:
        suburb: Suburb name
        state: State code (e.g., QLD, NSW)
        post_code: Post code
        
    Returns:
        Commission sheet number as string ("1", "2", or "3") or None if failed
    """
    try:
        payload = {
            "suburb": suburb,
            "state": state,
            "post_code": post_code
        }
        
        logger.info(f"Calling webhook for area type: {payload}")
        
        response = requests.post(
            WEBHOOK_URL,
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            commission_sheet = data.get("Commission Sheet")
            
            logger.info(f"Webhook response: {data}")
            
            # Check if commission_sheet is None or invalid
            if commission_sheet is None or str(commission_sheet).lower() == "none":
                logger.warning(f"Webhook returned None for commission sheet")
                return None
            
            return str(commission_sheet)
        else:
            logger.error(f"Webhook failed with status {response.status_code}: {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Error calling area type webhook: {e}", exc_info=True)
        return None


def get_commission_sheet_with_retry(suburb: str, state: str, post_code: str) -> str:
    """
    Get commission sheet number with retry logic
    
    Args:
        suburb: Suburb name
        state: State code
        post_code: Post code
        
    Returns:
        Commission sheet number as string ("1", "2", or "3")
        Defaults to "1" if all attempts fail
    """
    # First attempt
    commission_sheet = call_area_type_webhook(suburb, state, post_code)
    
    if commission_sheet is not None:
        logger.info(f"Got commission sheet on first attempt: {commission_sheet}")
        return commission_sheet
    
    # Retry once
    logger.info("First attempt returned None, retrying...")
    commission_sheet = call_area_type_webhook(suburb, state, post_code)
    
    if commission_sheet is not None:
        logger.info(f"Got commission sheet on retry: {commission_sheet}")
        return commission_sheet
    
    # Default to 1
    logger.warning("Both attempts failed, defaulting to commission sheet 1")
    return "1"


def get_commission_pdf_path(commission_sheet: str, rental_value: str) -> Optional[Path]:
    """
    Get the path to the commission PDF based on commission sheet and rental value
    
    Args:
        commission_sheet: Commission sheet number ("1", "2", or "3")
        rental_value: Rental value string from Jotform (e.g., "$1000-$1500pw" or "$2000+pw")
        
    Returns:
        Path to the commission PDF or None if not found
    """
    # Validate commission sheet
    if commission_sheet not in COMMISSION_FOLDERS:
        logger.error(f"Invalid commission sheet: {commission_sheet}, defaulting to 1")
        commission_sheet = "1"
    
    # Validate rental value (check if it's a valid Jotform value)
    if rental_value not in RENTAL_VALUE_MAPPING:
        logger.error(f"Invalid rental value from Jotform: {rental_value}")
        logger.error(f"Valid values are: {list(RENTAL_VALUE_MAPPING.keys())}")
        return None
    
    # Map Jotform format to PDF filename format
    pdf_rental_value = RENTAL_VALUE_MAPPING[rental_value]
    logger.info(f"Mapped Jotform value '{rental_value}' to PDF filename '{pdf_rental_value}'")
    
    # Build path
    folder_name = COMMISSION_FOLDERS[commission_sheet]
    base_path = Path(__file__).parent.parent / "assets" / "pdfs" / folder_name
    
    # PDF filename matches the mapped rental value
    pdf_filename = f"{pdf_rental_value}.pdf"
    pdf_path = base_path / pdf_filename
    
    logger.info(f"Looking for commission PDF at: {pdf_path}")
    
    if pdf_path.exists():
        logger.info(f"Found commission PDF: {pdf_path}")
        return pdf_path
    else:
        logger.error(f"Commission PDF not found: {pdf_path}")
        return None


def get_leasing_commission_info(
    suburb: str, 
    state: str, 
    post_code: str, 
    rental_value: str
) -> Tuple[Optional[Path], str]:
    """
    Complete workflow to get commission PDF path for leasing report
    
    Args:
        suburb: Suburb name
        state: State code
        post_code: Post code
        rental_value: Rental value string
        
    Returns:
        Tuple of (commission_pdf_path, commission_sheet_number)
    """
    logger.info(f"Getting commission info for: {suburb}, {state}, {post_code}, {rental_value}")
    
    # Step 1: Get commission sheet number
    commission_sheet = get_commission_sheet_with_retry(suburb, state, post_code)
    
    # Step 2: Get commission PDF path
    commission_pdf_path = get_commission_pdf_path(commission_sheet, rental_value)
    
    return commission_pdf_path, commission_sheet
