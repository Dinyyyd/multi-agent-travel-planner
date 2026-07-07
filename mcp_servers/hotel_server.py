from mcp.server.fastmcp import FastMCP
import requests
from typing import Optional

# The MCP server — a standalone program that holds the hotel tools
# and waits for a client to call them.
mcp = FastMCP("hotel-service")

HOTEL_API_BASE = "https://standing-fish-574.convex.site/hotels"


def _fetch_json(url: str, params: Optional[dict] = None):
    try:
        response = requests.get(url, params=params)
        return response.json()
    except Exception:
        return None


@mcp.tool()
def get_hotels() -> list[dict]:
    """Get a list of all available hotels. Use when the user asks to show/list all hotels."""
    data = _fetch_json(HOTEL_API_BASE)
    if isinstance(data, dict):
        return data.get("hotels", [])
    return []


@mcp.tool()
def search_hotel(city: str, checkIn: Optional[str] = None, checkOut: Optional[str] = None) -> list[dict]:
    """Search hotels by city and optional check-in/check-out dates (YYYY-MM-DD)."""
    params = {"city": city}
    if checkIn:
        params["checkIn"] = checkIn
    if checkOut:
        params["checkOut"] = checkOut
    data = _fetch_json(f"{HOTEL_API_BASE}/search", params=params)
    if isinstance(data, dict):
        return data.get("hotels", [])
    return []


@mcp.tool()
def book_hotel(hotel_id: str, guest_name: str, guest_email: str,
               check_in_date: str, check_out_date: str, room_type: str) -> dict:
    """Book a hotel room. Requires hotel_id, guest_name, guest_email, dates (YYYY-MM-DD), room_type."""
    payload = {
        "hotelId": hotel_id, "guestName": guest_name, "guestEmail": guest_email,
        "checkInDate": check_in_date, "checkOutDate": check_out_date, "roomType": room_type,
    }
    response = requests.post(f"{HOTEL_API_BASE}/book", json=payload)
    return response.json()


if __name__ == "__main__":
    mcp.run(transport="stdio")