LetsGoF1 | Ultimate F1 Dashboard
This repository contains the source code for LetsGoF1, a comprehensive Formula 1 data analytics dashboard. Built with Python and Streamlit, it leverages the FastF1 library to provide fans and analysts with real-time-like access to telemetry, lap timing, tyre strategies, and track insights.

🚀 Features
Home Hub: A season overview showing the current schedule and countdown/details for the next upcoming Grand Prix.

Race Analysis: * Classification: Final race results including positions, points, and status.

Tyre Strategy: Visual breakdown of compound usage and stint lengths for every driver.

Lap Pace: Box plots representing lap time consistency across the grid.

Weather Evolution: Real-time tracking of air/track temperature and humidity during the session.

Interactive Track Map: A speed-coded telemetry map showing braking and acceleration zones.

Driver Battle: Side-by-side telemetry comparison between any two drivers, featuring:

Speed Traces

Throttle Application

Braking Points

Live Time Delta (Gap analysis)

🛠️ Tech Stack
Framework: Streamlit

Data Source: FastF1

Visualization: Plotly & Matplotlib

Data Manipulation: Pandas & NumPy

📦 Installation & Setup
Clone the repository:

Bash
git clone https://github.com/your-username/letsgof1.git
cd letsgof1
Install dependencies:

Bash
pip install streamlit fastf1 pandas numpy plotly matplotlib
Run the application:

Bash
streamlit run app.py
🔧 Configuration
The application uses a local cache folder (f1_cache) to store telemetry data. This significantly speeds up load times for previously viewed races and reduces the load on F1's data servers.

Note: The first time you load a race, it may take 30–60 seconds to download the full telemetry packets.

📝 Disclaimer
LetsGoF1 is an unofficial project and is not associated in any way with the Formula 1 companies. F1, FORMULA ONE, FORMULA 1, FIA FORMULA ONE WORLD CHAMPIONSHIP, GRAND PRIX and related marks are trade marks of Formula One Licensing B.V.

Developed by: Danvanthram KK
