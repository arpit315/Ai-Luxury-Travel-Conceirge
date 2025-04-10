from flask import Flask, render_template, request, jsonify
import os
import requests
import re
from dotenv import load_dotenv

app = Flask(__name__)
load_dotenv()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json.get("message")

    if "hotel" in user_input.lower():
        match = re.search(r'(?:near|in|at)\s+([a-zA-Z\s]+)', user_input.lower())
        location_query = match.group(1).strip() if match else user_input
        response = get_hotels_from_foursquare(location_query)

    elif any(keyword in user_input.lower() for keyword in ["trek", "activity", "adventure", "things to do"]):
        match = re.search(r'(?:near|in|at)\s+([a-zA-Z\s]+)', user_input.lower())
        location_query = match.group(1).strip() if match else user_input
        response = get_activities_from_foursquare(location_query)

    elif any(word in user_input.lower() for word in ["dining", "restaurant", "food", "fine dining"]):
        match = re.search(r'(?:near|in|at)\s+([a-zA-Z\s]+)', user_input.lower())
        location_query = match.group(1).strip() if match else user_input
        response = get_dining_spots(location_query)

    else:
        response = "🧭 I can help with luxury hotels, activities, and fine dining. Try : 'Top restaurants in Goa' or 'Fine dining in Udaipur'!"

    return jsonify({"reply": response})


def get_hotels_from_foursquare(location):
    opencage_api_key = os.getenv("OPENCAGE_API_KEY")
    geocode_url = f"https://api.opencagedata.com/geocode/v1/json?q={location}&key={opencage_api_key}"
    geo_response = requests.get(geocode_url).json()

    if not geo_response["results"]:
        return "❌ Failed to retrieve location data."

    lat = geo_response["results"][0]["geometry"]["lat"]
    lon = geo_response["results"][0]["geometry"]["lng"]

    foursquare_api_key = os.getenv("FOURSQUARE_API_KEY")
    headers = {
        "Accept": "application/json",
        "Authorization": foursquare_api_key
    }

    search_url = f"https://api.foursquare.com/v3/places/search?ll={lat},{lon}&query=luxury hotel&limit=10"
    places_response = requests.get(search_url, headers=headers).json()

    if "results" not in places_response or not places_response["results"]:
        return "❌ No luxury hotels found near that location."

    result = f"🏨 <b>Top Luxury Hotels in {location.title()}</b><br>\n\n"

    for idx, place in enumerate(places_response["results"][:5]):
        name = place.get("name", "Unnamed Hotel")
        address = place.get("location", {}).get("formatted_address", "No address available")
        geo = place.get("geocodes", {}).get("main", {})
        lat = geo.get("latitude")
        lon = geo.get("longitude")
        maps_link = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}" if lat and lon else "Map link unavailable"
        rating = place.get("rating", 5)
        stars = "⭐" * int(round(rating)) if rating else "No rating"

        result += (
            f"{idx+1}. 🏨 <b>{name}</b><br>\n"
            f"📍 <b>Address:</b> {address}<br>\n"
            f"⭐ <b>Rating:</b> {stars}<br>\n"
            f"📌 <a href='{maps_link}'>View on google Map</a><br>\n\n"
        )

    return result.strip()


def get_activities_from_foursquare(location):
    opencage_api_key = os.getenv("OPENCAGE_API_KEY")
    geocode_url = f"https://api.opencagedata.com/geocode/v1/json?q={location}&key={opencage_api_key}"
    geo_response = requests.get(geocode_url).json()

    if not geo_response["results"]:
        return fallback_activities(location)

    lat = geo_response["results"][0]["geometry"]["lat"]
    lon = geo_response["results"][0]["geometry"]["lng"]

    foursquare_api_key = os.getenv("FOURSQUARE_API_KEY")
    headers = {
        "Accept": "application/json",
        "Authorization": foursquare_api_key
    }

    query = "hiking,adventure,trek,nature,paragliding,explore"
    search_url = f"https://api.foursquare.com/v3/places/search?ll={lat},{lon}&query={query}&limit=8"
    response = requests.get(search_url, headers=headers).json()

    if "results" not in response or not response["results"]:
        return fallback_activities(location)

    result = f"🎉 Here are some exciting things to do in {location.title()}:\n"
    emojis = ["🌄", "🛶", "🪂", "🚵‍♂️", "🎯", "🏕️", "🏞️", "🧗"]

    for idx, place in enumerate(response["results"]):
        name = place.get("name", "Unnamed Activity")
        emoji = emojis[idx % len(emojis)]
        result += f"{emoji} {name}\n"

    return result.strip()


def get_dining_spots(location):
    opencage_api_key = os.getenv("OPENCAGE_API_KEY")
    geocode_url = f"https://api.opencagedata.com/geocode/v1/json?q={location}&key={opencage_api_key}"
    geo_response = requests.get(geocode_url).json()

    if not geo_response["results"]:
        return fallback_dining(location)

    lat = geo_response["results"][0]["geometry"]["lat"]
    lon = geo_response["results"][0]["geometry"]["lng"]

    foursquare_api_key = os.getenv("FOURSQUARE_API_KEY")
    headers = {
        "Accept": "application/json",
        "Authorization": foursquare_api_key
    }

    search_url = f"https://api.foursquare.com/v3/places/search?ll={lat},{lon}&query=fine dining&limit=10"
    response = requests.get(search_url, headers=headers).json()

    if "results" not in response or not response["results"]:
        return fallback_dining(location)

    result = f"🍽️ <b>Top Fine-Dining Spots in {location.title()}</b><br><br>"
    for idx, place in enumerate(response["results"][:5]):
        name = place.get("name", "Unnamed Spot")
        address = place.get("location", {}).get("formatted_address", "No address available")
        geo = place.get("geocodes", {}).get("main", {})
        lat = geo.get("latitude")
        lon = geo.get("longitude")
        maps_link = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}" if lat and lon else "Map unavailable"
        result += (
            f"{idx+1}. 🍽️ <b>{name}</b><br>"
            f"📍 <b>Address:</b> {address}<br>"
            f"📌 <a href='{maps_link}'>View on Map</a><br><br>"
        )
    return result.strip()


def fallback_activities(location):
    state_fallbacks = {
        "goa": ["🏖️ Beach Parties", "🛥️ Yacht Rides", "🍹 Nightlife", "🌅 Sunset Cruise", "🏄 Water Sports"],
        "himachal pradesh": ["🧗 Trekking", "🏔️ Snow Adventures", "🏞️ Valley Hikes"],
        "manali": ["🧗 Paragliding", "🏕️ Camping", "🚵 Biking Trails"],
        "kerala": ["🏖️ Backwater Cruises", "🌿 Wildlife Safari", "🏄 Surfing", "🌺 Ayurveda Spa", "🚤 Houseboat Rides"],
        "rajasthan": ["🏰 Heritage Tours", "🎠 Camel Ride", "🏜️ Desert Safari", "🎨 Traditional Art Workshops", "🍂 Royal Palaces"],
        "uttarakhand": ["⛰️ Mountain Trekking", "🌄 Sunrise Views", "🎣 Fishing", "🏕️ Camping", "🚠 Cable Car Rides"],
        "goa": ["🏖️ Beach Parties", "🛥️ Yacht Rides", "🍹 Nightlife", "🌅 Sunset Cruise", "🏄 Water Sports"],
        "delhi": ["🏙️ Historical Monuments", "🍽️ Street Food", "🎭 Cultural Shows", "🛍️ Shopping Malls", "🌳 Parks & Gardens"],
        "tamil nadu": ["⛪ Temple Tours", "🌴 Beaches", "🌿 Wildlife Sanctuaries", "🎤 Classical Dance Shows", "🍜 Traditional Cuisine"],
        "kashmir": ["🏔️ Skiing", "🚤 Shikara Ride", "🌷 Flower Gardens", "🌲 Trekking", "🛶 Boating"],
        "sikkim": ["🏞️ Nature Walks", "⛰️ Mountain Views", "🌳 Wildlife Safaris", "🐍 River Rafting", "🎿 Skiing"],
        "andaman and nicobar islands": ["🐠 Scuba Diving", "🏝️ Island Hopping", "🐚 Beach Relaxation", "🚤 Boat Tours", "🌊 Snorkeling"],
        "ladakh": ["🏔️ High Altitude Trekking", "🚴‍♂️ Cycling", "🌌 Stargazing", "🏜️ Desert Safaris", "⛺ Camping"],
        "kerala": ["🏖️ Backwater Cruises", "🌿 Wildlife Safari", "🏄 Surfing", "🌺 Ayurveda Spa", "🚤 Houseboat Rides"],
        "uttar pradesh": ["🏰 Taj Mahal", "🌄 Sunrise Views", "🕌 Historical Sites", "🎡 Theme Parks", "🍛 Local Cuisine"],
        "bihar": ["🌿 Buddhist Circuit", "🎭 Traditional Dance", "🏰 Patna Sahib", "⛩️ Nalanda University", "🚶 Heritage Walks"],
        "punjab": ["🕌 Golden Temple", "🎶 Bhangra Dance", "🚜 Visit Village Farms", "🍛 Punjabi Cuisine", "🎨 Folk Art Exhibitions"]
        # Add more as needed
    }
    location_key = location.lower()
    matched_state = next((state for state in state_fallbacks if state in location_key), None)

    if matched_state:
        activities = state_fallbacks[matched_state]
        reply = f"🎉 Here are some popular things to do in {matched_state.title()}:<br>\n"
        for activity in activities:
            reply += f"{activity}\n<br> "
        return reply.strip()
    else:
        return "🤖 Sorry, couldn't find adventure spots there. Try another State"


def fallback_dining(location):
    custom_dining = {
        "goa": [
            "1. 🥂 <b>Aura Bistro</b> - Fine cocktails & seaview | 📍Baga Beach",
            "2. 🐟 <b>Thalassa</b> - Greek seaside magic | 📍Vagator",
            "3. 🧀 <b>Pousada by the Beach</b> - Gourmet beachside | 📍Calangute"
        ],
        "udaipur": [
            "1. 🍷 <b>Ambrai Restaurant</b> - Lake view fine dining | 📍Lake Pichola",
            "2. 🥘 <b>1559 AD</b> - Heritage Rajasthani vibes | 📍Saheli Marg",
            "3. 🏰 <b>Upre</b> - Rooftop palace views | 📍Chand Pole"
        ],
        "delhi": [
            "1. 🥂 <b>Indian Accent</b> - Global gourmet | 📍Lodhi Road",
            "2. 🍽️ <b>Bukhara</b> - Mughlai classics | 📍ITC Maurya",
            "3. 🧁 <b>Le Cirque</b> - French-Italian elegance | 📍The Leela"
        ],
         "rajasthan": [
            "1. 🍽️ <b>Rambagh Palace</b> - Royal dining experience | 📍Jaipur",
            "2. 🍷 <b>Oberoi Udaivilas</b> - Luxury with lake view | 📍Udaipur",
            "3. 🥘 <b>Suvarna Mahal</b> - Royal heritage dining | 📍Jaipur"
        ],
        "tamil nadu": [
            "1. 🍽️ <b>The Raintree</b> - Contemporary dining | 📍Chennai",
            "2. 🥂 <b>ITC Grand Chola</b> - Luxurious southern delicacies | 📍Chennai",
            "3. 🍴 <b>The Flying Elephant</b> - Fine global cuisine | 📍Chennai"
        ],
        "kerala": [
            "1. 🍽️ <b>The Leela Kovalam</b> - Seaview fine dining | 📍Kovalam",
            "2. 🥘 <b>Ayurveda and Restaurant</b> - Traditional Kerala flavors | 📍Kumarakom",
            "3. 🍷 <b>Fort Kochi</b> - Colonial charm and fine dining | 📍Kochi"
        ],
        "manali": [
            "1. 🥂 <b>The Manali Inn</b> - Alpine dining | 📍Manali",
            "2. 🍽️ <b>Johnson’s Lodge & Cafe</b> - Mountain view dining | 📍Manali",
            "3. 🍷 <b>Himalayan Village</b> - Heritage dining | 📍Manali"
        ],
        "goa": [
            "1. 🥂 <b>Aura Bistro</b> - Fine cocktails & seaview | 📍Baga Beach",
            "2. 🐟 <b>Thalassa</b> - Greek seaside magic | 📍Vagator",
            "3. 🧀 <b>Pousada by the Beach</b> - Gourmet beachside | 📍Calangute"
        ],
        "bihar": [
            "1. 🍽️ <b>Patna’s Bada Bagh</b> - Authentic Bihari cuisine | 📍Patna",
            "2. 🥂 <b>Hotel Maurya Patna</b> - Luxury in the heart of Patna | 📍Patna",
            "3. 🍛 <b>Gulzar Garden</b> - Cozy fine dining | 📍Patna"
        ],
        "punjab": [
            "1. 🍽️ <b>The Oberoi Sukhvilas</b> - Luxurious Punjabi flavors | 📍Chandigarh",
            "2. 🥂 <b>The Royal Orchid</b> - Modern luxury dining | 📍Amritsar",
            "3. 🍷 <b>Shahpura House</b> - Royal dining | 📍Amritsar"
        ],
        "uttarakhand": [
            "1. 🍷 <b>Ananda in the Himalayas</b> - Spa and fine dining | 📍Narendra Nagar",
            "2. 🍽️ <b>The Naini Retreat</b> - Dining with mountain views | 📍Nainital",
            "3. 🥂 <b>WelcomHeritage Haveli Dharampura</b> - Traditional ambiance | 📍Nainital"
        ],
        "himachal pradesh": [
            "1. 🥂 <b>Wildflower Hall</b> - Mountain luxury dining | 📍Shimla",
            "2. 🍽️ <b>The Himalayan Village</b> - Authentic Himachali flavors | 📍Kullu",
            "3. 🍷 <b>The Oberoi Cecil</b> - Colonial-style luxury | 📍Shimla"
        ],
        "sikkim": [
            "1. 🍷 <b>Mayfair Spa Resort & Casino</b> - Luxury dining and views | 📍Gangtok",
            "2. 🍽️ <b>The Royal Plaza</b> - Contemporary luxury | 📍Gangtok",
            "3. 🥂 <b>WelcomHeritage Denzong Regency</b> - Himalayan luxury | 📍Gangtok"
        ],
        "kashmir": [
            "1. 🥂 <b>The Lalit Grand Palace</b> - Royal dining experience | 📍Srinagar",
            "2. 🧀 <b>Houseboat Restaurants</b> - Floating dining experience | 📍Srinagar",
            "3. 🍷 <b>Shikara</b> - Dining on the Dal Lake | 📍Srinagar"
        ],
        "andaman and nicobar islands": [
            "1. 🍽️ <b>The Havelock Island Beach Resort</b> - Island-side luxury | 📍Havelock",
            "2. 🏝️ <b>Taj Exotica Resort & Spa</b> - Beachfront fine dining | 📍Port Blair",
            "3. 🥂 <b>Barefoot Bar & Restaurant</b> - Seafront luxury | 📍Havelock"
        ],
        "ladakh": [
            "1. 🥂 <b>The Grand Dragon Ladakh</b> - Dining with mountain views | 📍Leh",
            "2. 🍷 <b>Ladakh Sarai</b> - Traditional Ladakhi dining | 📍Leh",
            "3. 🍽️ <b>Zen Restaurant</b> - Luxury dining experience | 📍Leh"
        ],
        "uttar pradesh": [
            "1. 🍽️ <b>The Mughal Restaurant</b> - Mughlai luxury | 📍Agra",
            "2. 🥂 <b>Taj Mahal View Restaurant</b> - Dining with a view | 📍Agra",
            "3. 🍷 <b>Shah Jahan Restaurant</b> - Royal Mughal dining | 📍Agra"
        ]
    }

    key = location.lower()
    fallback = custom_dining.get(key)

    if fallback:
        return f"🍽️ <b>Curated Fine-Dining Spots in {location.title()}</b><br><br>" + "<br>".join(fallback)
    else:
        return "😕 Sorry, I couldn't find fine-dining options there. Try asking for Delhi, Goa, or Udaipur!"

if __name__ == "__main__":
    app.run(debug=True)
