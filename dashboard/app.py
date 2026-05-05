import sys
import os
import json
import uuid

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import folium
from streamlit_folium import st_folium
from datetime import datetime
import pandas as pd

from engine.predictive_irrigation import simulate_future, irrigation_schedule
from weather.weather_api import get_weather, get_forecast
from models.et_model import calculate_et0, calculate_etc, smart_irrigation_volume
from models.forecast import extract_forecast_features
from rl.multi_env import MultiZoneEnv
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet


# ================= SAVE / LOAD =================
DATA_FILE = "fields_data.json"

def save_fields(fields):
    with open(DATA_FILE, "w") as f:
        json.dump(fields, f, indent=2, ensure_ascii=False, default=str)

def load_fields():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            data = json.load(f)

            for field in data:
                if isinstance(field.get("last_irrigation"), str):
                    field["last_irrigation"] = datetime.fromisoformat(field["last_irrigation"])

                if isinstance(field.get("last_pump_run"), str):
                    field["last_pump_run"] = datetime.fromisoformat(field["last_pump_run"])

            return data
    return []


# ================= RL AGENT =================
def rl_agent_continuous(states):
    actions = []

    for state in states:
        moisture = state[0] * 100

        if moisture < 30:
            water = 20
        elif moisture < 40:
            water = 15
        elif moisture < 50:
            water = 10
        elif moisture < 60:
            water = 5
        else:
            water = 0

        actions.append(water)

    return actions


# ================= CONFIG =================
st.set_page_config(page_title="Smart Farm AI", layout="wide")
st.title("🌍 Smart Farm AI Dashboard")


# ================= STATE =================
if "fields" not in st.session_state:
    st.session_state.fields = load_fields()

# ✅ إضافة pump state لكل field
for f in st.session_state.fields:
    if "pump_status" not in f:
        f["pump_status"] = False
    if "last_pump_run" not in f:
        f["last_pump_run"] = None


# ================= ADD FIELD =================
st.sidebar.header("🌾 Fields Manager")

new_field_name = st.sidebar.text_input("Field Name")

if st.sidebar.button("➕ Add Field"):
    if new_field_name:
        st.session_state.fields.append({
            "id": str(uuid.uuid4()),
            "name": new_field_name,
            "lat": None,
            "lon": None,
            "area": 1000,
            "last_irrigation": datetime.now(),
            "pump_status": False,
            "last_pump_run": None
        })
        save_fields(st.session_state.fields)


# ================= CHECK =================
if len(st.session_state.fields) == 0:
    st.info("➕ Add a field first")
    st.stop()


# ================= SELECT FIELD =================
field_names = [f["name"] for f in st.session_state.fields]

selected_name = st.sidebar.selectbox("Select Field", field_names)

current_field = next(
    (f for f in st.session_state.fields if f["name"] == selected_name),
    None
)

if current_field is None:
    st.error("⚠️ Field not found")
    st.stop()


# ================= SETTINGS =================
st.sidebar.subheader("⚙️ Field Settings")

new_area = st.sidebar.number_input(
    "Area (m²)",
    min_value=1,
    value=current_field.get("area", 1000)
)

if new_area != current_field.get("area"):
    current_field["area"] = new_area
    save_fields(st.session_state.fields)


new_date = st.sidebar.datetime_input(
    "Last Irrigation",
    value=current_field.get("last_irrigation", datetime.now())
)

if new_date != current_field.get("last_irrigation"):
    current_field["last_irrigation"] = new_date
    save_fields(st.session_state.fields)


# ================= MAP =================
st.subheader("🗺️ Farm Map")

m = folium.Map(location=[30, 31], zoom_start=6)

for field in st.session_state.fields:
    if field["lat"] is not None:
        color = "red" if field["name"] == selected_name else "green"

        folium.Marker(
            [field["lat"], field["lon"]],
            popup=field["name"],
            icon=folium.Icon(color=color)
        ).add_to(m)

map_data = st_folium(m, height=450)

if map_data and map_data.get("last_clicked"):
    current_field["lat"] = map_data["last_clicked"]["lat"]
    current_field["lon"] = map_data["last_clicked"]["lng"]
    save_fields(st.session_state.fields)


# ================= LOCATION CHECK =================
if not current_field.get("lat") or not current_field.get("lon"):
    st.info("📍 Please select location on map")
    st.stop()


# ================= WEATHER =================
weather = get_weather(current_field["lat"], current_field["lon"])
forecast = get_forecast(current_field["lat"], current_field["lon"])

if not weather:
    st.error("⚠️ Weather API failed")
    st.stop()


# ================= ET =================
# 🔥 Fix: Estimated radiation if API returns 0
# 🔥 Fix: Estimated radiation if API returns 0
raw_radiation = weather.get("radiation", 0)

if raw_radiation and raw_radiation > 0:
    radiation = raw_radiation
else:
    radiation = max(0, (weather.get("temp", 0) - 5) * 80)
    
et0 = calculate_et0(
    weather.get("temp", 0),
    weather.get("humidity", 0),
    weather.get("wind", 0),
    radiation
)

etc = calculate_etc(et0)

f_et, f_rain = extract_forecast_features(forecast)

f_et_value = sum(f_et) if isinstance(f_et, list) else f_et
f_rain_value = sum(f_rain) if isinstance(f_rain, list) else f_rain


# ================= SMART WATER =================
current_moisture = 55

water_mm, water_liters = smart_irrigation_volume(
    etc,
    current_field["area"],
    current_moisture,
    f_rain_value
)

area_factor = 1 + (current_field["area"] / 10000)
water_liters *= area_factor


# ================= TIME =================
hours_since_irrigation = (
    datetime.now() - current_field["last_irrigation"]
).total_seconds() / 3600


# ================= TABS =================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🧠 Dashboard",
    "🗺️ Map",
    "📊 Analysis",
    "🔮 Predictive Irrigation",
    "🚿 Pump Control"
])


# ================= TAB 1 =================
with tab1:
    st.subheader(f"🧠 Dashboard - {current_field['name']}")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("🌡 Temp", f"{weather['temp']:.1f} °C")
    col2.metric("💧 Humidity", f"{weather['humidity']} %")
    col3.metric("🌬 Wind", f"{weather['wind']:.1f} m/s")
    col4.metric("☀️ Radiation", f"{radiation:.0f} W/m²")

    st.divider()

    col1, col2, col3 = st.columns(3)
    col1.metric("🌱 ETc", f"{etc:.2f}")
    col2.metric("💧 Water Depth", f"{water_mm:.2f} mm")
    col3.metric("🚜 Total Water", f"{water_liters:.0f} L")

    if hours_since_irrigation > 24:
        st.warning("🚨 Irrigation Needed")
    else:
        st.success("✅ No Irrigation Needed")

    
# ================= TAB 2 =================
with tab2:
    st.subheader("🗺️ Map View")
    st_folium(m, height=500)


# ================= TAB 3 =================
with tab3:
    st.subheader("📊 Smart Farm Advanced Analysis")

    # ================= BASIC DATA =================
    st.markdown("### 📌 Field Overview")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("🌡 Temperature", f"{weather['temp']:.1f} °C")
    col2.metric("💧 Humidity", f"{weather['humidity']} %")
    col3.metric("🌬 Wind Speed", f"{weather['wind']:.1f} m/s")
    col4.metric("☀️ Radiation", f"{radiation:.0f} W/m²")

    st.divider()

    # ================= WATER STRESS INDEX =================
    st.markdown("### 💧 Water Stress Index")

    stress_score = (60 - current_moisture) + (etc * 5)

    if stress_score < 20:
        stress_level = "🟢 Low"
    elif stress_score < 40:
        stress_level = "🟡 Medium"
    else:
        stress_level = "🔴 High"

    st.metric("Stress Score", f"{stress_score:.2f}")
    st.metric("Stress Level", stress_level)

    st.divider()

    # ================= IRRIGATION EFFICIENCY =================
    st.markdown("### 🚜 Irrigation Efficiency")

    ideal_water = etc * current_field["area"]
    efficiency = (ideal_water / (water_liters + 1)) * 100

    efficiency = min(100, efficiency)

    st.metric("Ideal Water Need", f"{ideal_water:.0f} L")
    st.metric("Actual Water Used", f"{water_liters:.0f} L")
    st.metric("Efficiency", f"{efficiency:.1f} %")

    if efficiency > 85:
        st.success("✅ Excellent irrigation efficiency")
    elif efficiency > 60:
        st.warning("⚠️ Moderate efficiency")
    else:
        st.error("❌ Low efficiency — optimize irrigation")

    st.divider()

    # ================= MOISTURE ANALYSIS =================
    st.markdown("### 🌱 Soil Moisture Insight")

    moisture_status = (
        "Dry 🔴" if current_moisture < 35 else
        "Optimal 🟢" if current_moisture < 65 else
        "Wet 🔵"
    )

    st.metric("Soil Moisture", f"{current_moisture:.1f}%")
    st.metric("Status", moisture_status)

    st.divider()

    # ================= WEATHER IMPACT ANALYSIS =================
    st.markdown("### 🌦 Weather Impact Analysis")

    evap_risk = (radiation * 0.5 + weather['wind'] * 10)

    if evap_risk > 80:
        risk_level = "🔴 High evaporation risk"
    elif evap_risk > 50:
        risk_level = "🟡 Medium risk"
    else:
        risk_level = "🟢 Low risk"

    st.metric("Evaporation Risk Score", f"{evap_risk:.1f}")
    st.write(risk_level)

    st.divider()

    # ================= FUTURE INSIGHT =================
    st.markdown("### 🔮 3-Day Irrigation Forecast")

    future = simulate_future(current_moisture, forecast)

    df_future = pd.DataFrame(future)

    st.line_chart(df_future.set_index("day")["moisture"])

    # تحليل الأيام الحرجة
    dry_days = df_future[df_future["moisture"] < 40]

    if len(dry_days) > 0:
        st.warning(f"⚠️ {len(dry_days)} days predicted below safe moisture level")

    st.dataframe(df_future)

    st.divider()

    # ================= FINAL DECISION =================
    st.markdown("### 🎯 AI Recommendation")

    if stress_score > 40 and efficiency < 70:
        st.error("🚨 Immediate irrigation optimization required")
    elif stress_score > 25:
        st.warning("⚠️ Irrigation needed soon")
    else:
        st.success("✅ Field condition is stable")

    st.dataframe(pd.DataFrame(st.session_state.fields))


# ================= TAB 4 =================
with tab4:
    st.subheader("🔮 Predictive Irrigation System")

    # ================= FUTURE SIMULATION =================
    future = simulate_future(current_moisture, forecast)
    schedule = irrigation_schedule(future, current_field["area"])

    df_future = pd.DataFrame(future)

    st.markdown("### 🌱 Soil Moisture Forecast")
    st.line_chart(df_future.set_index("day")["moisture"])

    st.markdown("### 📅 Irrigation Schedule")
    st.table(pd.DataFrame(schedule))

    st.divider()

    # ================= SMART INSIGHT =================
    st.subheader("🧠 Smart Irrigation Insight")

    risk_score = (
        (60 - current_moisture) +
        (radiation * 0.05) +
        (weather["wind"] * 2)
    )

    if risk_score < 20:
        risk = "🟢 Safe"
    elif risk_score < 40:
        risk = "🟡 Medium"
    else:
        risk = "🔴 High"

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Risk Score", f"{risk_score:.1f}")

    with col2:
        st.metric("Irrigation Risk", risk)

    st.divider()

    # ================= WATER EFFICIENCY =================
    st.subheader("💧 Water Efficiency Insight")

    ideal_water = etc * current_field["area"]
    efficiency = (ideal_water / (water_liters + 1)) * 100
    efficiency = min(100, efficiency)

    st.metric("Efficiency", f"{efficiency:.1f} %")

    if efficiency > 80:
        st.success("✅ System is optimized")
    elif efficiency > 60:
        st.warning("⚠️ Needs adjustment")
    else:
        st.error("❌ Inefficient irrigation")


# ================= TAB 5 =================
with tab5:
    st.subheader("🚿 Smart Pump Control")

    st.markdown("### ⚙️ Manual Control")

    col1, col2 = st.columns(2)

    with col1:
        water_amount = st.slider("💧 Water Amount (Liters)", 0, 5000, 1000)

    with col2:
        duration = st.slider("⏱ Duration (minutes)", 1, 120, 10)

    col1, col2 = st.columns(2)

    with col1:
        if st.button("▶️ Start Pump"):
            current_field["pump_status"] = True
            current_field["last_pump_run"] = datetime.now()
            current_field["last_irrigation"] = datetime.now()
            save_fields(st.session_state.fields)
            st.success(f"🚿 Pump started: {water_amount}L for {duration} min")

    with col2:
        if st.button("⛔ Stop Pump"):
            current_field["pump_status"] = False
            save_fields(st.session_state.fields)
            st.warning("Pump stopped")

    st.divider()

    st.markdown("### 📊 Pump Status")

    if current_field.get("pump_status"):
        st.success("🟢 Pump is RUNNING")
    else:
        st.error("🔴 Pump is OFF")

    if current_field.get("last_pump_run"):
        st.info(f"Last run: {current_field['last_pump_run']}")

    st.divider()

    st.markdown("### 🤖 Auto Mode (AI Control)")

    if st.button("🧠 Run Smart Irrigation"):
        if water_liters > 0:
            current_field["pump_status"] = True
            current_field["last_pump_run"] = datetime.now()
            current_field["last_irrigation"] = datetime.now()
            save_fields(st.session_state.fields)

            st.success(f"""
🤖 AI Activated Pump  
💧 كمية المياه: {water_liters:.0f} لتر  
🌱 بناءً على ET + Forecast
""")
        else:
            st.info("✅ No irrigation needed now")

    st.divider()

    st.markdown("### 🤖 RL Control")

    if st.button("⚡ Run RL Irrigation"):
        env = MultiZoneEnv(n_zones=1)
        states = env.reset()
        actions = rl_agent_continuous(states)

        water_rl = actions[0]

        if water_rl > 0:
            current_field["pump_status"] = True
            current_field["last_pump_run"] = datetime.now()
            current_field["last_irrigation"] = datetime.now()
            save_fields(st.session_state.fields)

            st.success(f"🚿 RL Pump: {water_rl} Liters")
        else:
            st.info("RL decided no irrigation")


# ================= PDF =================
def generate_report(fields):
    doc = SimpleDocTemplate("farm_report.pdf")
    styles = getSampleStyleSheet()

    content = []
    for f in fields:
        content.append(
            Paragraph(
                f"Field: {f['name']} | Area: {f['area']} m²",
                styles["Normal"]
            )
        )

    doc.build(content)


if st.button("📄 Export PDF"):
    generate_report(st.session_state.fields)
    st.success("Report Generated ✔")