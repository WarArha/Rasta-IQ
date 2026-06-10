# Rasta IQ — AI Safety & Tourism Companion for Pakistan

Rasta IQ is a safety-first AI travel planning web app for Pakistan. It helps travelers plan safer and budget-friendly trips by combining route recommendation, route safety scoring, predefined safety/risk zones, AI or fallback itinerary generation, tourist place suggestions, trip monitoring simulation, and guardian SMS alert simulation.

This project was built for the GDGoC IST Innovators Challenge under the Tourism and Build for Her themes.

---

## Problem Statement

Travel planning in Pakistan is not only about choosing destinations and estimating cost. For women, families, students, and tourists, safety is also a major concern.

Most travel planning apps focus on places, hotels, and routes, but they usually do not provide:

* Route safety scoring
* Safety/risk zone awareness
* Time-based safety warnings
* Guardian alert support
* Safety-focused itinerary planning
* Clear MVP limitations around real-time safety claims

Rasta IQ addresses this gap by combining tourism planning with safety-aware route analysis.

---

## Solution Overview

Rasta IQ allows users to enter trip details such as source, destination, budget, travel days, traveler type, preferences, and guardian details. The app then generates a safety-aware trip planning experience.

The app provides:

* Recommended route
* Route safety score
* Safety/risk zone warnings
* Interactive route map
* Optional road-following route support
* AI/fallback itinerary
* Tourist place recommendations
* Active trip monitoring simulation
* Guardian SMS alert simulation

---

## Key Features

### 1. Trip Input and Validation

Users can enter:

* Starting location
* Destination
* Budget
* Number of days
* Travel date
* Preferred departure time
* Traveler type
* Travel preferences
* Guardian name and phone number

The app validates required inputs before generating a trip plan.

---

### 2. Route Recommendation

The app selects a route from stored sample route data based on source and destination. If no exact route is found, it safely uses a fallback route for demo continuity.

---

### 3. Route Safety Score

Rasta IQ calculates a safety score out of 100 using:

* Predefined safety/risk zones
* Risk level
* Estimated crowd level
* Route difficulty
* Traffic level
* Traveler type

The route is labeled as:

* Safe
* Moderate
* Risky

---

### 4. Safety/Risk Zone Display

The app displays nearby predefined safety/risk zones with:

* City
* Risk level
* Crowd level
* Risk reason
* Avoid-after time
* Recommended action

---

### 5. Interactive Map

Rasta IQ uses Folium and streamlit-folium to display:

* Planned route
* Source marker
* Destination marker
* Route points
* High, medium, and low-risk safety zones

Map legend:

* Blue line: Planned route
* Red circle: High-risk zone
* Orange circle: Medium-risk zone
* Green circle: Low-risk or safer zone

---

### 6. Optional Road-Following Route

The app includes an optional road-following route mode using a free routing service. If this service is unavailable, the app safely falls back to demo/sample route coordinates.

---

### 7. AI / Fallback Itinerary

Rasta IQ includes an itinerary generation module.

If Gemini API is available, the app can generate an AI-based itinerary.

If Gemini API key is missing or unavailable, the app safely generates a fallback itinerary using local logic.

The itinerary includes:

* Day-wise trip plan
* Budget breakdown
* Safety notes

---

### 8. Tourist Place Suggestions

The app suggests destination-based tourist places using local JSON data.

For each place, it shows:

* Place name
* Category
* Estimated cost
* Recommended time
* Family-friendly status
* Safety note

---

### 9. Active Trip Monitoring Simulation

Rasta IQ simulates trip monitoring using predefined GPS scenarios.

Monitoring states:

* Safe: user is on route and outside risk zones
* Warning: user is deviated or inside a risk zone
* Critical: user is more than 1000 meters away from the route and inside a medium/high-risk zone

This is an MVP simulation and not background GPS tracking.

---

### 10. Guardian SMS Alert Simulation

If the monitoring result becomes Critical, the app generates a simulated guardian SMS alert.

The SMS feature is simulation-only in this MVP. No real telecom SMS is sent.

---

## Tech Stack

* Python
* Streamlit
* Folium
* streamlit-folium
* JSON data files
* Gemini API / fallback mode
* OSRM road-following route support
* Haversine distance calculation

---

## Project Structure

```text
Rasta-IQ/
│
├── app.py
├── gemini_service.py
├── location_utils.py
├── road_route_service.py
├── safety_score.py
├── sms_service.py
├── trip_monitor.py
├── requirements.txt
├── README.md
│
└── data/
    ├── safety_zones.json
    ├── sample_routes.json
    └── tourist_places.json
```

---

## Installation and Setup

### 1. Clone the repository

```bash
git clone <your-github-repository-link>
cd Rasta-IQ
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the Streamlit app

```bash
streamlit run app.py
```

The app will open in your browser at:

```text
http://localhost:8501
```

---

## Gemini API Setup

The app works even without a Gemini API key because fallback mode is included.

To use Gemini API locally, create a `.env` file and add:

```text
GEMINI_API_KEY=your_api_key_here
```

Do not upload `.env` to GitHub.

If no API key is available, the app will automatically use fallback itinerary mode.

---

## MVP Limitations

This project is an MVP and includes the following limitations:

* Safety/risk zones are predefined and stored in local JSON data.
* The app does not predict harassment in real time.
* Crowd and safety levels are estimated, not live-detected.
* Trip monitoring is simulated for demonstration.
* Guardian SMS alerts are simulated and not sent through a real telecom network.
* Road-following route uses a free routing service and falls back to demo coordinates if unavailable.
* Monitoring works only while the Streamlit web app is open and active.

---

## Future Scope

Future improvements may include:

* Real mobile GPS tracking
* Firebase-based live guardian updates
* Google Routes API for production-grade traffic-aware routing
* Verified safety-zone data from trusted public/community sources
* Real SMS or WhatsApp alert integration
* Nearby emergency service suggestions such as hospitals and police stations
* Urdu and Roman Urdu language support
* Mobile app version

---

## Ethical Safety Note

Rasta IQ is designed as a safety-awareness and travel-planning support tool. It does not replace emergency services, local authorities, or personal judgment. The app does not claim to predict harassment, crime, or real-time danger. It uses predefined safety data, route analysis, and simulated monitoring to demonstrate a safety-first travel planning concept.

---

## Team

Built by Team Rasta IQ for GDGoC IST Innovators Challenge 2026.

---

## Submission Deliverables

The final project submission includes:

* Pitch Deck PDF
* Public GitHub Repository
* Demo Video
* Working MVP Hosted Link
