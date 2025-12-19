# Property Tracker Implementation - Task Breakdown

**Project Goal**: Build a scalable property tracking system to monitor 20,000+ properties for listing/sold status without using Domain's expensive API service.

---

## 📋 Main Task 1: Property Tracker Research & Feasibility

**Status**: In Progress  
**Owner**: Kunal  
**Deadline**: TBD

### Sub-tasks:

- [ ] **1.1 Test Apify Scrapers**
  - Test 4 identified scrapers with sample property data
  - Verify they can detect sold vs listed status
  - Check data accuracy and completeness
  - Document API rate limits and reliability
  
- [ ] **1.2 Data Requirements Analysis**
  - Confirm required fields: listing date, sold date, agent name, agency name
  - Verify realestate.com.au as primary data source
  - Document data format and standardization needs
  
- [ ] **1.3 Cost Analysis**
  - Compare 4 scraper options (pricing included below)
  - Calculate monthly cost for 20k properties
  - Compare with Domain's service cost
  - Provide recommendation to Callum
  
- [ ] **1.4 Scalability Testing**
  - Test with batch sizes (1k properties per day)
  - Measure scraping time and success rate
  - Identify potential bottlenecks
  - Document error handling requirements

### Apify Scraper Options:

1. **Australian Property Listings Web Scraper** - $50/month
2. **Realestate.com.au Scraper (Iñigo Garcia)** - $19/month + usage fees
3. **Property AU Scraper (ABot API)** - $39/month (RECOMMENDED - most detailed)
4. **Aussie Scraper by ScrapeMind** - $50/month

---

## 📋 Main Task 2: Property Tracker System Design

**Status**: Not Started  
**Owner**: Kunal  
**Dependencies**: Task 1 completion

### Sub-tasks:

- [ ] **2.1 Database Schema Design**
  - Design property table structure
  - Include: address, suburb, postcode, state, status, dates, agent info
  - Add tracking metadata (last_checked, check_frequency, etc.)
  - Design for 20k+ properties with efficient querying
  
- [ ] **2.2 Batch Processing Logic**
  - Design daily batch system (1k properties/day)
  - Implement rotating queue (Day 1: rows 0-1000, Day 2: rows 1000-2000, etc.)
  - Handle 24-month property lifecycle (auto-archive old properties)
  - Design retry mechanism for failed checks
  
- [ ] **2.3 Notification System Design**
  - Define webhook/alert structure for status changes
  - Design notification payload (property details, old status → new status)
  - Determine notification channels (email, webhook, database flag)
  
- [ ] **2.4 Architecture Decision**
  - Choose: Google Sheets vs Database (PostgreSQL/MySQL)
  - Design data flow: Scraper → Processing → Storage → Notifications
  - Plan for N8N integration

---

## 📋 Main Task 3: Property Tracker Implementation

**Status**: Not Started  
**Owner**: Kunal  
**Dependencies**: Task 2 completion

### Sub-tasks:

- [ ] **3.1 Core Scraper Integration**
  - Integrate selected Apify scraper
  - Implement API authentication and error handling
  - Build property lookup function
  - Handle rate limits and retries
  
- [ ] **3.2 Data Storage Implementation**
  - Set up database/Google Sheets structure
  - Implement CRUD operations
  - Add indexing for efficient queries
  - Build data validation layer
  
- [ ] **3.3 Batch Processing Service**
  - Build daily batch processor
  - Implement queue management
  - Add logging and monitoring
  - Handle concurrent requests if needed
  
- [ ] **3.4 Status Change Detection**
  - Implement comparison logic (old status vs new status)
  - Trigger notifications on changes
  - Log all status transitions
  - Handle edge cases (unlisted → relisted, etc.)

---

## 📋 Main Task 4: Address Standardization & Validation

**Status**: Not Started  
**Owner**: Kunal  
**Dependencies**: Domain address API access

### Sub-tasks:

- [ ] **4.1 Domain Address API Integration**
  - Integrate Domain's free address autocomplete API
  - Build address validation function
  - Implement address standardization
  
- [ ] **4.2 Postcode Integration**
  - Add postcode field to all property records
  - Build suburb + postcode + state matching
  - Handle duplicate suburb names across states
  - Validate existing 2380+ properties with postcodes
  
- [ ] **4.3 Address Cleanup Script**
  - Build script to standardize existing addresses
  - Format: Street, Suburb, State, Postcode
  - Remove duplicates and invalid entries
  - Flag properties needing manual review

---

## 📋 Main Task 5: Testing & Quality Assurance

**Status**: Not Started  
**Owner**: Kunal

### Sub-tasks:

- [ ] **5.1 Unit Testing**
  - Test scraper integration
  - Test data validation functions
  - Test batch processing logic
  - Test notification system
  
- [ ] **5.2 Integration Testing**
  - Test with 100 properties (sample)
  - Test with 1000 properties (batch)
  - Test status change detection accuracy
  - Test error recovery
  
- [ ] **5.3 Performance Testing**
  - Measure processing time for 1k properties
  - Test concurrent scraping if applicable
  - Identify and optimize bottlenecks
  - Document system limits
  
- [ ] **5.4 User Acceptance Testing**
  - Run with Callum's 2380 property list
  - Verify data accuracy
  - Test notification system
  - Get Callum's approval

---

## 📋 Main Task 6: N8N Integration & Automation

**Status**: Not Started  
**Owner**: Kunal  
**Dependencies**: Task 3 completion

### Sub-tasks:

- [ ] **6.1 N8N Workflow Design**
  - Design automated daily workflow
  - Integrate with property tracker API/service
  - Add error handling and retries
  
- [ ] **6.2 Notification Workflows**
  - Send alerts to Callum/team on status changes
  - Format notification emails with property details
  - Log all notifications
  
- [ ] **6.3 Manual Trigger Workflows**
  - Build on-demand property check workflow
  - Build bulk property import workflow
  - Build reporting workflow

---

## 📋 Main Task 7: Documentation & Handover

**Status**: Not Started  
**Owner**: Kunal

### Sub-tasks:

- [ ] **7.1 Technical Documentation**
  - Document system architecture
  - Document API integrations
  - Document database schema
  - Create troubleshooting guide
  
- [ ] **7.2 User Guide**
  - Create guide for adding new properties
  - Create guide for viewing tracking status
  - Create guide for managing notifications
  
- [ ] **7.3 Maintenance Guide**
  - Document backup procedures
  - Document scaling procedures (10k → 20k)
  - Document cost monitoring
  - Create runbook for common issues

---

## 📊 Current Understanding & Next Steps

### Your Understanding ✅ (Correct):
- Callum has ~2,500 properties currently (scaling to 20k)
- Need to check if properties are sold or listed
- Using Apify scrapers as the solution
- Need property list from Callum to test

### Immediate Next Steps:

1. **Create `apify_scraper_testing.py`** - Test scrapers with sample data
2. **Request property list from Callum** - Get the Google Sheet with 2380+ properties
3. **Run tests on all 4 scrapers** - Document results
4. **Provide cost/feasibility report to Callum** - Include recommendation

### Key Requirements from Meeting:

- ✅ Track up to 20,000 properties (eventually)
- ✅ Check 1,000 properties per day (batch processing)
- ✅ Track for 24 months max (then archive)
- ✅ Data needed: listing date, sold date, agent, agency
- ✅ Source: realestate.com.au (not Domain)
- ✅ Must handle duplicate suburb names (need postcodes)
- ✅ Cost must be cheaper than Domain's service

---

## 📝 Notes & Questions for Callum

- [ ] Share Google Sheet with 2380+ property addresses
- [ ] Confirm preferred notification method (email, webhook, dashboard)
- [ ] Confirm budget range for monthly scraper costs
- [ ] Provide Domain address API credentials
- [ ] Clarify priority: speed vs cost vs data richness

---

**Last Updated**: December 8, 2025  
**Next Review**: After Task 1 completion
