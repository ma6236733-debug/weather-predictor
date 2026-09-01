import os
from datetime import datetime, timezone, timedelta
import requests
import streamlit as st
import pandas as pd
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("OPENWEATHER_API_KEY")

# Page Configuration
st.set_page_config(page_title="Weather Dashboard", page_icon="🌤️", layout="centered")

# Sidebar
with st.sidebar:
    st.header("API Status")
    if API_KEY:
        st.success("OpenWeather API Key Loaded", icon="✅")
    else:
        st.error("Missing API Key in .env file", icon="🚨")
    st.divider()
    st.markdown("### 👨‍💻 Developer Info")
    st.caption("Designed & Developed by **Muhammad AbuBakar**")

# App Header
st.title("🌤️ Real-Time Weather Dashboard")
city = st.text_input("Enter city name:", "London")

if st.button("Get Weather", type="primary"):
    if not API_KEY:
        st.error("Please add your OPENWEATHER_API_KEY to the .env file.")
    elif not city.strip():
        st.warning("Please enter a valid city name.")
    else:
        # Endpoints for Current Weather & 5-Day Hourly Forecast
        current_url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
        forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={API_KEY}&units=metric"
        
        try:
            with st.spinner(f"Fetching weather for {city}..."):
                current_res = requests.get(current_url)
                forecast_res = requests.get(forecast_url)
                
                c_data = current_res.json()
                f_data = forecast_res.json()

            if current_res.status_code == 200 and c_data.get("cod") == 200:
                # Basic Weather Info
                temp = round(c_data["main"]["temp"])
                feels_like = round(c_data["main"]["feels_like"])
                humidity = c_data["main"]["humidity"]
                raw_desc = c_data["weather"][0]["description"]
                weather_desc = raw_desc.capitalize()
                weather_main = c_data["weather"][0]["main"].lower()
                wind_speed = round(c_data["wind"]["speed"] * 3.6, 1) # convert m/s to km/h
                country = c_data["sys"]["country"]
                pressure = c_data["main"]["pressure"]

                # Calculate local time based on city timezone offset
                tz_offset = c_data.get("timezone", 0)
                local_time = datetime.now(timezone.utc) + timedelta(seconds=tz_offset)
                formatted_time = local_time.strftime("%A %I:%M %p")

                # --- Google Weather Header Widget Layout ---
                col_top_left, col_top_right = st.columns([2, 1])
                
                with col_top_left:
                    st.markdown(f"## ☀️ {temp}°C")
                    st.caption(f"Precipitation: 0% | Humidity: {humidity}% | Wind: {wind_speed} km/h")

                with col_top_right:
                    st.markdown(f"### Weather")
                    st.write(f"**{formatted_time}**")
                    st.write(f"*{weather_desc}*")

                st.divider()

                # --- 24-Hour Temperature Trend Chart ---
                if forecast_res.status_code == 200:
                    st.subheader("Temperature Trend")
                    hourly_list = f_data["list"][:8] # Next 24 hours (8 intervals of 3 hrs)
                    
                    chart_data = []
                    for item in hourly_list:
                        item_time = datetime.fromtimestamp(item["dt"], tz=timezone.utc) + timedelta(seconds=tz_offset)
                        chart_data.append({
                            "Time": item_time.strftime("%I %p").lstrip('0'),
                            "Temp (°C)": round(item["main"]["temp"])
                        })
                    
                    df_chart = pd.DataFrame(chart_data)
                    st.line_chart(df_chart.set_index("Time"), height=180)

                    # --- Daily Forecast Cards ---
                    st.subheader("Upcoming Forecast")
                    daily_data = f_data["list"][::8] # Pick daily intervals
                    cols = st.columns(len(daily_data))
                    
                    for idx, day in enumerate(daily_data):
                        day_time = datetime.fromtimestamp(day["dt"], tz=timezone.utc) + timedelta(seconds=tz_offset)
                        day_name = day_time.strftime("%a")
                        day_temp = round(day["main"]["temp"])
                        day_min = round(day["main"]["temp_min"])
                        
                        with cols[idx]:
                            st.caption(f"**{day_name}**")
                            st.markdown("🌤️")
                            st.write(f"{day_temp}° {day_min}°")

                st.divider()

                # --- Alert Siren Logic ---
                harsh_conditions = ["thunderstorm", "drizzle", "rain", "snow", "squall", "tornado"]
                is_harsh = any(condition in weather_main or condition in raw_desc.lower() for condition in harsh_conditions)
                
                if is_harsh or temp > 40 or temp < -5:
                    st.error(f"🚨 **RED SIREN ALERT:** Harsh Weather Detected! ({weather_desc})", icon="🚨")
                else:
                    st.success(f"🟢 **GREEN SIREN ALERT:** Weather Condition is Safe & Clear ({weather_desc})", icon="🟢")
                
                if "few clouds" in raw_desc.lower():
                    st.markdown("### ⛅ Condition: Few Clouds")

                # --- Thermal & Pressure Waves ---
                col1, col2 = st.columns(2)
                with col1:
                    st.write("### 🌡️ Thermal Condition")
                    if feels_like >= 35:
                        st.warning(f"🔥 Heat Index High ({feels_like}°C)")
                    elif 20 <= feels_like < 35:
                        st.info(f"🌤️ Comfortable ({feels_like}°C)")
                    else:
                        st.info(f"🧥 Cool ({feels_like}°C)")

                with col2:
                    st.write("### 🌊 Pressure Waves")
                    st.metric("Atmospheric Pressure", f"{pressure} hPa")

                # --- Dynamic Safety Precautions ---
                st.write("### 🛡️ Safety Precautions")
                precautions = []
                if is_harsh:
                    if "rain" in weather_main:
                        precautions.append("☔ **Carry an umbrella** and drive carefully.")
                    elif "thunderstorm" in weather_main:
                        precautions.append("🌩️ **Stay indoors** and avoid tall trees or high ground.")
                if feels_like >= 35:
                    precautions.append("💧 **Stay hydrated** and keep out of direct sun.")
                if not precautions:
                    precautions.append("✅ Weather conditions are clear and suitable for outdoors.")

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