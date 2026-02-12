#!/usr/bin/env python3
"""
Test script to verify district mapping fix
"""
import asyncio
import httpx
import json

async def test_query():
    """Test district query routing"""
    
    base_url = "http://localhost:8002"
    
    test_queries = [
        "Total candidates in Koshi?",
        "How many candidates in Sunsari?",
        "Count candidates in Sunseri?",
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Testing: {query}")
        print(f"{'='*60}")
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(
                    f"{base_url}/api/v1/chat",
                    json={"query": query},
                    headers={"Content-Type": "application/json"}
                )
                
                print(f"Status: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"Query Type: {result.get('query_type')}")
                    print(f"Intent: {result.get('intent')}")
                    print(f"Method: {result.get('method')}")
                    print(f"Answer: {result.get('answer', '')[:300]}...")
                    
                    metadata = result.get('metadata', {})
                    if 'results_count' in metadata:
                        print(f"Results Count: {metadata['results_count']}")
                    if 'operation' in metadata:
                        print(f"Operation: {metadata['operation']}")
                else:
                    print(f"Error: {response.text}")
                    
            except Exception as e:
                print(f"Exception: {e}")
    
    print(f"\n{'='*60}")
    print("Testing complete!")

if __name__ == "__main__":
    asyncio.run(test_query())
