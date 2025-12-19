"""
Apify Property Scraper Testing Script

Purpose: Test 4 Apify scrapers for realestate.com.au to determine:
1. Which scraper can reliably detect sold/listed properties
2. Data quality and completeness
3. Performance and cost efficiency
4. Best option for tracking 20k+ properties

Scrapers to test:
1. Australian Property Listings Web Scraper - $50/month
2. Realestate.com.au Scraper (Iñigo Garcia) - $19/month
3. Property AU Scraper (ABot API) - $39/month (RECOMMENDED)
4. Aussie Scraper by ScrapeMind - $50/month

Author: Kunal Barve
Date: December 8, 2025
"""

import os
import json
import time
import csv
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import requests

# Install required packages:
# pip install apify-client pandas openpyxl

try:
    from apify_client import ApifyClient
    import pandas as pd
except ImportError:
    print("⚠️ Missing dependencies. Please install:")
    print("pip install apify-client pandas openpyxl")
    exit(1)


@dataclass
class PropertyTestResult:
    """Store test results for each property"""
    address: str
    suburb: str
    state: str
    postcode: Optional[str]
    scraper_name: str
    found: bool
    status: Optional[str]  # 'sold', 'listed', 'rented', 'unlisted'
    sold_date: Optional[str]
    listing_date: Optional[str]
    agent_name: Optional[str]
    agency_name: Optional[str]
    price: Optional[str]
    execution_time: float
    error: Optional[str]
    raw_data: Optional[Dict]


class ApifyScraperTester:
    """Test multiple Apify scrapers for property tracking"""
    
    def __init__(self, api_token: Optional[str] = None):
        """
        Initialize the tester with Apify API token
        
        Args:
            api_token: Apify API token (or set APIFY_API_TOKEN env var)
        """
        self.api_token = api_token or os.getenv('APIFY_API_TOKEN')
        if not self.api_token:
            raise ValueError(
                "Apify API token required. Set APIFY_API_TOKEN environment variable "
                "or pass it to the constructor."
            )
        
        self.client = ApifyClient(self.api_token)
        self.results: List[PropertyTestResult] = []
        
        # Scraper configurations
        self.scrapers = {
            'australian_property_listings': {
                'actor_id': 'YOUR_ACTOR_ID_HERE',  # Replace with actual actor ID
                'name': 'Australian Property Listings Web Scraper',
                'cost': '$50/month'
            },
            'realestate_inigo': {
                'actor_id': 'YOUR_ACTOR_ID_HERE',  # Replace with actual actor ID
                'name': 'Realestate.com.au Scraper (Iñigo Garcia)',
                'cost': '$19/month + usage'
            },
            'property_au_abot': {
                'actor_id': 'YOUR_ACTOR_ID_HERE',  # Replace with actual actor ID
                'name': 'Property AU Scraper (ABot API)',
                'cost': '$39/month'
            },
            'aussie_scrapemind': {
                'actor_id': 'YOUR_ACTOR_ID_HERE',  # Replace with actual actor ID
                'name': 'Aussie Scraper by ScrapeMind',
                'cost': '$50/month'
            }
        }
    
    def load_test_properties(self, file_path: str) -> List[Dict[str, str]]:
        """
        Load test properties from CSV/Excel file
        
        Args:
            file_path: Path to CSV or Excel file with property addresses
            
        Returns:
            List of property dictionaries
        """
        print(f"📂 Loading properties from {file_path}...")
        
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_path.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file_path)
        else:
            raise ValueError("File must be CSV or Excel format")
        
        # Expected columns: address, suburb, state, postcode (optional)
        required_cols = ['address', 'suburb', 'state']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
        
        properties = df.to_dict('records')
        print(f"✅ Loaded {len(properties)} properties")
        return properties
    
    def test_australian_property_listings(self, property_data: Dict) -> PropertyTestResult:
        """Test Australian Property Listings Web Scraper"""
        start_time = time.time()
        scraper_name = self.scrapers['australian_property_listings']['name']
        
        try:
            # Configure actor input
            run_input = {
                "suburb": property_data['suburb'],
                "state": property_data['state'],
                "listing_type": "sold",  # Test sold properties
                "max_results": 100
            }
            
            # Run the actor
            print(f"  🔍 Testing {property_data['suburb']}, {property_data['state']}...")
            run = self.client.actor(self.scrapers['australian_property_listings']['actor_id']).call(
                run_input=run_input
            )
            
            # Get results
            items = list(self.client.dataset(run["defaultDatasetId"]).iterate_items())
            
            # Search for matching address
            matching_property = self._find_matching_property(
                items, 
                property_data['address']
            )
            
            execution_time = time.time() - start_time
            
            if matching_property:
                return PropertyTestResult(
                    address=property_data['address'],
                    suburb=property_data['suburb'],
                    state=property_data['state'],
                    postcode=property_data.get('postcode'),
                    scraper_name=scraper_name,
                    found=True,
                    status=matching_property.get('status', 'sold'),
                    sold_date=matching_property.get('soldDate'),
                    listing_date=matching_property.get('listingDate'),
                    agent_name=matching_property.get('agentName'),
                    agency_name=matching_property.get('agencyName'),
                    price=matching_property.get('price'),
                    execution_time=execution_time,
                    error=None,
                    raw_data=matching_property
                )
            else:
                return PropertyTestResult(
                    address=property_data['address'],
                    suburb=property_data['suburb'],
                    state=property_data['state'],
                    postcode=property_data.get('postcode'),
                    scraper_name=scraper_name,
                    found=False,
                    status=None,
                    sold_date=None,
                    listing_date=None,
                    agent_name=None,
                    agency_name=None,
                    price=None,
                    execution_time=execution_time,
                    error="Property not found in results",
                    raw_data=None
                )
                
        except Exception as e:
            execution_time = time.time() - start_time
            return PropertyTestResult(
                address=property_data['address'],
                suburb=property_data['suburb'],
                state=property_data['state'],
                postcode=property_data.get('postcode'),
                scraper_name=scraper_name,
                found=False,
                status=None,
                sold_date=None,
                listing_date=None,
                agent_name=None,
                agency_name=None,
                price=None,
                execution_time=execution_time,
                error=str(e),
                raw_data=None
            )
    
    def test_realestate_inigo(self, property_data: Dict) -> PropertyTestResult:
        """Test Realestate.com.au Scraper by Iñigo Garcia"""
        start_time = time.time()
        scraper_name = self.scrapers['realestate_inigo']['name']
        
        try:
            # Configure actor input
            run_input = {
                "locations": [f"{property_data['suburb']}, {property_data['state']}"],
                "listing_type": "sold",
                "max_properties": 100
            }
            
            print(f"  🔍 Testing {property_data['suburb']}, {property_data['state']}...")
            run = self.client.actor(self.scrapers['realestate_inigo']['actor_id']).call(
                run_input=run_input
            )
            
            items = list(self.client.dataset(run["defaultDatasetId"]).iterate_items())
            matching_property = self._find_matching_property(items, property_data['address'])
            
            execution_time = time.time() - start_time
            
            if matching_property:
                return PropertyTestResult(
                    address=property_data['address'],
                    suburb=property_data['suburb'],
                    state=property_data['state'],
                    postcode=property_data.get('postcode'),
                    scraper_name=scraper_name,
                    found=True,
                    status='sold',
                    sold_date=matching_property.get('soldDate'),
                    listing_date=matching_property.get('listedDate'),
                    agent_name=matching_property.get('agent'),
                    agency_name=matching_property.get('agency'),
                    price=matching_property.get('price'),
                    execution_time=execution_time,
                    error=None,
                    raw_data=matching_property
                )
            else:
                return self._create_not_found_result(
                    property_data, scraper_name, execution_time
                )
                
        except Exception as e:
            return self._create_error_result(
                property_data, scraper_name, time.time() - start_time, str(e)
            )
    
    def test_property_au_abot(self, property_data: Dict) -> PropertyTestResult:
        """Test Property AU Scraper (ABot API) - RECOMMENDED"""
        start_time = time.time()
        scraper_name = self.scrapers['property_au_abot']['name']
        
        try:
            # This scraper supports direct property URL or suburb search
            run_input = {
                "search_type": "suburb",
                "suburb": property_data['suburb'],
                "state": property_data['state'],
                "listing_type": "sold",
                "include_history": True,  # Get property history
                "max_results": 100
            }
            
            print(f"  🔍 Testing {property_data['suburb']}, {property_data['state']}...")
            run = self.client.actor(self.scrapers['property_au_abot']['actor_id']).call(
                run_input=run_input
            )
            
            items = list(self.client.dataset(run["defaultDatasetId"]).iterate_items())
            matching_property = self._find_matching_property(items, property_data['address'])
            
            execution_time = time.time() - start_time
            
            if matching_property:
                return PropertyTestResult(
                    address=property_data['address'],
                    suburb=property_data['suburb'],
                    state=property_data['state'],
                    postcode=property_data.get('postcode'),
                    scraper_name=scraper_name,
                    found=True,
                    status=matching_property.get('propertyStatus', 'sold'),
                    sold_date=matching_property.get('soldDate'),
                    listing_date=matching_property.get('firstListedDate'),
                    agent_name=matching_property.get('primaryAgent'),
                    agency_name=matching_property.get('agency'),
                    price=matching_property.get('soldPrice'),
                    execution_time=execution_time,
                    error=None,
                    raw_data=matching_property
                )
            else:
                return self._create_not_found_result(
                    property_data, scraper_name, execution_time
                )
                
        except Exception as e:
            return self._create_error_result(
                property_data, scraper_name, time.time() - start_time, str(e)
            )
    
    def test_aussie_scrapemind(self, property_data: Dict) -> PropertyTestResult:
        """Test Aussie Scraper by ScrapeMind"""
        start_time = time.time()
        scraper_name = self.scrapers['aussie_scrapemind']['name']
        
        try:
            run_input = {
                "suburb": property_data['suburb'],
                "state": property_data['state'],
                "category": "sold",
                "maxListings": 100
            }
            
            print(f"  🔍 Testing {property_data['suburb']}, {property_data['state']}...")
            run = self.client.actor(self.scrapers['aussie_scrapemind']['actor_id']).call(
                run_input=run_input
            )
            
            items = list(self.client.dataset(run["defaultDatasetId"]).iterate_items())
            matching_property = self._find_matching_property(items, property_data['address'])
            
            execution_time = time.time() - start_time
            
            if matching_property:
                return PropertyTestResult(
                    address=property_data['address'],
                    suburb=property_data['suburb'],
                    state=property_data['state'],
                    postcode=property_data.get('postcode'),
                    scraper_name=scraper_name,
                    found=True,
                    status='sold',
                    sold_date=matching_property.get('dateSold'),
                    listing_date=matching_property.get('dateListed'),
                    agent_name=matching_property.get('agentName'),
                    agency_name=matching_property.get('agencyName'),
                    price=matching_property.get('soldPrice'),
                    execution_time=execution_time,
                    error=None,
                    raw_data=matching_property
                )
            else:
                return self._create_not_found_result(
                    property_data, scraper_name, execution_time
                )
                
        except Exception as e:
            return self._create_error_result(
                property_data, scraper_name, time.time() - start_time, str(e)
            )
    
    def _find_matching_property(self, items: List[Dict], address: str) -> Optional[Dict]:
        """
        Find property in results that matches the given address
        
        Args:
            items: List of property dictionaries from scraper
            address: Address to match
            
        Returns:
            Matching property dict or None
        """
        address_lower = address.lower().strip()
        
        for item in items:
            # Try different address field names
            item_address = (
                item.get('address') or 
                item.get('fullAddress') or 
                item.get('streetAddress') or 
                ''
            ).lower().strip()
            
            # Simple fuzzy matching - can be improved
            if address_lower in item_address or item_address in address_lower:
                return item
        
        return None
    
    def _create_not_found_result(
        self, 
        property_data: Dict, 
        scraper_name: str, 
        execution_time: float
    ) -> PropertyTestResult:
        """Helper to create a 'not found' result"""
        return PropertyTestResult(
            address=property_data['address'],
            suburb=property_data['suburb'],
            state=property_data['state'],
            postcode=property_data.get('postcode'),
            scraper_name=scraper_name,
            found=False,
            status=None,
            sold_date=None,
            listing_date=None,
            agent_name=None,
            agency_name=None,
            price=None,
            execution_time=execution_time,
            error="Property not found in results",
            raw_data=None
        )
    
    def _create_error_result(
        self, 
        property_data: Dict, 
        scraper_name: str, 
        execution_time: float,
        error: str
    ) -> PropertyTestResult:
        """Helper to create an error result"""
        return PropertyTestResult(
            address=property_data['address'],
            suburb=property_data['suburb'],
            state=property_data['state'],
            postcode=property_data.get('postcode'),
            scraper_name=scraper_name,
            found=False,
            status=None,
            sold_date=None,
            listing_date=None,
            agent_name=None,
            agency_name=None,
            price=None,
            execution_time=execution_time,
            error=error,
            raw_data=None
        )
    
    def run_tests(
        self, 
        properties: List[Dict], 
        scrapers_to_test: Optional[List[str]] = None,
        sample_size: Optional[int] = None
    ):
        """
        Run tests on all scrapers with given properties
        
        Args:
            properties: List of property dictionaries to test
            scrapers_to_test: List of scraper keys to test (default: all)
            sample_size: Number of properties to test (default: all)
        """
        if sample_size:
            properties = properties[:sample_size]
        
        if not scrapers_to_test:
            scrapers_to_test = list(self.scrapers.keys())
        
        print(f"\n🚀 Starting tests on {len(properties)} properties...")
        print(f"📊 Testing scrapers: {', '.join(scrapers_to_test)}\n")
        
        for prop in properties:
            print(f"\n{'='*60}")
            print(f"Testing: {prop['address']}, {prop['suburb']}, {prop['state']}")
            print(f"{'='*60}")
            
            for scraper_key in scrapers_to_test:
                scraper_info = self.scrapers[scraper_key]
                print(f"\n🤖 {scraper_info['name']} ({scraper_info['cost']})")
                
                # Call appropriate test method
                if scraper_key == 'australian_property_listings':
                    result = self.test_australian_property_listings(prop)
                elif scraper_key == 'realestate_inigo':
                    result = self.test_realestate_inigo(prop)
                elif scraper_key == 'property_au_abot':
                    result = self.test_property_au_abot(prop)
                elif scraper_key == 'aussie_scrapemind':
                    result = self.test_aussie_scrapemind(prop)
                
                self.results.append(result)
                
                # Print result
                if result.found:
                    print(f"  ✅ FOUND - Status: {result.status}")
                    print(f"  📅 Sold: {result.sold_date}, Listed: {result.listing_date}")
                    print(f"  👤 Agent: {result.agent_name} ({result.agency_name})")
                    print(f"  💰 Price: {result.price}")
                else:
                    print(f"  ❌ NOT FOUND")
                    if result.error:
                        print(f"  ⚠️ Error: {result.error}")
                
                print(f"  ⏱️ Time: {result.execution_time:.2f}s")
                
                # Rate limiting - be respectful
                time.sleep(2)
    
    def generate_report(self, output_file: str = 'scraper_test_report.csv'):
        """
        Generate comprehensive test report
        
        Args:
            output_file: Path to save CSV report
        """
        if not self.results:
            print("⚠️ No results to report")
            return
        
        # Convert results to DataFrame
        df = pd.DataFrame([asdict(r) for r in self.results])
        
        # Save to CSV (without raw_data column for readability)
        df_export = df.drop(columns=['raw_data'])
        df_export.to_csv(output_file, index=False)
        print(f"\n📄 Report saved to {output_file}")
        
        # Generate summary statistics
        print("\n" + "="*60)
        print("📊 TEST SUMMARY")
        print("="*60)
        
        for scraper_key, scraper_info in self.scrapers.items():
            scraper_results = df[df['scraper_name'] == scraper_info['name']]
            
            if len(scraper_results) == 0:
                continue
            
            print(f"\n🤖 {scraper_info['name']}")
            print(f"   Cost: {scraper_info['cost']}")
            print(f"   Properties tested: {len(scraper_results)}")
            print(f"   Found: {scraper_results['found'].sum()} ({scraper_results['found'].sum()/len(scraper_results)*100:.1f}%)")
            print(f"   Avg execution time: {scraper_results['execution_time'].mean():.2f}s")
            print(f"   Errors: {scraper_results['error'].notna().sum()}")
            
            # Check data completeness
            if scraper_results['found'].sum() > 0:
                found_results = scraper_results[scraper_results['found']]
                print(f"   Data completeness:")
                print(f"     - Sold date: {found_results['sold_date'].notna().sum()}/{len(found_results)}")
                print(f"     - Agent name: {found_results['agent_name'].notna().sum()}/{len(found_results)}")
                print(f"     - Agency name: {found_results['agency_name'].notna().sum()}/{len(found_results)}")
        
        # Recommendation
        print("\n" + "="*60)
        print("💡 RECOMMENDATION")
        print("="*60)
        
        # Calculate scores (you can adjust weights)
        recommendations = []
        for scraper_key, scraper_info in self.scrapers.items():
            scraper_results = df[df['scraper_name'] == scraper_info['name']]
            
            if len(scraper_results) == 0:
                continue
            
            score = (
                scraper_results['found'].sum() / len(scraper_results) * 50 +  # 50% weight on success rate
                (1 - scraper_results['execution_time'].mean() / 60) * 25 +  # 25% weight on speed
                (scraper_results[scraper_results['found']]['agent_name'].notna().sum() / 
                 max(scraper_results['found'].sum(), 1)) * 25  # 25% weight on data completeness
            )
            
            recommendations.append({
                'name': scraper_info['name'],
                'cost': scraper_info['cost'],
                'score': score,
                'success_rate': scraper_results['found'].sum() / len(scraper_results) * 100
            })
        
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        
        if recommendations:
            best = recommendations[0]
            print(f"\n🏆 Best performer: {best['name']}")
            print(f"   Success rate: {best['success_rate']:.1f}%")
            print(f"   Cost: {best['cost']}")
        
        print("\n" + "="*60)


def main():
    """Main execution function"""
    print("="*60)
    print("🏘️  APIFY PROPERTY SCRAPER TESTING")
    print("="*60)
    
    # Initialize tester
    # Set your API token: export APIFY_API_TOKEN="your_token_here"
    try:
        tester = ApifyScraperTester()
    except ValueError as e:
        print(f"\n❌ {e}")
        print("\nTo set your API token:")
        print("  Windows: $env:APIFY_API_TOKEN='your_token_here'")
        print("  Linux/Mac: export APIFY_API_TOKEN='your_token_here'")
        return
    
    # Load test properties
    # TODO: Replace with actual path from Callum
    property_file = input("\n📂 Enter path to property file (CSV/Excel): ").strip()
    
    if not os.path.exists(property_file):
        print(f"❌ File not found: {property_file}")
        return
    
    properties = tester.load_test_properties(property_file)
    
    # Ask for sample size
    total_props = len(properties)
    sample_size = input(f"\n🔢 Test all {total_props} properties or enter sample size (default: 10): ").strip()
    
    if sample_size:
        try:
            sample_size = int(sample_size)
        except ValueError:
            sample_size = 10
    else:
        sample_size = min(10, total_props)
    
    # Ask which scrapers to test
    print("\n🤖 Available scrapers:")
    for i, (key, info) in enumerate(tester.scrapers.items(), 1):
        print(f"  {i}. {info['name']} ({info['cost']})")
    
    choice = input("\nTest all scrapers? (y/n, default: y): ").strip().lower()
    
    if choice == 'n':
        scraper_nums = input("Enter scraper numbers to test (e.g., 1,3,4): ").strip()
        scraper_keys = []
        for num in scraper_nums.split(','):
            try:
                idx = int(num.strip()) - 1
                scraper_keys.append(list(tester.scrapers.keys())[idx])
            except (ValueError, IndexError):
                pass
    else:
        scraper_keys = None  # Test all
    
    # Run tests
    tester.run_tests(properties, scraper_keys, sample_size)
    
    # Generate report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"scraper_test_report_{timestamp}.csv"
    tester.generate_report(report_file)
    
    print(f"\n✅ Testing complete!")
    print(f"📊 Review the report and share with Callum for decision.")


if __name__ == "__main__":
    main()
