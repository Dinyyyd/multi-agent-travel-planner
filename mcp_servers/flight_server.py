from mcp.server.fastmcp import FastMCP
import requests
from typing import Optional

mcp = FastMCP("flight-service")

FLIGHT_API_BASE = "https://standing-fish-574.convex.site/flights"


def _fetch_json(url: str, params: Optional[dict] = None):
    try:
        response = requests.get(url, params=params)
        return response.json()
    except Exception:
        return None


@mcp.tool()
def get_flights() -> list[dict]:
    """Get a list of all available flights. Use when the user asks to show/list all flights."""
    data = _fetch_json(FLIGHT_API_BASE)
    if isinstance(data, dict):
        return data.get("flights", [])
    return []


@mcp.tool()
def search_flights(origin: str, destination: str, date: Optional[str] = None) -> list[dict]:
    """Search flights by origin, destination, and optional date (YYYY-MM-DD). Use 3-letter codes like BOM, DEL."""
    if origin and len(origin) == 3 and origin.isalpha():
        origin = origin.upper()
    if destination and len(destination) == 3 and destination.isalpha():
        destination = destination.upper()

    params = {"origin": origin, "destination": destination}
    if date:
        params["date"] = date

    data = _fetch_json(f"{FLIGHT_API_BASE}/search", params=params)
    if isinstance(data, dict):
        return data.get("flights", [])
    return []


@mcp.tool()
def book_flight(flight_id: str, passenger_name: str, passenger_email: str) -> dict:
    """Book a flight ticket. Requires flight_id, passenger_name, passenger_email."""
    payload = {
        "flightId": flight_id,
        "passengerName": passenger_name,
        "passengerEmail": passenger_email,
    }
    response = requests.post(f"{FLIGHT_API_BASE}/book", json=payload)
    return response.json()


if __name__ == "__main__":
    mcp.run(transport="stdio")