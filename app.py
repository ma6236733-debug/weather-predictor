import os
from datetime import datetime, timezone, timedelta
import requests
import streamlit as st
import pandas as pd
from dotenv import load_dotenv
from streamlit_autorefresh import st_autorefresh

# Load environment variables
load_dotenv()
API_KEY = os.getenv("OPENWEATHER_API_KEY")

# Page Configuration
st.set_page_config(page_title="Weather Dashboard", page_icon="🌤️", layout="centered")

# Sidebar - API Status, Refresh Timer & Developer Info
with st.sidebar:
    st.header("API Status")
    if API_KEY:
        st.success("OpenWeather API Key Loaded", icon="✅")
    else:
        st.error("Missing API Key in .env file", icon="🚨")
        
    st.divider()
    st.header("🔄 Auto-Refresh")
    refresh_minutes = st.slider("Select Refresh Interval (Minutes):", min_value=1, max_value=30, value=5)
    
    # Auto-refresh component (converts minutes to milliseconds)
    count = st_autorefresh(interval=refresh_minutes * 60 * 1000, key="weather_auto_refresh")
    st.caption(f"Last updated / Refresh count: **{count}**")

    st.divider()
    st.markdown("### 👨‍💻 Developer Info")
    st.caption("Designed & Developed by **Muhammad AbuBakar**")

# App Header
st.title("🌤️ Real-Time Weather Dashboard")

# Input Section
col_input, col_btn = st.columns([3, 1])
with col_input:
    city = st.text_input("Enter city name:", "London")
with col_btn:
    st.write(" ")
    fetch_data = st.button("Get Weather", type="primary", use_container_width=True)

if fetch_data or city:
    if not API_KEY:
        st.error("Please add your OPENWEATHER_API_KEY to the .env file.")
    elif not city.strip():
        st.warning("Please enter a valid city name.")
    else:
        # API Endpoints
        current_url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
        forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={API_KEY}&units=metric"
        
        try:
            with st.spinner(f"Fetching live weather for {city}..."):
                current_res = requests.get(current_url, headers={"Cache-Control": "no-cache"})
                forecast_res = requests.get(forecast_url, headers={"Cache-Control": "no-cache"})
                
                c_data = current_res.json()
                f_data = forecast_res.json()

            if current_res.status_code == 200 and c_data.get("cod") == 200:
                # Core Metrics
                temp = round(c_data["main"]["temp"])
                feels_like = round(c_data["main"]["feels_like"])
                humidity = c_data["main"]["humidity"]
                raw_desc = c_data["weather"][0]["description"].lower()
                weather_desc = raw_desc.capitalize()
                weather_main = c_data["weather"][0]["main"].lower()
                wind_speed = round(c_data["wind"]["speed"] * 3.6, 1)  # Convert m/s to km/h
                country = c_data["sys"]["country"]
                pressure = c_data["main"]["pressure"]
                
                # Check for live precipitation volume from API
                rain_data = c_data.get("rain", {})
                rain_1h = rain_data.get("1h", 0)

                # Timezone & Local Time
                tz_offset = c_data.get("timezone", 0)
                local_time = datetime.now(timezone.utc) + timedelta(seconds=tz_offset)
                formatted_time = local_time.strftime("%A %I:%M %p")

                # --- Header Widget Display ---
                col_top_left, col_top_right = st.columns([2, 1])
                
                with col_top_left:
                    st.markdown(f"## ☀️ {temp}°C")
                    st.caption(f"Rain Volume: {rain_1h} mm/h | Humidity: {humidity}% | Wind: {wind_speed} km/h")

                with col_top_right:
                    st.markdown("### Weather")
                    st.write(f"**{formatted_time}**")
                    st.write(f"*{weather_desc}*")

                st.divider()

                # --- Alert & Siren Logic ---
                harsh_keywords = ["thunderstorm", "drizzle", "rain", "snow", "squall", "tornado", "shower"]
                is_harsh = any(keyword in weather_main or keyword in raw_desc for keyword in harsh_keywords) or rain_1h > 0
                
                if is_harsh or temp > 40 or temp < -5:
                    st.error(f"🚨 **RED SIREN ALERT:** Adverse/Harsh Weather Detected! ({weather_desc})", icon="🚨")
                else:
                    st.success(f"🟢 **GREEN SIREN ALERT:** Weather Condition is Safe & Clear ({weather_desc})", icon="🟢")
                
                if "few clouds" in raw_desc:
                    st.markdown("### ⛅ Condition: Few Clouds")

                # --- Temperature Trend Line Chart ---
                if forecast_res.status_code == 200 and f_data.get("cod") == "200":
                    st.subheader("24-Hour Temperature Trend")
                    hourly_list = f_data["list"][:8]
                    
                    chart_data = []
                    for item in hourly_list:
                        item_time = datetime.fromtimestamp(item["dt"], tz=timezone.utc) + timedelta(seconds=tz_offset)
                        chart_data.append({
                            "Time": item_time.strftime("%I %p").lstrip('0'),
                            "Temp (°C)": round(item["main"]["temp"])
                        })
                    
                    df_chart = pd.DataFrame(chart_data)
                    st.line_chart(df_chart.set_index("Time"), height=180)

                    # --- Daily Cards ---
                    st.subheader("Upcoming Forecast")
                    daily_data = f_data["list"][::8]
                    cols = st.columns(len(daily_data))
                    
                    for idx, day in enumerate(daily_data):
                        day_time = datetime.fromtimestamp(day["dt"], tz=timezone.utc) + timedelta(seconds=tz_offset)
                        day_name = day_time.strftime("%a")
                        day_temp = round(day["main"]["temp"])
                        day_min = round(day["main"]["temp_min"])
                        
                        with cols[idx]:
                            st.caption(f"**{day_name}**")
                            st.markdown("🌤️")
                            st.write(f"{day_temp}° / {day_min}°")

                st.divider()

                # --- Thermal Conditions & Pressure Waves ---
                col1, col2 = st.columns(2)
                with col1:
                    st.write("### 🌡️ Thermal Condition")
                    if feels_like >= 35:
                        st.warning(f"🔥 Heat Index High ({feels_like}°C)")
                    elif 20 <= feels_like < 35:
                        st.info(f"🌤️ Comfortable ({feels_like}°C)")
                    elif 10 <= feels_like < 20:
                        st.info(f"🧥 Cool ({feels_like}°C)")
                    else:
                        st.warning(f"❄️ Cold ({feels_like}°C)")

                with col2:
                    st.write("### 🌊 Atmospheric Pressure")
                    st.metric("Pressure Level", f"{pressure} hPa")

                st.divider()

                # --- Safety Precautions ---
                st.write("### 🛡️ Safety Precautions")
                precautions = []
                
                if "rain" in weather_main or "drizzle" in weather_main or "shower" in weather_main or rain_1h > 0:
                    precautions.append("☔ **Active Rain:** Carry an umbrella or raincoat before stepping outside.")
                    precautions.append("🚗 **Slippery Roads:** Drive below standard speed limits.")
                elif "thunderstorm" in weather_main:
                    precautions.append("🌩️ **Thunderstorm Warning:** Stay indoors and avoid metallic or high structures.")
                elif "snow" in weather_main:
                    precautions.append("❄️ **Snow / Freezing:** Wear anti-slip footwear and insulated clothing.")
                
                if feels_like >= 35:
                    precautions.append("💧 **Extreme Heat:** Hydrate frequently and avoid peak sun hours.")
                
                if not precautions:
                    precautions.append("✅ **Optimal Conditions:** Safe to enjoy outdoor activities.")

                for p in precautions:
                    st.markdown(f"- {p}")

            else:
                st.error(f"Error: {c_data.get('message', 'City not found.').capitalize()}")
                
        except Exception as e:
            st.error(f"Connection Error: {e}")

# Footer Section
st.divider()
st.markdown(
    """
    <div style="text-align: center; color: #888888; padding: 10px;">
        <p>✨ <strong>Designed & Developed by Muhammad AbuBakar</strong> ✨</p>
        <p><i>Welcome to the Real-Time Weather Predictor & Monitoring Dashboard!</i></p>
    </div>
    """, 
    unsafe_allow_html=True
)