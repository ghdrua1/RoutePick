"""walking 모드 테스트"""
import asyncio
import os
from dotenv import load_dotenv
import googlemaps

load_dotenv()

async def test_walking():
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    client = googlemaps.Client(key=api_key)
    
    # 경복궁 -> 남산타워
    origin = "37.5796,126.9770"
    dest = "37.5512,126.9882"
    
    print(f"Testing: {origin} -> {dest} (walking mode)")
    
    try:
        result = client.directions(
            origin=origin,
            destination=dest,
            mode="walking"
        )
        print(f"Result type: {type(result)}")
        print(f"Result length: {len(result) if result else 0}")
        if result and len(result) > 0:
            route = result[0]
            print(f"Routes: {len(route.get('legs', []))}")
            if route.get("legs"):
                leg = route["legs"][0]
                print(f"Duration: {leg.get('duration', {}).get('text')}")
                print(f"Distance: {leg.get('distance', {}).get('text')}")
        else:
            print("Empty result!")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_walking())

