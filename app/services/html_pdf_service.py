import os
import tempfile
import logging
from datetime import datetime
from weasyprint import HTML, CSS
from jinja2 import Environment, FileSystemLoader, select_autoescape
import uuid

logger = logging.getLogger("articflow.html_pdf")

# Determine the directory of the current script (which is in app/services)
current_dir = os.path.dirname(os.path.abspath(__file__))
# The app directory is one level up from services
app_dir = os.path.dirname(current_dir)

# Set the base URL to the "template" folder inside the app directory
template_folder = os.path.join(app_dir, "templates")  # use "template" (singular) if that's your folder name
base_url = os.path.abspath(template_folder).replace('\\', '/')
print(f"Using base URL for WeasyPrint: {base_url}")
logger.info(f"Using base URL for WeasyPrint: {base_url}")
# Make sure assets directory exists
assets_dir = os.path.join(app_dir, "assets")
print(f"Using assets Dir for WeasyPrint: {assets_dir}")
os.makedirs(assets_dir, exist_ok=True)

# Set up Jinja2 environment for templates
template_dir = os.path.join(app_dir, "templates")
os.makedirs(template_dir, exist_ok=True)
env = Environment(loader=FileSystemLoader(template_dir))

async def generate_agents_report_html(data):
    template = env.get_template("agents_report.html")
    suburb = data.get("property", {}).get("suburb", "Local")
    template_data = {
        "suburb": suburb,
        "agents": data.get("top_agents", []),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    html_content = template.render(**template_data)
    return html_content

async def html_to_pdf(html_content, css_files=None, output_path=None):
    if not output_path:
        temp_dir = tempfile.gettempdir()
        output_path = os.path.join(temp_dir, f"report_{int(datetime.now().timestamp())}.pdf")
    
    css_list = []
    if css_files:
        for css_file in css_files:
            css_path = os.path.join(template_dir, "css", css_file)
            # Convert backslashes to forward slashes for WeasyPrint
            css_path = css_path.replace('\\', '/')
            if os.path.exists(css_path):
                css_list.append(CSS(filename=css_path, base_url=base_url))
                logger.info(f"Added CSS file: {css_path}")
            else:
                # Try with alternative name (styles.css vs style.css)
                alternative_name = "style.css" if css_file == "styles.css" else "styles.css"
                alternative_path = os.path.join(template_dir, "css", alternative_name)
                alternative_path = alternative_path.replace('\\', '/')
                if os.path.exists(alternative_path):
                    css_list.append(CSS(filename=alternative_path, base_url=base_url))
                    logger.info(f"CSS file {css_file} not found, using alternative: {alternative_path}")
                else:
                    logger.warning(f"CSS file not found: {css_path} or {alternative_path}")
    
    try:
        # Create HTML object with the proper base_url
        html = HTML(string=html_content, base_url=base_url)
        # Write PDF with CSS stylesheets
        html.write_pdf(output_path, stylesheets=css_list)
        logger.info(f"PDF generated successfully at {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Error generating PDF: {e}", exc_info=True)
        raise

async def generate_pdf_with_weasyprint(data, job_id=None, template_name="property_report.html"):
    """
    Generate a PDF from HTML using WeasyPrint
    
    Args:
        data: Dictionary with data for the template
        job_id: Optional job ID for tracking
        template_name: HTML template to use (default: property_report.html)
        
    Returns:
        Path to the generated PDF file
    """
    # Get job_id from data if not provided directly
    if not job_id and isinstance(data, dict) and "job_id" in data:
        job_id = data["job_id"]
    
    # Create a temporary directory for the PDF
    temp_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "temp")
    os.makedirs(temp_dir, exist_ok=True)
    
    # Add date and time to filename for better organization
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Use job_id in filename if provided, otherwise use property_id
    if job_id:
        filename = f"job_{job_id}_{current_time}.pdf"
    else:
        # Extract property ID or use a timestamp if not available
        if isinstance(data, dict) and "property" in data and "id" in data["property"]:
            property_id = data["property"]["id"]
        else:
            # Use timestamp as fallback
            import time
            property_id = f"property_{int(time.time())}"
        filename = f"{property_id}_{current_time}.pdf"
    
    output_path = os.path.join(temp_dir, filename)
    
    # CSS files to include
    css_files = ["styles.css"]
    
    # Check if this is a property report or agents report
    if "top_agents" in data:
        # This is an agents report
        html_content = await generate_agents_report_html(data)
    else:
        # This is a property report
        template = env.get_template(template_name)
        html_content = template.render(**data)
    
    # Generate PDF from HTML
    pdf_path = await html_to_pdf(html_content, css_files, output_path)
    return pdf_path
