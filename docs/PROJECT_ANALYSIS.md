# AgentLink Project - Comprehensive Analysis

## Project Overview

**AgentLink** is a FastAPI-based real estate analytics platform that generates professional PDF reports about top-performing real estate agents and agencies in Australian suburbs. The system integrates with:
- **Domain.com.au API** - Australia's leading property marketplace
- **Dropbox API** - Cloud storage for generated reports
- **Make.com Webhooks** - Dynamic commission calculations and featured agent management

---

## 🏗️ System Architecture

### Technology Stack
- **Backend Framework**: FastAPI (Python 3.11)
- **Web Server**: Gunicorn + Uvicorn workers
- **Reverse Proxy**: Nginx (configured for SSL)
- **PDF Generation**: WeasyPrint (HTML to PDF conversion)
- **Template Engine**: Jinja2
- **Containerization**: Docker + Docker Compose
- **Cloud Storage**: Dropbox API
- **External APIs**: Domain.com.au, Make.com webhooks

### Deployment
- **Server IP**: 65.108.146.173
- **Container**: Docker-based deployment
- **Ports**: 
  - Application: 8000 (internal)
  - Nginx: 80 (HTTP), 443 (HTTPS)

---

## 📁 Project Structure

```
Make-Integration/
├── app/
│   ├── main.py                    # FastAPI application entry point
│   ├── services/                  # Business logic layer
│   │   ├── domain_service.py      # Domain.com.au integration (agents)
│   │   ├── domain_agency_service.py # Domain.com.au integration (agencies)
│   │   ├── agent_commission.py    # Commission calculation logic
│   │   ├── domain_utils.py        # Utility functions for Domain API
│   │   ├── dropbox_service.py     # Dropbox upload & OAuth management
│   │   └── html_pdf_service.py    # PDF generation using WeasyPrint
│   ├── templates/                 # HTML templates for PDF reports
│   │   ├── agents_report.html     # Top agents in suburb
│   │   ├── agency_report.html     # Top rental agencies
│   │   ├── commission_report.html # Commission rates report
│   │   ├── not_found.html         # No results fallback
│   │   └── property_report.html   # Individual property report
│   ├── assets/                    # Images and fonts
│   └── data/                      # Job tracking data
├── docker-compose.yml             # Container orchestration
├── Dockerfile                     # Application container config
├── requirements.txt               # Python dependencies
├── .env                          # Environment variables (API keys)
└── documentation.md              # Original project documentation
```

---

## 🔄 Core Workflows

### 1. **Generate Agents Report** (`/api/generate-agents-report`)

**Flow:**
1. User submits request with suburb and filters (bedrooms, bathrooms, property types, etc.)
2. System creates background job with unique `job_id`
3. **Domain Service** queries Domain.com.au API for sold properties in the suburb (last 12 months)
4. Processes sold listings to extract agent performance metrics:
   - Total sales count (primary + joint sales)
   - Total sales value
   - Median sold price
   - Agency affiliations
5. **Agent Deduplication**: Removes duplicate entries when agents appear across multiple branch offices
6. **Featured Agent Check**: Calls Make.com webhook to identify premium/featured agents
7. **Commission Calculation**: 
   - For featured agents: retrieves custom rates from Make.com
   - For standard agents: applies area-based rates (suburb/rural/inner_city)
8. **Agent Prioritization**:
   - Featured agents (top priority)
   - Standard subscription agents
   - Regular agents (sorted by sales volume)
9. **PDF Generation**: Renders `agents_report.html` with agent data
10. **Dropbox Upload**: Uploads to `/Suburbs Top Agents` folder
11. Returns shareable Dropbox link

**Commission Report (if `home_owner_pricing` provided):**
- Generates separate commission PDF
- Shows commission rates, marketing costs, and potential discounts
- Uploads to `/Commission Rate` folder

---

### 2. **Generate Agency Report** (`/api/generate-agency-report`)

**Flow:**
1. User submits request with suburb and filters
2. **Domain Agency Service** queries rental listings in the suburb
3. Counts rental listings per agency
4. Fetches agency addresses from Domain API
5. Sorts agencies by number of rental listings
6. Generates PDF with top 5 rental agencies
7. Uploads to `/Suburbs Top Rental Agencies` folder

---

### 3. **Job Status Tracking** (`/api/job-status/{job_id}`)

**Status Progression:**
- `processing` (10%)
- `fetching_agents_data` / `fetching_agency_data` (30%)
- `generating_commission_pdf` (45%)
- `generating_pdf` (60%)
- `uploading_to_dropbox` (85%)
- `completed` (100%)
- `failed` (0%)

Returns:
- Current status
- Progress percentage
- Dropbox URLs (when completed)
- Error messages (if failed)

---

## 🔌 External API Integrations

### 1. **Domain.com.au API**

**Purpose**: Fetch real estate data
**Authentication**: API Key in header (`X-Api-Key`)

**Key Endpoints Used:**
- `POST /v1/listings/residential/_search` - Search sold/rental listings
- `GET /v1/agencies/{agency_id}` - Get agency details
- `GET /v1/agents/search` - Search for agents

**Search Parameters:**
- Location: suburb, state, postcode, region
- Property types: House, Apartment, Townhouse, etc. (35+ types)
- Filters: bedrooms, bathrooms, carspaces, land area
- Date range: Last 12 months
- Listing type: Sold or Rent

---

### 2. **Make.com Webhooks**

**a) Featured Agent Lookup**
- **URL**: `https://hook.eu2.make.com/nuedlxjy6fsn398sa31tfh1ca6sgycda`
- **Method**: POST
- **Payload**: `{"suburb": "...", "state": "..."}`
- **Returns**: List of featured agents with subscription types (Featured/Featured Plus)

**b) Featured Agent Commission**
- **URL**: `https://hook.eu2.make.com/4d6cv0gxrw8aok5becjj1odpb55mpiqw`
- **Method**: GET
- **Params**: `agent_name`, `suburb`, `state_code`
- **Returns**: Custom commission rates and marketing costs by price range

**c) Standard Agent Commission**
- **URL**: `https://hook.eu2.make.com/wrkwzgqpensv34xlw14mcuzzcu79ohs9`
- **Method**: GET
- **Params**: `state_code`, `home_owner_pricing`
- **Returns**: Standard commission rates by state and price range

**d) Area Type Determination**
- **URL**: `https://hook.eu2.make.com/vq5xn04nnc9iio7nzjnkwu6ahkbtlizp`
- **Method**: GET
- **Params**: `post_code`, `suburb`
- **Returns**: Area classification (0=suburb, 1=inner_city, 2=suburb, 3=rural)

**e) Standard Subscription Check**
- **URL**: `https://hook.eu2.make.com/gne36wgwoje49c54gwrz8lnf749mxw3e`
- **Method**: POST
- **Payload**: `{"agent_name": "...", "suburb": "...", "state": "..."}`
- **Returns**: Boolean indicating standard subscription status

---

### 3. **Dropbox API**

**Purpose**: Store and share generated PDF reports

**Authentication**: OAuth 2.0 with refresh token
- Access tokens auto-refresh when expired
- Account verification on startup

**Upload Strategy:**
- Different folders for different report types
- Generates shareable links (preview mode)
- Automatic retry with token refresh on auth errors

---

## 💰 Commission Calculation Logic

### Price Ranges
- Less than $500k
- $500k-$1m
- $1m-$1.5m
- $1.5m-$2m
- $2m-$2.5m
- $2.5m-$3m
- $3m-$3.5m
- $3.5m-$4m
- $4m-$6m
- $6m-$8m
- $8m-$10m
- $10m+

### Area Type Rates

**Suburb (Default):**
- Commission: 1.98-2.20% (low range) to 1.25-1.50% (high range)
- Marketing: $6,000-$7,500 (low) to $10,000-$12,000 (high)

**Rural:**
- Commission: 2.25-2.75% (low) to 1.25-1.50% (high)
- Marketing: $2,000-$4,000 (low) to $7,000-$9,000+ (high)

**Inner City:**
- Commission: 1.75-2.10% (low) to 1.25-1.50% (high)
- Marketing: $6,000-$7,500 (low) to $10,000-$12,000 (high)

### Discount Calculation (Featured Agents)
Formula: `price × lowest_commission_rate × 20% × 30%`
- Rounded to nearest $500
- Only applies to featured agents

---

## 🎨 PDF Report Design

### Visual Design
- **A4 Landscape**: 1123px × 794px
- **Color Scheme**: Navy blue (#002366) branding
- **Layout**: 
  - Left: 59px navy strip with logo
  - Center: Content area with agent/agency data
  - Right: 400px beach/house imagery
- **Typography**: Montserrat font family

### Agent Report Features
- Agent photos (80px circular)
- Agency logos
- Performance metrics table:
  - Total Sales
  - Total Value
  - Median Sold Price
- Featured agent highlighting (red border + shadow)
- Featured Plus badge
- Up to 5 agents per report

### Commission Report Features
- Commission rate ranges
- Marketing cost estimates
- Discount calculations (featured agents)
- Price range-specific data
- Professional beach-house imagery

---

## 🔐 Environment Variables

```
DOMAIN_API_KEY=key_28cf...         # Domain.com.au API key
DOMAIN_API_SECRET=...              # Domain.com.au API secret

DROPBOX_APP_KEY=...                # Dropbox app key
DROPBOX_APP_SECRET=...             # Dropbox app secret
DROPBOX_ACCESS_TOKEN=...           # OAuth access token (auto-refreshes)
DROPBOX_REFRESH_TOKEN=...          # OAuth refresh token
DROPBOX_ACCOUNT_ID=...             # Dropbox account verification

INSTANCE_IP=65.108.146.173         # Production server IP
```

---

## 🚀 Deployment & Operations

### Docker Setup
```yaml
services:
  agentlink:
    build: .
    image: agentlink
    restart: always
    ports: ["8000:8000"]
    volumes:
      - ./app/templates:/app/app/templates
      - ./app/assets:/app/app/assets
  
  nginx:
    image: nginx:alpine
    ports: ["80:80", "443:443"]
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf
      - /etc/letsencrypt:/etc/letsencrypt
    depends_on: [agentlink]
```

### Application Startup
```bash
gunicorn -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 180 \
  app.main:app
```

### Logging
- Location: `/logs/` directory
- Format: Date-time stamped files (`ArticFlow_YYYY-MM-DD_HH-MM-SS.log`)
- Levels: INFO, WARNING, ERROR
- Handlers: File + Console

---

## 🎯 Key Features

### Agent Deduplication
Sophisticated algorithm that:
1. Groups agents by name (case-insensitive)
2. Normalizes agency names (handles branches)
3. Recognizes franchise patterns (Ray White, Belle Property, etc.)
4. Merges sales data across branches
5. Preserves branch information

### Agent Prioritization
1. **Featured Agents** (paid premium subscription)
2. **Standard Subscription** (paid standard tier)
3. **Regular Agents** (sorted by sales volume)

### Background Processing
- Asynchronous job processing
- In-memory job tracking
- Real-time status updates
- Automatic cleanup of temporary files

### Error Handling
- API retry logic with exponential backoff
- Token refresh on authentication errors
- Fallback to mock data when APIs fail
- Comprehensive error logging

---

## 📊 Data Flow Example

**User Request**: Generate agents report for "Manly, NSW"

```
1. POST /api/generate-agents-report
   ↓
2. Create job_id: "abc-123"
   ↓
3. Query Domain API for sold listings in Manly (last 12 months)
   ↓
4. Extract 150 listings with 25 unique agents
   ↓
5. Deduplicate → 20 unique agents
   ↓
6. Check Make.com → 1 featured agent found
   ↓
7. Calculate commission rates for featured agent
   ↓
8. Sort agents: 1 featured + 4 top performers
   ↓
9. Render agents_report.html with data
   ↓
10. Convert HTML → PDF using WeasyPrint
    ↓
11. Upload PDF to Dropbox: /Suburbs Top Agents/Manly_Top_Agents_abc-123.pdf
    ↓
12. Return shareable link: https://www.dropbox.com/s/...?dl=0
```

---

## 🔧 Technical Highlights

### Performance Optimizations
- Concurrent API calls where possible
- Caching of standard subscription checks
- Batch processing of agent data
- Efficient property type filtering

### Code Quality
- Modular service architecture
- Separation of concerns (API/service/presentation layers)
- Comprehensive logging
- Type hints with Pydantic models

### Scalability Considerations
- Background job processing
- Stateless API design (job data in memory - should migrate to Redis/DB)
- Docker containerization
- Nginx reverse proxy

---

## 🐛 Known Issues & Limitations

1. **Job Storage**: In-memory dictionary (lost on restart) - should use Redis or database
2. **No Authentication**: API endpoints are public
3. **Rate Limiting**: No built-in rate limiting for Domain API calls
4. **Concurrency**: Single worker process (could scale horizontally)
5. **Temporary Files**: Manual cleanup required (potential disk space issue)

---

## 🔮 Potential Improvements

1. **Database Integration**: PostgreSQL for job persistence
2. **Caching Layer**: Redis for API response caching
3. **Queue System**: Celery or RQ for better job management
4. **API Authentication**: JWT tokens or API keys
5. **Monitoring**: Prometheus + Grafana for metrics
6. **Testing**: Unit tests and integration tests
7. **API Documentation**: Swagger/OpenAPI integration
8. **Error Recovery**: Better retry mechanisms and circuit breakers
9. **Real-time Updates**: WebSocket for live job status updates
10. **Multi-region Support**: Beyond NSW (currently optimized for NSW)

---

## 📝 API Endpoint Summary

| Endpoint | Method | Purpose | Returns |
|----------|--------|---------|---------|
| `/api/generate-agents-report` | POST | Generate top agents PDF | job_id |
| `/api/generate-agency-report` | POST | Generate top agencies PDF | job_id |
| `/api/job-status/{job_id}` | GET | Check job progress | status, progress, URLs |

---

## 🎓 Business Logic Highlights

### How Featured Agents Work
- Featured agents are promoted in Make.com CRM
- Two tiers: "Featured" and "Featured Plus"
- Custom commission rates per agent
- Visual distinction in PDF (red border + badge)
- Always appear first in reports

### Property Type Handling
- API accepts 35+ property types
- User can filter to specific types
- Post-filtering applied after API response
- Ensures accurate agent metrics per property category

### Sales Attribution
- **Primary Sales**: Agent is first contact on listing
- **Joint Sales**: Agent is secondary contact
- Both counted in total, but tracked separately
- Median price calculated across all sales

---

## 💡 Understanding the Commission System

The commission system has three tiers:

1. **Featured Agent Rates** (Highest Priority)
   - Retrieved from Make.com webhook
   - Agent-specific rates
   - Includes discount calculations
   - Example: Agent gets 1.65-1.85% on $2m property

2. **State-Based Standard Rates** (Medium Priority)
   - Retrieved from Make.com webhook
   - State-specific rates (NSW, VIC, QLD, etc.)
   - Falls back if featured rates unavailable

3. **Area-Type Fallback Rates** (Lowest Priority)
   - Hardcoded in application
   - Based on area classification (suburb/rural/inner_city)
   - Used when webhooks fail

---

## 🌟 Unique Features

1. **Intelligent Agent Deduplication**: Handles agents working across multiple branch offices
2. **Dynamic Commission Rates**: Integration with Make.com for real-time rate updates
3. **Professional PDF Design**: A4 landscape layout with branding
4. **Background Processing**: Non-blocking report generation
5. **Flexible Filtering**: Multiple property and listing filters
6. **Auto-Token Refresh**: Seamless Dropbox authentication management

---

## 📈 Usage Statistics

Based on code analysis:
- **Search Window**: 12 months of historical data
- **Max Results**: 100 properties per API call
- **Agent Display**: Top 5 agents per report
- **Agency Display**: Top 5 agencies per report
- **PDF Size**: ~1123x794 pixels (A4 landscape)
- **Upload Folders**: 3 Dropbox folders for different report types

---

**Last Updated**: Analysis completed on 2025-10-11
**Analyzed By**: Cascade AI Assistant
**Project Status**: Production-ready, actively deployed
