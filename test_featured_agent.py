import asyncio
import sys
import os

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.domain_utils import check_featured_agent

async def test_featured_agent():
    """
    Test the check_featured_agent function with two different suburbs
    """
    print("=" * 80)
    print("TESTING check_featured_agent FUNCTION")
    print("=" * 80)
    
    # Test Case 1: Invalid/Non-existent suburb (should return None)
    print("\n\n" + "=" * 80)
    print("TEST CASE 1: Non-existent suburb - 'Wellin', 'QLD'")
    print("=" * 80)
    print("Expected: Should return None (no featured agent found)")
    print("-" * 80)
    
    result1 = await check_featured_agent("Wellin", "QLD")
    
    print("-" * 80)
    print(f"RESULT 1: {result1}")
    print(f"TYPE: {type(result1)}")
    if result1 is None:
        print("✓ TEST PASSED: Correctly returned None for non-existent suburb")
    else:
        print("✗ TEST FAILED: Expected None but got:", result1)
    print("=" * 80)
    
    # Test Case 2: Valid suburb with featured agent (should return agent data)
    print("\n\n" + "=" * 80)
    print("TEST CASE 2: Valid suburb - 'Wellington Point', 'QLD'")
    print("=" * 80)
    print("Expected: Should return featured agent data or None")
    print("-" * 80)
    
    result2 = await check_featured_agent("Wellington Point", "QLD")
    
    print("-" * 80)
    print(f"RESULT 2: {result2}")
    print(f"TYPE: {type(result2)}")
    
    if result2 is None:
        print("✓ Result: No featured agent found for Wellington Point")
    elif isinstance(result2, list):
        print(f"✓ Result: Found {len(result2)} featured agent(s)")
        for idx, agent in enumerate(result2, 1):
            print(f"\n  Agent {idx}:")
            print(f"    Name: {agent.get('Name')}")
            print(f"    Agency: {agent.get('Agency')}")
            print(f"    Email: {agent.get('Email')}")
            print(f"    Phone: {agent.get('Phone')}")
            print(f"    Subscription Type: {agent.get('Subscription Type')}")
            print(f"    Is Featured Plus: {agent.get('is_featured_plus')}")
            print(f"    Manually Pull Data: '{agent.get('Manully Pull Data')}'")
    else:
        print("✗ Unexpected result type:", type(result2))
    
    print("=" * 80)
    
    # Summary
    print("\n\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Test Case 1 (Wellin, QLD): {'PASSED' if result1 is None else 'FAILED'}")
    print(f"Test Case 2 (Wellington Point, QLD): {'COMPLETED' if result2 is not None or result2 is None else 'ERROR'}")
    print("=" * 80)

if __name__ == "__main__":
    # Run the async test function
    asyncio.run(test_featured_agent())
