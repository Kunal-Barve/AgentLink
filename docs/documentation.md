# AgentLink: Project Documentation

## Project Overview

AgentLink is a FastAPI-based web application that:

1. Fetches real estate data from Domain.com.au API
2. Generates detailed PDF reports for properties, agents, and agencies
3. Uploads these reports to Dropbox
4. Provides APIs to monitor job status and retrieve report links

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Key Components](#key-components)
3. [Domain Service Deep Dive](#domain-service-deep-dive)
4. [API Endpoints](#api-endpoints)
5. [Workflows](#workflows)
6. [Data Flow Diagrams](#data-flow-diagrams)
7. [Dependencies](#dependencies)
8. [Server Access](#server-access)

## System Architecture

The application follows a service-oriented architecture with the following layers:

1. **API Layer**: FastAPI endpoints that handle HTTP requests
2. **Service Layer**: Business logic separated into domain-specific services
3. **Integration Layer**: Connectors to external APIs (Domain.com.au, Dropbox)
4. **Presentation Layer**: HTML templates and PDF generation

## Key Components

### 1. API Layer (`main.py`)
- FastAPI application handling HTTP endpoints
- Background job processing for report generation
- Job status monitoring and tracking
- Integration points between all services

### 2. Domain Integration (`domain_service.py`, `domain_agency_service.py`)
- Fetches property data from Domain.com.au API
- Gets top agent performance metrics in suburbs
- Processes rental listings and agency data
- Deduplicates and normalizes agent data across branches

### 3. Commission Services (`agent_commission.py`)
- Calculates agent commission rates based on property pricing and area type
- Determines area types (suburb, rural, inner_city)
- Calculates discounts for featured agents
- Integrates with Make.com webhooks for agent-specific commission data

### 4. PDF Generation (`html_pdf_service.py`)
- Generates HTML reports using Jinja2 templates
- Converts HTML to PDF using WeasyPrint
- Includes styling and formatted content

### 5. Dropbox Integration (`dropbox_service.py`)
- Manages OAuth token handling and refresh
- Uploads files to specific Dropbox folders
- Generates shareable links for uploaded PDFs
- Handles authentication errors and retries

### 6. Templates (`/app/templates/`)
- HTML templates for different report types:
  - `agents_report.html`: Top agents in a suburb
  - `agency_report.html`: Top agencies in a suburb
  - `property_report.html`: Property details
  - `commission_report.html`: Commission rates
  - `not_found.html`: Fallback for no results

## Domain Service Deep Dive

The `domain_service.py` file is a core component of the AgentLink application, responsible for interacting with the Domain.com.au API and processing real estate data.

### 1. Main Function: `fetch_property_data`

This function serves as the central data-gathering mechanism for the application.

#### What it does:
- Fetches top real estate agents in a specified suburb
- Gets their performance metrics (sales, values, etc.)
- Identifies and marks featured agents
- Processes agent commissions for reports
- Deduplicates agents appearing in multiple branches

#### When it's used:
When users request reports about agents in a specific suburb via the `/api/generate-agents-report` endpoint.

#### Parameters it accepts:
- `property_id`: ID for a specific property (optional)
- `suburb`: The suburb to analyze (default: "Queenscliff")
- `state`: State code (default: "NSW")
- `property_types`: Types of properties to include
- `min_bedrooms`, `max_bedrooms`: Bedroom range filters
- `min_bathrooms`, `max_bathrooms`: Bathroom range filters
- `min_carspaces`, `max_carspaces`: Carspace range filters
- `include_surrounding_suburbs`: Whether to include nearby suburbs
- `post_code`: Filter by postal code
- `min_land_area`, `max_land_area`: Land size filters
- `home_owner_pricing`: Property price range (used for commission calculations)

#### How it works (in simple terms):

1. **Gets agent performance data**: Calls `get_agent_performance_metrics` to find all agents with sales in the suburb
2. **Converts data format**: Changes from a nested agency->agents structure to a flat list of agents
3. **Deduplicates agents**: Removes duplicates when the same agent appears in multiple branch offices
4. **Checks for featured agents**: Uses `check_featured_agent` to find agents who have paid for featured status
5. **Gets area type**: Determines if this is a suburban, rural, or inner city area (affects commission rates)
6. **Processes featured agents**: Adds special handling for featured agents including:
   - Marking them as featured in the data
   - Getting their special commission rates and discounts
   - Ensuring their photos and agency logos are included
7. **Returns the processed data**: A structured list of agents with all their details and metrics

### 2. Supporting Functions in Domain Service

#### `search_sold_listings_by_suburb`
- **What it does**: Searches for recently sold properties in a specified suburb
- **When used**: To find sales data for analyzing agent performance
- **How it works**: Makes API calls to Domain.com.au with specific filters for location and property characteristics

#### `process_agent_sales_data`
- **What it does**: Organizes sales data by agencies and agents
- **When used**: To structure raw sales data into a useful format
- **How it works**: Groups sales by agency and agent, counting how many properties each agent has sold

#### `get_agent_performance_metrics`
- **What it does**: Calculates key performance indicators for agents
- **When used**: To determine which agents are top performers in a suburb
- **How it works**:
  1. Gets sales listings from the suburb
  2. Groups them by agent and agency
  3. Calculates total sales, values, and median prices
  4. Sorts and ranks agents by their performance

#### `get_agent_sales_metrics`
- **What it does**: A higher-level function to get comprehensive agent metrics
- **When used**: When a complete sales analysis is needed
- **How it works**: Combines multiple data queries to build a complete picture of agent performance

## How Domain Service Connects to Endpoints

### Endpoint: `/api/generate-agents-report`

When a user hits this endpoint:

1. **Controller function**: `generate_agents_report` in `main.py` is triggered
2. **Background task**: `process_agents_report_job` is started
3. **Domain service call**: This background task calls `fetch_property_data`
4. **Data processing**:
   - Agent data is fetched and processed by `domain_service.py`
   - If `home_owner_pricing` is provided, commission reports are generated
5. **PDF generation**: The processed data is passed to `generate_pdf_with_weasyprint`
6. **Dropbox upload**: The PDF is uploaded using `upload_to_dropbox`
7. **Result**: User gets a `job_id` to track progress

### The Data Flow for Agent Reports

```
API Request 
  → Background Task 
    → domain_service.fetch_property_data
      → get_agent_performance_metrics
        → search_sold_listings_by_suburb
      → check_featured_agent (for premium agents)
      → get_area_type (for commission calculations)
    → generate_pdf_with_weasyprint
    → upload_to_dropbox
  → Job Status Updates
```

## API Endpoints

### 1. `/api/generate-agents-report`
- **Purpose**: Generate a report of top agents in a suburb
- **Parameters**:
  - `suburb`: The suburb name (e.g., "Manly")
  - `state`: State code (e.g., "NSW")
  - `property_types`: List of property types to filter by
  - `min_bedrooms`/`max_bedrooms`: Bedroom range
  - `min_bathrooms`/`max_bathrooms`: Bathroom range
  - Others (see domain_service parameters)
- **Response**: Job ID to track the report generation progress
- **Backend Process**: Uses domain_service to fetch and process agent data

### 2. `/api/job-status/{job_id}`
- **Purpose**: Check the status of a report generation job
- **Parameters**:
  - `job_id`: The ID of the job to check
- **Response**: Job status (processing, completed, failed) and progress
- **Backend Process**: Checks the in-memory job tracking system

### 3. `/api/generate-property-report`
- **Purpose**: Generate a report about a specific property
- **Parameters**:
  - `property_id`: Domain.com.au property ID
- **Response**: Job ID to track the report generation progress
- **Backend Process**: Fetches property data and generates a PDF report

## Domain Service Special Features

### Featured Agent Detection

The service checks if agents have paid for featured status by calling the `check_featured_agent` function. Featured agents get special treatment:
- Prominent placement in reports
- Special styling (colored borders, "Featured Agent" label)
- Their commission rates may differ from standard rates

### Agent Deduplication

Many agents work across multiple branch offices of the same agency. The service has a sophisticated deduplication process that:
1. Identifies potential duplicates by agent name
2. Normalizes agency names (e.g., "Belle Property Dee Why" → "Belle Property")
3. Combines statistics from multiple branches into a single agent entry
4. Preserves the branch information

### Commission Calculation

For homeowner pricing reports, the service:
1. Gets the area type (suburb, rural, inner city)
2. Retrieves commission rates based on property price ranges
3. For featured agents, gets their specific rates from Make.com
4. Calculates potential discounts based on property values

## Typical Workflow Example

When someone wants to know about the top agents in Manly, NSW:

1. They make a request to `/api/generate-agents-report` with parameters:
   - suburb: "Manly"
   - state: "NSW" 
   - min_bedrooms: 2
   - property_types: ["House", "Apartment"]

2. A job is created and the backend starts working:
   - `domain_service.fetch_property_data` is called
   - It queries Domain.com.au for all sold properties in Manly matching the criteria
   - It identifies which agents sold those properties
   - It calculates how many sales each agent made and their total value
   - It checks if any agents in Manly have paid for featured status

3. The data is processed:
   - Agents are sorted by their sales performance
   - Duplicate agents are combined
   - Featured agents are highlighted
   - Photos and logos are added

4. A PDF report is generated showing:
   - Featured agents at the top with special styling
   - Each agent's photo and agency logo
   - Total sales, total value, and median sold price for each agent

5. The PDF is uploaded to Dropbox in the "/Suburbs Top Agents" folder

6. The user gets a link to download the PDF from Dropbox

This entire process happens asynchronously in the background, and the user can check the job status with the provided job ID until it's complete.

## Dependencies

The project relies on several key dependencies:

1. **FastAPI**: Web framework for building the API endpoints
2. **Uvicorn**: ASGI server for running the FastAPI application
3. **Dropbox SDK**: For interacting with Dropbox API
4. **WeasyPrint**: For converting HTML to PDF
5. **Jinja2**: For templating HTML reports
6. **Pydantic**: For data validation
7. **Requests**: For making HTTP requests to Domain.com.au API
8. **Python-dotenv**: For loading environment variables

## Environment Variables

The application requires several environment variables to be set in a `.env` file:

- **DOMAIN_API_KEY**: API key for Domain.com.au
- **DOMAIN_API_SECRET**: API secret for Domain.com.au
- **DROPBOX_ACCESS_TOKEN**: Access token for Dropbox API
- **DROPBOX_REFRESH_TOKEN**: Refresh token for Dropbox API
- **DROPBOX_APP_KEY**: App key for Dropbox API
- **DROPBOX_APP_SECRET**: App secret for Dropbox API
- **DROPBOX_ACCOUNT_ID**: Account ID for Dropbox

## Server Access

### SSH Connection

To connect to the production server, use the following SSH command:

```bash
ssh root@65.108.146.173
```

### Server Maintenance

- The application is deployed on a Linux server with the FastAPI application running behind Nginx
- Logs can be found in `/var/log/fastapi/`
- The application code is located in `/var/www/fastapi-app/AgentLink`
- Use `systemctl status fastapi` to check the application status
- Use `systemctl restart fastapi` to restart the application after code changes
