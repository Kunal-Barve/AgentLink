import asyncio
import json
import os
import sys

# Add the parent directory to sys.path to ensure imports work correctly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the required functions from domain_service
from app.services.domain_service import (
    search_sold_listings_by_suburb,
    get_agent_sales_metrics,
    get_agent_performance_metrics,
    format_price
)

async def main():
    print("Starting Domain.com.au API test...")
    
    # Test the API with a suburb search
    suburb = "Deer Park"
    state = "VIC"
    print(f"Searching for sold listings in {suburb}...")
    
    # Test the new agent sales metrics function
    print("\n" + "="*50)
    print(f"Getting agent sales metrics for {suburb}...")
    sales_metrics = await get_agent_sales_metrics(suburb = suburb ,state = state)
    
    if sales_metrics:
        print(f"\nFound {len(sales_metrics)} agencies with sales in {suburb}")
        
        # Print summary of each agency and their top agents
        for agency_id, agency_data in sales_metrics.items():
            print(f"\nAgency: {agency_data['name']}")
            print(f"Logo URL: {agency_data['logoUrl']}")
            
            # Get agents sorted by number of properties sold
            agents = list(agency_data["agents"].values())
            agents.sort(key=lambda x: x["propertiesSold"], reverse=True)
            
            print(f"Top agents ({len(agents)} total):")
            for i, agent in enumerate(agents[:3]):  # Show top 3 agents
                print(f"  {i+1}. {agent['name']}")
                print(f"     Photo: {agent['photoUrl']}")
                print(f"     Properties Sold: {agent['propertiesSold']}")
                print(f"     Total Sales Value: {agent.get('formattedTotalValue', 'N/A')}")
                print(f"     Median Sale Price: {agent.get('formattedMedianPrice', 'N/A')}")
                print(f"     Average Sale Price: {agent.get('formattedAvgPrice', 'N/A')}")
    else:
        print(f"No sales metrics found for {suburb}")
    
    print("Domain.com.au API test completed")
    
    # Now test the agent performance metrics
    print("\n" + "="*50)
    print(f"Calculating agent performance metrics for {suburb}...")
    agencies_data = await get_agent_performance_metrics(suburb)
    
    if agencies_data:
        # Convert the nested dictionary structure to a flat list of agents for display
        agents_list = []
        for agency_id, agency_data in agencies_data.items():
            agency_name = agency_data['name']
            for agent_id, agent_data in agency_data['agents'].items():
                if agent_data['total_sales'] > 0:  # Only include agents with sales
                    # Add agency name to the agent data for display
                    agent_data['agency'] = agency_name
                    agents_list.append(agent_data)
        
        # Sort agents by total sales (descending)
        agents_list.sort(key=lambda x: x['total_sales'], reverse=True)
        # Print the full dictionary structure in a readable format
        print("\n" + "="*50)
        print("Full data structure (formatted):")
        print(json.dumps(agencies_data, indent=2, default=str))
        print(f"\nFound {len(agents_list)} agents with sales in {suburb}")
        print("\nTop agents by sales volume:")
        
        # Display top 5 agents or all if less than 5
        top_agents = agents_list[:5] if len(agents_list) > 5 else agents_list
        
        for i, agent in enumerate(top_agents):
            print(f"{i+1}. {agent['name']} ({agent['agency']})")
            # Use the combined sales count (primary + joint)
            print(f"   Total Sales: {agent['total_sales'] }")
            print(f"   Joint Sales: {agent.get('joint_sales', 0)}")  # Display joint sales count
            print(f"   Median Sold Price: {agent['median_sold_price']}")
            
            # Use the combined sales value for display
            combined_value = agent.get('total_sales_value_combined', 0)
            if combined_value > 0:
                formatted_combined = f"${combined_value/1000000:.1f}m" if combined_value >= 1000000 else f"${combined_value/1000:.0f}k"
            else:
                formatted_combined = "Not disclosed"
                
            print(f"   Total Sales Value: {formatted_combined}")
            print(f"   Joint Sales Value: {agent.get('joint_sales_value_formatted', '$0')}")  # Display joint sales value
            print(f"   Photo URL: {agent.get('photo', 'N/A')}")
            
            # Find the agency logo URL for this agent
            agency_name = agent['agency']
            agency_logo = "N/A"
            for agency_id, agency_data in agencies_data.items():
                if agency_data['name'] == agency_name:
                    agency_logo = agency_data.get('logo', 'N/A')
                    break
            
            print(f"   Agency Logo URL: {agency_logo}")
            print()
        
        
    else:
        print(f"No agent data found for {suburb}")
    
    print("Domain.com.au API test completed")
# Run the main function if this file is executed directly
if __name__ == "__main__":
    asyncio.run(main())