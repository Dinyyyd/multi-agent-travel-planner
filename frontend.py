import json
import os
import time
from urllib.request import Request, urlopen
import gradio as gr

API_URL = os.environ.get("TRAVEL_PLANNER_API_URL", "http://127.0.0.1:8000/chat")


def format_flights(flights):
    lines = ["**Flights Found:**\n"]
    for i, flight in enumerate(flights, 1):
        fid = flight.get("_id", "N/A")
        airline = flight.get("airline", "Unknown")
        number = flight.get("flightNumber", "N/A")
        origin = flight.get("origin", {})
        dest = flight.get("destination", {})
        origin_name = origin.get("airport", origin) if isinstance(origin, dict) else origin
        dest_name = dest.get("airport", dest) if isinstance(dest, dict) else dest
        date = flight.get("flightDate", "N/A")
        dep = flight.get("departureTime", "N/A")
        arr = flight.get("arrivalTime", "N/A")
        price = flight.get("price", "N/A")
        currency = flight.get("currency", "USD")
        seats = flight.get("availableSeats", "N/A")
        lines.append(
            f"{i}. **{airline} {number}** | {origin_name} to {dest_name}\n"
            f"   Date: {date} | Time: {dep} - {arr}\n"
            f"   Price: {currency} {price} | Seats: {seats}\n"
            f"   ID: `{fid}`\n"
        )
    return "\n".join(lines)


def format_hotels(hotels):
    lines = ["**Hotels Found:**\n"]
    for i, hotel in enumerate(hotels, 1):
        hid = hotel.get("_id", "N/A")
        name = hotel.get("name", "Unknown")
        city = hotel.get("city", "")
        if isinstance(city, dict):
            city = city.get("name", "")
        stars = hotel.get("starRating", hotel.get("stars", "N/A"))
        price = hotel.get("pricePerNight", hotel.get("price", "N/A"))
        currency = hotel.get("currency", "USD")
        rooms = hotel.get("availableRooms", hotel.get("available_rooms", "N/A"))
        star_str = f"{stars} stars" if isinstance(stars, (int, float)) else "N/A"
        lines.append(
            f"{i}. **{name}** - {city} ({star_str})\n"
            f"   Price: {currency} {price}/night | Rooms: {rooms} available\n"
            f"   ID: `{hid}`\n"
        )
    return "\n".join(lines)


def call_chat_api(message):
    payload = json.dumps({"message": message}).encode("utf-8")
    request = Request(API_URL, data=payload, headers={"Content-Type": "application/json"})
    try:
        response = urlopen(request, timeout=60)
        return json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        return {"response": f"Service temporarily unavailable. Please try again. ({exc})"}


def respond(message, history):
    if not message or not message.strip():
        yield history
        return

    history = history + [{"role": "user", "content": message}]

    msg_lower = message.lower()
    if any(w in msg_lower for w in ["hotel", "room", "stay", "accommodation"]):
        activity = "Searching hotel options..."
    elif any(w in msg_lower for w in ["flight", "fly", "ticket", "airline"]):
        activity = "Searching flight options..."
    elif any(w in msg_lower for w in ["book", "reserve"]):
        activity = "Processing your booking..."
    else:
        activity = "Processing your request..."

    history = history + [{"role": "assistant", "content": activity}]
    yield history

    data = call_chat_api(message)

    parts = []
    chat_text = data.get("response", "No response returned.")
    if chat_text:
        parts.append(chat_text)
    if data.get("hotels"):
        parts.append(format_hotels(data["hotels"]))
    if data.get("flights"):
        parts.append(format_flights(data["flights"]))

    full_response = "\n\n".join(parts)

    streamed = ""
    for char in full_response:
        streamed += char
        history[-1] = {"role": "assistant", "content": streamed}
        yield history
        time.sleep(0.01)


def main():
    with gr.Blocks(title="TripWeaver") as demo:
        gr.HTML("""
            <div style="text-align:center; padding:20px;
                        background:linear-gradient(135deg,#0061ff 0%,#60efff 100%);
                        border-radius:12px; margin-bottom:16px; color:white;">
                <h1 style="margin:0; font-size:28px;">TripWeaver</h1>
                <p style="margin:8px 0 0 0; opacity:0.9;">Your AI travel assistant - hotels, flights, and bookings</p>
            </div>
        """)

        chatbot = gr.Chatbot(height=500)

        with gr.Row():
            message = gr.Textbox(
                placeholder="e.g. Find me a hotel in Mumbai, or flights from BOM to DEL",
                scale=8,
                container=False,
            )
            submit = gr.Button("Send", scale=1, variant="primary")

        with gr.Row():
            btn1 = gr.Button("Hotels in Mumbai", size="sm")
            btn2 = gr.Button("Flights BOM to DEL", size="sm")
            btn3 = gr.Button("List all hotels", size="sm")

        btn1.click(lambda: "find me a hotel in Mumbai", outputs=message)
        btn2.click(lambda: "find flights from BOM to DEL", outputs=message)
        btn3.click(lambda: "show me all hotels", outputs=message)

        submit.click(respond, inputs=[message, chatbot], outputs=chatbot)
        message.submit(respond, inputs=[message, chatbot], outputs=chatbot)

    demo.launch(server_name="0.0.0.0", server_port=7860)


if __name__ == "__main__":
    main()
