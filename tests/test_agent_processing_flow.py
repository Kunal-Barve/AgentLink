import asyncio
import sys
import os
import json

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.domain_service import fetch_property_data

async def test_agent_processing_flow():
    """
    Test the complete agent processing flow with Wellington Point, QLD
    This will test:
    1. Fetching top agents from Domain.au
    2. Checking for featured agents from Google Sheet
    3. Proper prioritization (Featured Plus > Featured > Standard > Regular)
    4. Correct handling of manual vs automatic featured agents
    """
    print("=" * 80)
    print("TESTING COMPLETE AGENT PROCESSING FLOW")
    print("=" * 80)
    
    # Test with Wellington Point, QLD - where we know there's a featured agent
    test_params = {
        "property_id": "test-123",
        "suburb": "Wellington Point",
        "state": "QLD",
        "property_types": None,
        "min_bedrooms": 1,
        "max_bedrooms": None,
        "min_bathrooms": 1,
        "max_bathrooms": None,
        "min_carspaces": 1,
        "max_carspaces": None,
        "include_surrounding_suburbs": False,
        "post_code": "4160",
        "region": None,
        "area": None,
        "min_land_area": None,
        "max_land_area": None,
        "home_owner_pricing": "$1m-$1.5m"
    }
    
    print("\n" + "=" * 80)
    print("TEST PARAMETERS:")
    print("=" * 80)
    for key, value in test_params.items():
        print(f"  {key}: {value}")
    print("=" * 80)
    
    print("\n" + "=" * 80)
    print("EXECUTING fetch_property_data...")
    print("=" * 80)
    print("This will test the entire flow:")
    print("  1. Fetch agents from Domain.au")
    print("  2. Check for featured agents via webhook")
    print("  3. Process and prioritize agents")
    print("  4. Format top agents for report")
    print("-" * 80)
    
    try:
        result = await fetch_property_data(**test_params)
        
        print("\n" + "=" * 80)
        print("RESULTS:")
        print("=" * 80)
        
        if "top_agents" in result:
            top_agents = result["top_agents"]
            print(f"\n✓ Found {len(top_agents)} top agents")
            print("=" * 80)
            
            # Display each agent
            for idx, agent in enumerate(top_agents, 1):
                print(f"\n{'=' * 80}")
                print(f"AGENT #{idx}")
                print('=' * 80)
                print(f"  Name:               {agent.get('name', 'N/A')}")
                print(f"  Agency:             {agent.get('agency', 'N/A')}")
                print(f"  Total Sales:        {agent.get('total_sales', 0)}")
                print(f"  Median Sold Price:  {agent.get('median_sold_price', 'N/A')}")
                print(f"  Total Sales Value:  {agent.get('total_sales_value', 'N/A')}")
                print(f"  Featured:           {agent.get('featured', False)}")
                print(f"  Featured Plus:      {agent.get('featured_plus', False)}")
                print(f"  Commission Rate:    {agent.get('commission_rate', 'N/A')}")
                print(f"  Discount:           {agent.get('discount', 'N/A')}")
                print(f"  Marketing:          {agent.get('marketing', 'N/A')}")
                print(f"  Photo URL:          {agent.get('photo_url', 'N/A')[:50]}...")
                print(f"  Agency Logo URL:    {agent.get('agency_logo_url', 'N/A')[:50]}...")
                
                # Highlight priority
                if agent.get('featured_plus'):
                    print(f"\n  🌟 PRIORITY: FEATURED PLUS (Highest)")
                elif agent.get('featured'):
                    print(f"\n  ⭐ PRIORITY: FEATURED (High)")
                else:
                    print(f"\n  📊 PRIORITY: REGULAR/STANDARD")
            
            print("\n" + "=" * 80)
            print("AGENT PRIORITY VERIFICATION:")
            print("=" * 80)
            
            # Check if Stacey Ritson is in the top agents
            stacey_found = False
            stacey_position = None
            for idx, agent in enumerate(top_agents, 1):
                if "stacey" in agent.get('name', '').lower():
                    stacey_found = True
                    stacey_position = idx
                    break
            
            if stacey_found:
                print(f"✓ Stacey Ritson FOUND at position #{stacey_position}")
                if top_agents[stacey_position - 1].get('featured'):
                    print(f"✓ Stacey Ritson is correctly marked as FEATURED")
                else:
                    print(f"✗ WARNING: Stacey Ritson is NOT marked as featured!")
            else:
                print("✗ ERROR: Stacey Ritson NOT FOUND in top agents list!")
                print("   This is the BUG we were trying to fix!")
            
            # Check priority order
            print("\n" + "-" * 80)
            print("Priority Order Validation:")
            print("-" * 80)
            
            featured_plus_count = sum(1 for a in top_agents if a.get('featured_plus'))
            featured_count = sum(1 for a in top_agents if a.get('featured') and not a.get('featured_plus'))
            regular_count = len(top_agents) - featured_plus_count - featured_count
            
            print(f"  Featured Plus agents: {featured_plus_count}")
            print(f"  Featured agents:      {featured_count}")
            print(f"  Regular agents:       {regular_count}")
            
            # Verify order
            last_priority = 3  # 3=Featured Plus, 2=Featured, 1=Regular
            order_correct = True
            for agent in top_agents:
                if agent.get('featured_plus'):
                    current_priority = 3
                elif agent.get('featured'):
                    current_priority = 2
                else:
                    current_priority = 1
                
                if current_priority > last_priority:
                    order_correct = False
                    print(f"\n✗ Priority order violation detected!")
                    break
                last_priority = current_priority
            
            if order_correct:
                print(f"\n✓ Agent priority order is CORRECT")
            
        else:
            print("✗ No 'top_agents' found in result")
        
        # Print full result as JSON for debugging
        print("\n" + "=" * 80)
        print("FULL RESULT JSON:")
        print("=" * 80)
        result_copy = result.copy()
        if "top_agents" in result_copy:
            # Truncate URLs for readability
            for agent in result_copy["top_agents"]:
                if agent.get("photo_url") and len(agent["photo_url"]) > 50:
                    agent["photo_url"] = agent["photo_url"][:50] + "..."
                if agent.get("agency_logo_url") and len(agent["agency_logo_url"]) > 50:
                    agent["agency_logo_url"] = agent["agency_logo_url"][:50] + "..."
        
        print(json.dumps(result_copy, indent=2))
        
    except Exception as e:
        print(f"\n✗ ERROR during test execution:")
        print(f"  {type(e).__name__}: {str(e)}")
        import traceback
        print("\nFull traceback:")
        print(traceback.format_exc())
    
    print("\n" + "=" * 80)
    print("TEST COMPLETED")
    print("=" * 80)

if __name__ == "__main__":
    # Run the async test function
    asyncio.run(test_agent_processing_flow())
