import streamlit as st
import fastf1
import fastf1.plotting
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timezone
import os

st.set_page_config(
    page_title="LetsGoF1 | Ultimate Dashboard",
    page_icon="🏎️",
    layout="wide",
    initial_sidebar_state="expanded"
)
cache_dir = 'f1_cache'
if not os.path.exists(cache_dir):
    os.makedirs(cache_dir)

fastf1.Cache.enable_cache(cache_dir)
fastf1.plotting.setup_mpl(misc_mpl_mods=False)

st.markdown("""
<style>
    .stApp { background-color: #0e0e10; color: #e0e0e0; }
    [data-testid="stSidebar"] { background-color: #050505; border-right: 1px solid #222; }
    h1, h2, h3 { color: #ff1801 !important; font-family: "Arial Black", sans-serif; text-transform: uppercase; }
    div[data-testid="metric-container"] { background-color: #1a1a1a; border: 1px solid #333; padding: 10px; border-radius: 8px; color: white; }
    .stButton>button { background-color: #ff1801; color: white; border: none; border-radius: 4px; font-weight: bold; }
    .stButton>button:hover { background-color: #cc0000; color: white; }
</style>
""", unsafe_allow_html=True)
@st.cache_data
def get_schedule(year):
    try:
        schedule = fastf1.get_event_schedule(year)
        return schedule[schedule['EventFormat'] != 'testing']
    except Exception as e:
        return pd.DataFrame()

@st.cache_resource
def load_session(year, race_name, session_type='R'):
    session = fastf1.get_session(year, race_name, session_type)
    session.load()
    return session

def get_next_race(schedule):
    now = pd.Timestamp.now('UTC')
    
    if not schedule.empty:
        date_col = 'Session5Date' if 'Session5Date' in schedule.columns else 'EventDate'
        schedule[date_col] = pd.to_datetime(schedule[date_col], utc=True)
        
        future_races = schedule[schedule[date_col] >= now]
        if not future_races.empty:
            return future_races.iloc[0], date_col
    return None, None

# 5. MAIN APP
def main():
    st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/3/33/F1.svg/1200px-F1.svg.png", width=100)
    st.sidebar.title("LetsGoF1")
    st.sidebar.caption("The Ultimate Data Dashboard")

    current_year = datetime.now().year
    selected_year = st.sidebar.selectbox("Select Season", [2026, 2025, 2024, 2023, 2022], index=1)
    
    page = st.sidebar.radio("Navigation", ["🏠 Home Hub", "📊 Race Analysis", "🏎️ Driver Battle", "ℹ️ About"])

    # --- HOME PAGE ---
    if page == "🏠 Home Hub":
        st.title(f"📅 {selected_year} Season Command Center")
        
        schedule = get_schedule(selected_year)
        
        if not schedule.empty:
            next_race, date_col = get_next_race(schedule)
            
            if next_race is not None:
                st.markdown("### 🚀 Next Grand Prix")
                c1, c2, c3 = st.columns([2, 1, 1])
                with c1:
                    st.header(next_race['EventName'])
                    st.subheader(f"📍 {next_race['Location']}")
                with c2:
                    st.metric("Round", f"#{next_race['RoundNumber']}")
                with c3:
                    race_time = next_race[date_col]
                    st.metric("Date", race_time.strftime('%d %b'))
                    st.caption(race_time.strftime('%H:%M UTC'))

            st.markdown("---")
            
            st.subheader("🗓️ Full Calendar")
            display_cols = ['RoundNumber', 'EventName', 'Location', 'Session5Date'] if 'Session5Date' in schedule.columns else ['RoundNumber', 'EventName', 'Location', 'EventDate']
            
            st.dataframe(
                schedule[display_cols].set_index('RoundNumber'),
                use_container_width=True,
                column_config={
                    "EventName": "Grand Prix",
                    "Session5Date": st.column_config.DatetimeColumn("Race Date", format="D MMM YYYY, HH:mm"),
                    "EventDate": st.column_config.DatetimeColumn("Race Date", format="D MMM YYYY")
                }
            )
        else:
            st.info("Schedule not available for this year yet.")

    # --- RACE ANALYSIS ---
    elif page == "📊 Race Analysis":
        st.title("📊 Grand Prix Analytics")
        
        schedule = get_schedule(selected_year)
        
        # Fix: Force UTC for comparison
        now = pd.Timestamp.now('UTC')
        date_col = 'Session5Date' if 'Session5Date' in schedule.columns else 'EventDate'
        schedule[date_col] = pd.to_datetime(schedule[date_col], utc=True)
        past_races = schedule[schedule[date_col] < now]

        if past_races.empty:
            st.warning("No races have been completed in this season yet.")
        else:
            selected_race_name = st.selectbox("Select Race", past_races['EventName'].unique(), index=len(past_races)-1)
            
            if st.button("Load Race Data 🚀"):
                with st.spinner("Downloading Telemetry, Laps, and Weather... This takes about 30s."):
                    try:
                        session = load_session(selected_year, selected_race_name, 'R')
                        st.session_state['session'] = session
                        st.success(f"Data Loaded for {selected_race_name}")
                    except Exception as e:
                        st.error(f"Error loading data: {e}")

            if 'session' in st.session_state and st.session_state['session'].event['EventName'] == selected_race_name:
                session = st.session_state['session']
                
                tab1, tab2, tab3, tab4 = st.tabs(["🏆 Classification", "🍩 Tyre Strategy", "📉 Lap Pace", "🌧️ Weather"])
                
                with tab1:
                    results = session.results
                    cols = ['Position', 'BroadcastName', 'TeamName', 'Points', 'Time', 'Status']
                    results_clean = results[cols].fillna(0)
                    results_clean['Position'] = results_clean['Position'].astype(int)
                    st.dataframe(results_clean.set_index('Position'), use_container_width=True)

                with tab2:
                    st.subheader("Tyre Compounds & Stint Lengths")
                    laps = session.laps
                    
                    stints = laps[["Driver", "Stint", "Compound", "LapNumber"]].groupby(
                        ["Driver", "Stint", "Compound"]
                    ).count().reset_index().rename(columns={"LapNumber": "Laps"})
                    
                    stints = stints.sort_values(by=['Driver', 'Stint'])

                    fig_tyres = px.bar(
                        stints, 
                        x="Laps", 
                        y="Driver", 
                        color="Compound", 
                        orientation='h',
                        title="Tyre Strategy History",
                        color_discrete_map={
                            "SOFT": "#FF3333", "MEDIUM": "#FFE933", "HARD": "#F0F0F0", 
                            "INTERMEDIATE": "#39B54A", "WET": "#0056D6"
                        },
                        text="Laps"
                    )
                    fig_tyres.update_layout(template="plotly_dark", height=800)
                    st.plotly_chart(fig_tyres, use_container_width=True)

                with tab3:
                    st.subheader("Lap Time Consistency (Box Plot)")
                    laps = session.laps.pick_quicklaps()
                    laps['LapTimeSec'] = laps['LapTime'].dt.total_seconds()
                    finishing_order = session.results.sort_values(by='Position')['Abbreviation'].tolist()
                    
                    fig_pace = px.box(
                        laps, 
                        x="Driver", y="LapTimeSec", color="Team",
                        category_orders={"Driver": finishing_order},
                        title="Lap Time Distribution (Lower is Better/Faster)"
                    )
                    fig_pace.update_layout(template="plotly_dark", height=600)
                    st.plotly_chart(fig_pace, use_container_width=True)

                with tab4:
                    weather = session.weather_data
                    weather['TimeMin'] = weather['Time'].dt.total_seconds() / 60
                    fig_weather = px.line(
                        weather, x="TimeMin", y=["AirTemp", "TrackTemp", "Humidity"], 
                        title="Weather Evolution During Race"
                    )
                    fig_weather.update_layout(template="plotly_dark", xaxis_title="Time (Minutes)")
                    st.plotly_chart(fig_weather, use_container_width=True)

    # --- DRIVER BATTLE ---
    elif page == "🏎️ Driver Battle":
        st.title("⚔️ Head-to-Head Telemetry")
        st.markdown("Compare the fastest laps of two drivers in detail.")
        
        if 'session' not in st.session_state:
            st.warning("Please load a race in 'Race Analysis' tab first.")
        else:
            session = st.session_state['session']
            drivers = session.results['Abbreviation'].unique()
            
            c1, c2 = st.columns(2)
            with c1: d1 = st.selectbox("Driver 1", drivers, index=0)
            with c2: d2 = st.selectbox("Driver 2", drivers, index=1)
                
            if st.button("Compare Telemetry"):
                with st.spinner("Processing Telemetry..."):
                    laps_d1 = session.laps.pick_driver(d1).pick_fastest()
                    laps_d2 = session.laps.pick_driver(d2).pick_fastest()
                    
                    if laps_d1 is None or laps_d2 is None:
                        st.error("One of the drivers has no valid lap time.")
                    else:
                        tel_d1 = laps_d1.get_car_data().add_distance()
                        tel_d2 = laps_d2.get_car_data().add_distance()
                        
                        fig_speed = go.Figure()
                        fig_speed.add_trace(go.Scatter(x=tel_d1['Distance'], y=tel_d1['Speed'], name=f"{d1} Speed", line=dict(color='cyan')))
                        fig_speed.add_trace(go.Scatter(x=tel_d2['Distance'], y=tel_d2['Speed'], name=f"{d2} Speed", line=dict(color='red')))
                        fig_speed.update_layout(
                            title=f"Speed Trace: {d1} vs {d2}", 
                            xaxis_title="Distance (m)", yaxis_title="Speed (km/h)",
                            template="plotly_dark", height=500
                        )
                        st.plotly_chart(fig_speed, use_container_width=True)
                        
                        c_throt, c_brake = st.columns(2)
                        with c_throt:
                            fig_t = go.Figure()
                            fig_t.add_trace(go.Scatter(x=tel_d1['Distance'], y=tel_d1['Throttle'], name=d1, line=dict(color='cyan')))
                            fig_t.add_trace(go.Scatter(x=tel_d2['Distance'], y=tel_d2['Throttle'], name=d2, line=dict(color='red')))
                            fig_t.update_layout(title="Throttle Application", template="plotly_dark", height=300)
                            st.plotly_chart(fig_t, use_container_width=True)
                        
                        with c_brake:
                            fig_b = go.Figure()
                            fig_b.add_trace(go.Scatter(x=tel_d1['Distance'], y=tel_d1['Brake'], name=d1, line=dict(color='cyan')))
                            fig_b.add_trace(go.Scatter(x=tel_d2['Distance'], y=tel_d2['Brake'], name=d2, line=dict(color='red')))
                            fig_b.update_layout(title="Braking Points", template="plotly_dark", height=300)
                            st.plotly_chart(fig_b, use_container_width=True)

                        st.subheader("⏱️ Time Delta")
                        delta_time, ref_tel, compare_tel = fastf1.utils.delta_time(laps_d1, laps_d2)
                        
                        fig_delta = go.Figure()
                        fig_delta.add_trace(go.Scatter(x=ref_tel['Distance'], y=delta_time, mode='lines', name=f"Gap ({d2} relative to {d1})", line=dict(color='white')))
                        fig_delta.add_hline(y=0, line_dash="dash", line_color="gray")
                        fig_delta.update_layout(
                            title=f"Time Delta (Positive means {d1} is ahead)",
                            xaxis_title="Distance (m)", yaxis_title="Delta (Seconds)",
                            template="plotly_dark"
                        )
                        st.plotly_chart(fig_delta, use_container_width=True)

    # --- ABOUT ---
    elif page == "ℹ️ About":
        st.title("About LetsGoF1")
        st.info("Built with Python & Streamlit")
        st.write("Data Source: FastF1 (Open Source)")
        st.write("Build By Danvanthram KK")

if __name__ == "__main__":

    main()
