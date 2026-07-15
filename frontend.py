import json
import os
import time
from urllib.request import Request, urlopen
import gradio as gr

API_URL = os.environ.get(
    "TRAVEL_PLANNER_API_URL",
    "http://127.0.0.1:8000/chat"
)

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;1,400;1,600&family=DM+Sans:wght@300;400;500;600&display=swap');

*, *::before, *::after { box-sizing: border-box; }

html, body, .gradio-container, gradio-app, .app {
    background: #F0EDF8 !important;
    font-family: 'DM Sans', sans-serif !important;
    color: #2D2535 !important;
}

.gradio-container {
    max-width: 860px !important;
    width: 100% !important;
    margin: 0 auto !important;
    padding: 20px 16px !important;
}

.trip-hero {
    text-align: center;
    padding: 36px 24px 28px;
    background: rgba(255, 255, 255, 0.94);
    border-radius: 16px;
    margin-bottom: 18px;
    border: 1px solid rgba(123, 94, 167, 0.12);
    box-shadow: 0 4px 28px rgba(123, 94, 167, 0.12);
}

.trip-hero .wordmark {
    font-family: 'DM Sans', sans-serif;
    font-size: 14px;
    font-weight: 600;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: #7B5EA7;
    margin-bottom: 10px;
}

.trip-hero h1 {
    font-family: 'Cormorant Garamond', Georgia, serif;
    font-style: italic;
    font-size: clamp(24px, 4.5vw, 34px);
    font-weight: 400;
    color: #2D2535;
    margin: 0 0 8px 0;
    line-height: 1.2;
    letter-spacing: -0.01em;
}

.trip-hero p {
    font-family: 'DM Sans', sans-serif;
    font-size: 13px;
    font-weight: 400;
    color: #8A7FA0;
    margin: 0;
    letter-spacing: 0.01em;
}

footer { display: none !important; }

@media (max-width: 640px) {
    .gradio-container { padding: 12px 10px !important; }
    .trip-hero { padding: 24px 16px 20px; margin-bottom: 14px; }
    .trip-hero .wordmark { font-size: 12px; }
    .trip-hero h1 { font-size: 22px; }
    .trip-hero p { font-size: 12px; }
}
"""


def format_flights(flights):
    lines = ["**Flights**\n"]
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
            f"{i}. **{airline} {number}** — {origin_name} to {dest_name}\n"
            f"   {date} | {dep} – {arr} | {currency} {price} | {seats} seats\n"
            f"   Booking ID: `{fid}`\n"
        )
    return "\n".join(lines)


def format_hotels(hotels):
    lines = ["**Hotels**\n"]
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
        star_str = f"{stars}-star" if isinstance(stars, (int, float)) else ""
        lines.append(
            f"{i}. **{name}** — {city} {star_str}\n"
            f"   {currency} {price} per night | {rooms} rooms available\n"
            f"   Booking ID: `{hid}`\n"
        )
    return "\n".join(lines)


def call_chat_api(message):
    payload = json.dumps({"message": message}).encode("utf-8")
    req = Request(
        API_URL, data=payload,
        headers={"Content-Type": "application/json"}
    )
    try:
        response = urlopen(req, timeout=60)
        return json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        return {"response": f"Something went wrong. Please try again in a moment. ({exc})"}


def respond(message, history):
    if not message or not message.strip():
        yield history
        return

    history = history + [{"role": "user", "content": message}]

    msg_lower = message.lower()
    if any(w in msg_lower for w in ["hotel", "room", "stay", "accommodation", "place to stay"]):
        activity = "Searching available hotels..."
    elif any(w in msg_lower for w in ["flight", "fly", "ticket", "airline"]):
        activity = "Searching available flights..."
    elif any(w in msg_lower for w in ["book", "reserve"]):
        activity = "Processing your booking..."
    elif any(w in msg_lower for w in ["plan", "trip", "travel", "journey"]):
        activity = "Putting your journey together..."
    else:
        activity = "On it..."

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
        time.sleep(0.008)


def main():
    with gr.Blocks(title="TripWeaver", css=CSS) as demo:

        gr.HTML("""
        <div class="trip-hero">
            <div class="wordmark">TripWeaver</div>
            <h1>Plan your perfect journey</h1>
            <p>Hotels, flights and bookings</p>
        </div>
        """)

        chatbot = gr.Chatbot(
            height=440,
            placeholder=(
                "<div style='text-align:center; color:#8A7FA0; padding:40px 20px;'>"
                "<div style='font-family:Cormorant Garamond,Georgia,serif; "
                "font-style:italic; font-size:20px; margin-bottom:8px;'>"
                "Where would you like to go?"
                "</div>"
                "<div style='font-family:DM Sans,sans-serif; font-size:13px; "
                "font-weight:300;'>"
                "Ask about hotels in a city, flights between airports, "
                "or help planning a trip."
                "</div>"
                "</div>"
            ),
        )

        with gr.Row():
            message = gr.Textbox(
                placeholder="Search hotels, flights, or plan a trip...",
                scale=8,
                container=False,
                lines=1,
            )
            submit = gr.Button("Send", scale=1, variant="primary")

        with gr.Row():
            btn1 = gr.Button("Find somewhere to stay", size="sm", variant="secondary")
            btn2 = gr.Button("Search for a flight", size="sm", variant="secondary")
            btn3 = gr.Button("Help me plan a trip", size="sm", variant="secondary")

        btn1.click(lambda: "Find me somewhere to stay", outputs=message)
        btn2.click(lambda: "Search for a flight", outputs=message)
        btn3.click(lambda: "Help me plan a trip", outputs=message)

        submit.click(respond, inputs=[message, chatbot], outputs=chatbot)
        message.submit(respond, inputs=[message, chatbot], outputs=chatbot)

    demo.launch(server_name="0.0.0.0", server_port=7860)


if __name__ == "__main__":
    main()
