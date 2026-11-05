# app.py
import streamlit as st
from ultralytics import YOLO
from PIL import Image
import numpy as np
import cv2
import os
import json
import base64
import html
from datetime import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

import smtplib
from email.mime.text import MIMEText
import requests
from gtts import gTTS 
import io  
import pandas as pd 

from dotenv import load_dotenv

# Load environment variables
load_dotenv()
ALERT_RECIPIENT = os.getenv("ALERT_EMAIL", "tahazibtahazu@gmail.com")

# Must be the first Streamlit command in the script
st.set_page_config(
    page_title="Crowd Density Detection - Smart Safety",
    page_icon="👥",
    layout="centered",
)

# ==============================
# 📧 EMAIL (GMAIL SMTP)
# ==============================
def send_email(to_email, subject, body):
    """Send alert email via Gmail (using App Password)."""
    EMAIL_USER = os.getenv("EMAIL_USER")
    EMAIL_PASS = os.getenv("EMAIL_PASS")

    if not EMAIL_USER or not EMAIL_PASS:
        print("❌ Gmail credentials missing.")
        return

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_USER
    msg["To"] = to_email

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASS)
            server.send_message(msg)
        print("✅ Email sent successfully!")
    except Exception as e:
        print("⚠ Error sending email:", e)

# ==============================
# 💬 TELEGRAM ALERT (FREE)
# ==============================
def send_telegram_alert(message):
    """Send a free alert message via Telegram bot."""
    bot_token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not bot_token or not chat_id:
        print("❌ Telegram credentials missing.")
        return

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    try:
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            print("✅ Telegram alert sent successfully!")
        else:
            print(f"⚠ Telegram failed: {response.text}")
    except Exception as e:
        print("⚠ Error sending Telegram alert:", e)

def send_telegram_incident_report(
    event_name,
    current_count,
    risk_level,
    timestamp,
    safety_threshold,
    warning_threshold,
    danger_threshold,
    predicted_count=None,
):
    """Send a readable manual-emergency incident summary to Telegram."""
    forecast_line = (
        f"Predicted crowd: {predicted_count} people\n"
        if predicted_count is not None
        else "Predicted crowd: Not available\n"
    )
    message = (
        "🚨 MANUAL EMERGENCY ALERT\n\n"
        f"Event: {event_name or 'Not specified'}\n"
        f"Current crowd: {current_count if current_count is not None else 'Not available'} people\n"
        f"Risk level: {risk_level or 'Not available'}\n"
        f"Time: {timestamp or datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        "SAFETY THRESHOLDS\n"
        f"Safe: up to {safety_threshold} people\n"
        f"Warning: up to {warning_threshold} people\n"
        f"Danger: above {danger_threshold} people\n\n"
        f"{forecast_line}"
        "REQUIRED ACTION\n"
        "Move people calmly toward the nearest safe exit. "
        "Keep emergency routes clear and follow security instructions.\n\n"
        "Open the Crowd Safety dashboard to view the complete charts, "
        "photos, density history, and downloadable report."
    )
    send_telegram_alert(message)

# ==============================
# 🛑 MAIN SOS TRIGGER
# ==============================
def trigger_sos(event_name, event_location, current_count, predicted_crowd_count, danger_threshold):
    """Auto SOS + Evacuation when critical crowd detected."""
    if predicted_crowd_count > danger_threshold:
        st.error("🚨 AI Alert: Critical crowd density detected! Activating SOS protocol...")

        # --- AUTO EMAIL ALERT ---
        send_email(
            to_email=ALERT_RECIPIENT,
            subject="🚨 SOS: Overcrowding Alert",
            body=f"""
            Immediate attention required!
            Crowd risk has exceeded safety limits.

            Event: {event_name}
            Current Count: {current_count}
            Predicted in 10 min: {predicted_crowd_count}
            Location: {event_location}
            """
        )

        # --- TELEGRAM ALERT ---
        send_telegram_alert("🚨 SOS Alert! Overcrowding detected. Please guide people to exits immediately.")
        send_telegram_alert("🚨 AI Alert: Crowd density critical! Evacuation protocol activated.")

        # --- VOICE ANNOUNCEMENT ---
        sos_message = "Attention! Overcrowding detected. Please move calmly towards the nearest exit. Follow security instructions."
        tts = gTTS(sos_message)
        sos_audio = io.BytesIO()
        tts.write_to_fp(sos_audio)
        sos_audio.seek(0)
        st.audio(sos_audio, format='audio/mp3', autoplay=True)

        # --- SAFE ROUTE MAP ---
        st.markdown("### 🗺 Safe Evacuation Route")
        st.map(pd.DataFrame({
            'lat': [12.9716, 12.9720, 12.9730],  # Example path
            'lon': [77.5946, 77.5950, 77.5960]
        }))
        st.success("✅ Safe exit routes shown in green. Security teams notified.")

# ===================== GLOBAL EMERGENCY BUTTON =====================
from gtts import gTTS
import io , time
import base64
import streamlit as st

# Keep track of emergency state between clicks
if "emergency_active" not in st.session_state:
    st.session_state.emergency_active = False
if "latest_analysis" not in st.session_state:
    st.session_state.latest_analysis = {}

st.sidebar.markdown("---")
st.sidebar.header("🚨 Emergency Control Center")

# Dynamic button label + color
button_label = "🔴 ACTIVATE EMERGENCY ALERT" if not st.session_state.emergency_active else "🟢 DEACTIVATE EMERGENCY ALERT"
button_style = """
<style>
div[data-testid="stSidebar"] button {
    background-color: %s !important;
    color: white !important;
    font-weight: bold;
    border-radius: 8px;
    height: 3em;
}
</style>
""" % ("red" if not st.session_state.emergency_active else "green")
st.markdown(button_style, unsafe_allow_html=True)

# Toggle button
if st.sidebar.button(button_label, width="stretch"):
    st.session_state.emergency_active = not st.session_state.emergency_active
    if st.session_state.emergency_active:
        latest = st.session_state.latest_analysis
        send_telegram_incident_report(
            event_name=latest.get("event_name"),
            current_count=latest.get("count"),
            risk_level=latest.get("risk_level"),
            timestamp=latest.get("timestamp"),
            safety_threshold=st.session_state.get("safety_threshold", 10),
            warning_threshold=st.session_state.get("warning_threshold", 15),
            danger_threshold=st.session_state.get("danger_threshold", 20),
            predicted_count=latest.get("predicted_count"),
        )
        st.sidebar.success("✅ Telegram emergency report sent.")

# ===================== WHEN EMERGENCY IS ACTIVE =====================
if st.session_state.emergency_active:
    emergency_message = "Attention please! Emergency detected. High crowd risk! Please move to safety immediately!"

    # Big banner
    st.markdown(
        """
        <div style='text-align:center; color:white; background-color:red;
             padding:15px; font-size:26px; border-radius:10px;'>
             🚨 EMERGENCY ALERT ACTIVATED 🚨<br>
             <span style='font-size:20px;'>High crowd risk detected! Evacuate safely!</span>
        </div>
        """, unsafe_allow_html=True
    )

    # Voice message (auto plays)
    tts = gTTS(emergency_message)
    audio_bytes = io.BytesIO()
    tts.write_to_fp(audio_bytes)
    audio_bytes.seek(0)
    b64_audio = base64.b64encode(audio_bytes.read()).decode()
    st.markdown(
        f"""
        <audio autoplay>
            <source src="data:audio/mp3;base64,{b64_audio}" type="audio/mp3">
        </audio>
        """,
        unsafe_allow_html=True
    )

    # Optional looping siren (replace with your own MP3 if desired)
    siren_base64 = """
    UklGRoQAAABXQVZFZm10IBAAAAABAAEAESsAACJWAAACABAAZGF0YZAAAAAA//8AAP//AAD//wAA//8AAP//AAD//wAA//8AAP//AAD//wAA
    """
    st.markdown(
        f"""
        <audio autoplay loop>
            <source src="data:audio/wav;base64,{siren_base64}" type="audio/wav">
        </audio>
        """,
        unsafe_allow_html=True
    )

    # Flashing text
    st.markdown(
        """
        <style>
        @keyframes blink { 50% { opacity: 0; } }
        .blink {
          animation: blink 1s step-start infinite;
          color: red;
          font-size: 22px;
          text-align: center;
          font-weight: bold;
        }
        </style>
        <div class='blink'>🚨 EMERGENCY IN PROGRESS — AUTHORITIES NOTIFIED 🚨</div>
        """,
        unsafe_allow_html=True
    )

    st.warning("⚠ Emergency protocol active. All systems locked for safety monitoring.")
else:
    st.sidebar.success("✅ System Normal — No emergency detected.")
# ===================== DATA STORAGE SETUP =====================
DATA_DIR = "crowd_data"
EVENTS_FILE = os.path.join(DATA_DIR, "events.json")
IMAGES_DIR = os.path.join(DATA_DIR, "images")
ALERTS_FILE = os.path.join(DATA_DIR, "alerts.json")

# Create directories if they don't exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)

# Initialize events file if it doesn't exist
if not os.path.exists(EVENTS_FILE):
    with open(EVENTS_FILE, 'w') as f:
        json.dump([], f)

# Initialize alerts file if it doesn't exist
if not os.path.exists(ALERTS_FILE):
    with open(ALERTS_FILE, 'w') as f:
        json.dump([], f)

# ===================== DATA FUNCTIONS =====================
def load_events():
    """Load all event records from JSON file."""
    with open(EVENTS_FILE, 'r') as f:
        return json.load(f)

def save_event(event_name, count, timestamp, image_path):
    """Save a new event record."""
    events = load_events()
    events.append({
        "event_name": event_name,
        "people_count": count,
        "timestamp": timestamp,
        "image_path": image_path
    })
    with open(EVENTS_FILE, 'w') as f:
        json.dump(events, f, indent=2)

def get_event_data(event_name):
    """Get all records for a specific event."""
    events = load_events()
    return [e for e in events if e["event_name"].lower() == event_name.lower()]

def load_alerts():
    """Load all alert records from JSON file."""
    with open(ALERTS_FILE, 'r') as f:
        return json.load(f)

def save_alert(event_name, count, timestamp, risk_level, notifications_sent):
    """Save a new alert record."""
    alerts = load_alerts()
    alerts.append({
        "event_name": event_name,
        "people_count": count,
        "timestamp": timestamp,
        "risk_level": risk_level,
        "notifications_sent": notifications_sent
    })
    with open(ALERTS_FILE, 'w') as f:
        json.dump(alerts, f, indent=2)

# ===================== HEADER =====================
st.title("👥 Smart Crowd Detection & Risk Awareness")
st.markdown("""
This app detects people in images using a trained YOLOv8 model and classifies the situation as:
- 🟢 Low (Safe)
- 🟡 Moderate
- 🔴 High Risk (Crowded)

It also tracks crowd density over time for specific events and provides safety suggestions.
""")

# ===================== LOAD MODEL =====================
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
configured_model_path = os.getenv("YOLO_MODEL_PATH")
MODEL_PATH = configured_model_path or os.path.join(PROJECT_DIR, "best.pt")

if not os.path.exists(MODEL_PATH):
    local_default_model = os.path.join(PROJECT_DIR, "yolov8n.pt")
    MODEL_PATH = local_default_model if os.path.exists(local_default_model) else "yolov8n.pt"

@st.cache_resource
def load_model():
    if os.path.basename(MODEL_PATH) == "yolov8n.pt":
        st.info("Using the local YOLOv8 COCO weights. Add best.pt or set YOLO_MODEL_PATH to use custom trained weights.")
    return YOLO(MODEL_PATH)

model = load_model()

# ===================== AWARENESS IMAGES =====================
st.subheader("🚨 Crowd Awareness & Safety Examples")
awareness_images = [
    ("RCB STAMPEDE", os.getenv('AWARE_IMG_1', os.path.join('interface images', '1.jpeg'))),
    ("RCB STAMPEDE", os.getenv('AWARE_IMG_2', os.path.join('interface images', '2.jpeg'))),
    ("RCB STAMPEDE", os.getenv('AWARE_IMG_3', os.path.join('interface images', '3.jpeg'))),
]

cols = st.columns(3)
for (label, img_url), col in zip(awareness_images, cols):
    if not os.path.exists(img_url):
        continue
    with col:
        st.image(img_url, caption=label, width='stretch')

st.markdown("---")

# ===================== MODE SELECTION =====================
st.header("📊 Select Mode")
# Use session state to hold the selected mode so buttons act like toggle tabs
if "mode" not in st.session_state:
    st.session_state.mode = "📸 Capture & Analyze New Image"

st.markdown("Choose what you want to do:")
cols = st.columns(4)
options = [
    "📸 Capture & Analyze New Image",
    "🔍 Search Event History",
    "🚨 View Alert History",
    "🗺 Location Hotspot Map",
]

for col, opt in zip(cols, options):
    if col.button(opt, key=f"btn_{opt}"):
        st.session_state.mode = opt

# Expose the selected mode (used by existing logic below)
mode = st.session_state.mode

# ===================== SIDEBAR THRESHOLD =====================
crowd_threshold = st.sidebar.slider("Crowd threshold (# people)", 1, 200, 20)

# ---------------------
# 🧩 Step 1 — Define safety thresholds (configurable in sidebar)
# ---------------------
st.sidebar.markdown("### ⚖️ Auto-Alert Thresholds")
safety_threshold = st.sidebar.number_input("Safe threshold (crowd)", min_value=1, max_value=1000, value=10, step=1)
warning_threshold = st.sidebar.number_input(
    "Warning threshold (crowd)",
    min_value=safety_threshold + 1,
    max_value=1000,
    value=max(15, safety_threshold + 1),
    step=1,
)
danger_threshold = st.sidebar.number_input(
    "Danger threshold (crowd)",
    min_value=warning_threshold + 1,
    max_value=1000,
    value=max(20, warning_threshold + 1),
    step=1,
)
st.session_state.safety_threshold = safety_threshold
st.session_state.warning_threshold = warning_threshold
st.session_state.danger_threshold = danger_threshold

# Sidebar toggle for emergency features
st.sidebar.markdown("---")
st.sidebar.subheader("🚨 Emergency Features")
enable_alerts = st.sidebar.checkbox("Enable Emergency Alerts", value=True)
enable_notifications = st.sidebar.checkbox("Enable Notification Simulation", value=True)

# ===================== DETECTION =====================
def detect_people(image):
    """Run YOLO detection and return people count + annotated image."""
    results = model.predict(image, imgsz=640, conf=0.3, iou=0.45, verbose=False)
    for r in results:
        people_boxes = [box for box in r.boxes if model.names[int(box.cls[0])] in {"person", "people"}]
        count = len(people_boxes)
        annotated = r.plot()
        return count, annotated

# ===================== RISK EVALUATION =====================
def classify_crowd(count, safe_limit, warning_limit, danger_limit):
    """Classify a crowd using the current sidebar thresholds."""
    if count == 0:
        return "No people", "⚪", "No people detected in the image."
    elif count <= safe_limit:
        return "Low", "🟢", "The area looks safe and not crowded."
    elif count <= warning_limit:
        return "Moderate", "🟡", "Be cautious; the area is moderately crowded."
    else:
        return "High", "🔴", "High risk! Too many people in one place — potential stampede danger."

def show_analysis_diagram():
    """Show a simple visual explanation of the monitoring and prediction workflow."""
    st.markdown(
        """
        <h3 style="color:#38bdf8;margin:18px 0 12px;">
          🔄 How the Crowd-Risk Analysis Works
        </h3>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div style="display:flex;align-items:center;justify-content:center;gap:8px;
                    flex-wrap:wrap;margin:12px 0 22px;">
          <div style="background:#e8f1ff;border:2px solid #4c78a8;border-radius:10px;
                      color:#102a43;padding:12px;text-align:center;min-width:125px;">
            <b style="color:#102a43;">📸 Image</b><br><small style="color:#243b53;">Upload / camera</small>
          </div>
          <div style="font-size:25px;color:#38bdf8;">➡</div>
          <div style="background:#eaf7ea;border:2px solid #59a14f;border-radius:10px;
                      color:#123b1a;padding:12px;text-align:center;min-width:125px;">
            <b style="color:#123b1a;">🧠 YOLOv8</b><br><small style="color:#1f5130;">Detect people</small>
          </div>
          <div style="font-size:25px;color:#38bdf8;">➡</div>
          <div style="background:#fff4df;border:2px solid #f28e2b;border-radius:10px;
                      color:#5c2d00;padding:12px;text-align:center;min-width:125px;">
            <b style="color:#5c2d00;">🔢 Count</b><br><small style="color:#7c3f00;">Measure crowd</small>
          </div>
          <div style="font-size:25px;color:#38bdf8;">➡</div>
          <div style="background:#fce8e8;border:2px solid #e15759;border-radius:10px;
                      color:#5b1111;padding:12px;text-align:center;min-width:125px;">
            <b style="color:#5b1111;">⚠️ Risk</b><br><small style="color:#7f1d1d;">Low / Moderate / High</small>
          </div>
          <div style="font-size:25px;color:#38bdf8;">➡</div>
          <div style="background:#f1e8ff;border:2px solid #9c6ade;border-radius:10px;
                      color:#32115f;padding:12px;text-align:center;min-width:125px;">
            <b style="color:#32115f;">📈 Forecast</b><br><small style="color:#4c1d95;">Next 60 minutes</small>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def show_event_analytics(df, safe_limit, warning_limit, danger_limit):
    """Render understandable frequency and risk charts for one event."""
    chart_df = df.copy()
    chart_df["risk_level"] = chart_df["people_count"].apply(
        lambda value: classify_crowd(
            value, safe_limit, warning_limit, danger_limit
        )[0]
    )
    chart_df["observation_time"] = chart_df["timestamp"].dt.strftime("%H:%M")
    risk_order = ["No people", "Low", "Moderate", "High"]
    risk_counts = (
        chart_df["risk_level"]
        .value_counts()
        .reindex(risk_order, fill_value=0)
        .reset_index()
    )
    risk_counts.columns = ["risk_level", "observations"]

    st.markdown("### 📊 Crowd Frequency & Risk Overview")
    st.caption(
        "Use these charts to see how often crowd levels were recorded and how the "
        "observations are distributed across safety categories."
    )

    col1, col2 = st.columns(2)
    with col1:
        frequency_fig = px.histogram(
            chart_df,
            x="people_count",
            nbins=max(5, min(15, chart_df["people_count"].nunique())),
            text_auto=True,
            color_discrete_sequence=["#4c78a8"],
            labels={"people_count": "People detected", "count": "Observations"},
            title="🔢 Frequency of Detected Crowd Sizes",
        )
        for threshold, color, label in [
            (safe_limit, "#59a14f", "Safe"),
            (warning_limit, "#f28e2b", "Warning"),
            (danger_limit, "#e15759", "Danger"),
        ]:
            frequency_fig.add_vline(
                x=threshold,
                line_dash="dash",
                line_color=color,
                annotation_text=f"{label}: {threshold}",
                annotation_position="top",
            )
        frequency_fig.update_layout(
            height=360,
            template="plotly_white",
            showlegend=False,
            bargap=0.12,
        )
        st.plotly_chart(frequency_fig, width="stretch")

    with col2:
        risk_fig = px.bar(
            risk_counts,
            x="risk_level",
            y="observations",
            text="observations",
            color="risk_level",
            category_orders={"risk_level": risk_order},
            color_discrete_map={
                "No people": "#9e9e9e",
                "Low": "#59a14f",
                "Moderate": "#f28e2b",
                "High": "#e15759",
            },
            labels={"risk_level": "Risk level", "observations": "Observations"},
            title="🚦 Risk-Level Frequency",
        )
        risk_fig.update_layout(
            height=360,
            template="plotly_white",
            showlegend=False,
        )
        st.plotly_chart(risk_fig, width="stretch")

    timeline_fig = go.Figure()
    timeline_fig.add_trace(
        go.Scatter(
            x=chart_df["timestamp"],
            y=chart_df["people_count"],
            mode="lines+markers",
            name="Detected crowd",
            line=dict(color="#4c78a8", width=3),
            hovertemplate="%{x|%d %b %H:%M}<br>%{y} people<extra></extra>",
        )
    )
    for threshold, color, label in [
        (safe_limit, "#59a14f", "Safe limit"),
        (warning_limit, "#f28e2b", "Warning limit"),
        (danger_limit, "#e15759", "Danger limit"),
    ]:
        timeline_fig.add_hline(
            y=threshold,
            line_dash="dash",
            line_color=color,
            annotation_text=f"{label}: {threshold}",
            annotation_position="top left",
        )
    timeline_fig.update_layout(
        title="⏱ Crowd Count Over Observation Time",
        xaxis_title="Observation time",
        yaxis_title="People detected",
        template="plotly_white",
        height=400,
        legend=dict(orientation="h", y=-0.2),
    )
    st.plotly_chart(timeline_fig, width="stretch")

def show_live_detection_charts(
    event_name, count, timestamp, safe_limit, warning_limit, danger_limit
):
    """Display charts immediately after an image is analyzed."""
    st.markdown("### 📊 Live Crowd Analysis")
    st.caption(
        "These charts update automatically whenever a new image is analyzed. "
        "Save the record to include it in event history and reports."
    )

    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        level_names = ["Safe", "Warning", "Danger"]
        level_values = [safe_limit, warning_limit, danger_limit]
        level_colors = ["#59a14f", "#f28e2b", "#e15759"]
        threshold_fig = go.Figure(
            go.Bar(
                x=level_names,
                y=level_values,
                marker_color=level_colors,
                text=level_values,
                textposition="auto",
                hovertemplate="%{x} threshold: %{y} people<extra></extra>",
            )
        )
        threshold_fig.add_hline(
            y=count,
            line_color="#4c78a8",
            line_width=4,
            annotation_text=f"Current: {count}",
            annotation_position="top left",
        )
        threshold_fig.update_layout(
            title="Current Crowd vs Safety Thresholds",
            xaxis_title="Safety zone",
            yaxis_title="People",
            template="plotly_white",
            height=350,
            showlegend=False,
        )
        st.plotly_chart(threshold_fig, width="stretch")

    with chart_col2:
        risk_labels = ["Current crowd"]
        risk_fig = go.Figure(
            go.Bar(
                x=risk_labels,
                y=[count],
                marker_color="#e15759" if count > danger_limit else (
                    "#f28e2b" if count > safe_limit else "#59a14f"
                ),
                text=[f"{count} people"],
                textposition="auto",
                hovertemplate="%{y} people detected<extra></extra>",
            )
        )
        for threshold, color, label in [
            (safe_limit, "#59a14f", "Safe"),
            (warning_limit, "#f28e2b", "Warning"),
            (danger_limit, "#e15759", "Danger"),
        ]:
            risk_fig.add_hline(
                y=threshold,
                line_dash="dash",
                line_color=color,
                annotation_text=f"{label}: {threshold}",
                annotation_position="top left",
            )
        risk_fig.update_layout(
            title=f"Crowd Density at {timestamp}",
            xaxis_title="Latest observation",
            yaxis_title="People detected",
            template="plotly_white",
            height=350,
            showlegend=False,
        )
        st.plotly_chart(risk_fig, width="stretch")

    event_records = get_event_data(event_name)
    if event_records:
        history_df = pd.DataFrame(event_records)
        history_df["timestamp"] = pd.to_datetime(history_df["timestamp"])
        history_df = pd.concat(
            [
                history_df[["timestamp", "people_count"]],
                pd.DataFrame(
                    [{"timestamp": pd.to_datetime(timestamp), "people_count": count}]
                ),
            ],
            ignore_index=True,
        ).sort_values("timestamp")
        history_fig = px.line(
            history_df,
            x="timestamp",
            y="people_count",
            markers=True,
            title=f"{event_name} Crowd Trend",
            labels={"timestamp": "Time", "people_count": "People detected"},
        )
        history_fig.update_layout(template="plotly_white", height=360)
        for threshold, color, label in [
            (safe_limit, "#59a14f", "Safe"),
            (warning_limit, "#f28e2b", "Warning"),
            (danger_limit, "#e15759", "Danger"),
        ]:
            history_fig.add_hline(
                y=threshold,
                line_dash="dash",
                line_color=color,
                annotation_text=f"{label}: {threshold}",
            )
        st.plotly_chart(history_fig, width="stretch")

def image_as_data_uri(image_path):
    """Return a local image as an embeddable data URI for downloaded reports."""
    if not image_path or not os.path.exists(image_path):
        return None
    extension = os.path.splitext(image_path)[1].lower()
    mime_type = "image/png" if extension == ".png" else "image/jpeg"
    with open(image_path, "rb") as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode("ascii")
    return f"data:{mime_type};base64,{encoded_image}"

def build_event_report(
    event_name,
    event_data,
    df,
    safe_limit,
    warning_limit,
    danger_limit,
    forecast_display=None,
):
    """Build a self-contained HTML report with charts, forecast, and photos."""
    report_df = df.copy()
    report_df["risk_level"] = report_df["people_count"].apply(
        lambda value: classify_crowd(
            value, safe_limit, warning_limit, danger_limit
        )[0]
    )
    risk_order = ["No people", "Low", "Moderate", "High"]
    risk_counts = (
        report_df["risk_level"]
        .value_counts()
        .reindex(risk_order, fill_value=0)
        .reset_index()
    )
    risk_counts.columns = ["risk_level", "observations"]

    frequency_fig = px.histogram(
        report_df,
        x="people_count",
        nbins=max(5, min(15, report_df["people_count"].nunique())),
        text_auto=True,
        color_discrete_sequence=["#4c78a8"],
        labels={"people_count": "People detected", "count": "Observations"},
        title="Frequency of Detected Crowd Sizes",
    )
    frequency_fig.update_layout(template="plotly_white", height=380)

    risk_fig = px.bar(
        risk_counts,
        x="risk_level",
        y="observations",
        text="observations",
        color="risk_level",
        category_orders={"risk_level": risk_order},
        color_discrete_map={
            "No people": "#9e9e9e",
            "Low": "#59a14f",
            "Moderate": "#f28e2b",
            "High": "#e15759",
        },
        title="Risk-Level Frequency",
    )
    risk_fig.update_layout(template="plotly_white", height=380)

    timeline_fig = px.line(
        report_df,
        x="timestamp",
        y="people_count",
        markers=True,
        title="Crowd Count Over Time",
        labels={"timestamp": "Observation time", "people_count": "People detected"},
    )
    for threshold, color, label in [
        (safe_limit, "#59a14f", "Safe"),
        (warning_limit, "#f28e2b", "Warning"),
        (danger_limit, "#e15759", "Danger"),
    ]:
        timeline_fig.add_hline(
            y=threshold,
            line_dash="dash",
            line_color=color,
            annotation_text=f"{label}: {threshold}",
        )
    timeline_fig.update_layout(template="plotly_white", height=400)

    chart_html = "\n".join(
        [
            frequency_fig.to_html(full_html=False, include_plotlyjs=True),
            risk_fig.to_html(full_html=False, include_plotlyjs=False),
            timeline_fig.to_html(full_html=False, include_plotlyjs=False),
        ]
    )
    forecast_html = "<p>Forecast was not available. At least five observations are required.</p>"
    if forecast_display is not None and not forecast_display.empty:
        forecast_fig = px.line(
            forecast_display,
            x="ds",
            y=["yhat", "yhat_lower", "yhat_upper"],
            title="AI Crowd Forecast (Next 60 Minutes)",
            labels={"ds": "Time", "value": "People"},
        )
        forecast_fig.update_layout(template="plotly_white", height=420)
        forecast_html = forecast_fig.to_html(
            full_html=False, include_plotlyjs=False
        )

    photo_cards = []
    for record in event_data:
        image_uri = image_as_data_uri(record.get("image_path"))
        image_markup = (
            f'<img src="{image_uri}" alt="Crowd detection photo">'
            if image_uri
            else "<p>Photo unavailable</p>"
        )
        photo_cards.append(
            f"""
            <article class="photo-card">
              {image_markup}
              <p><b>{html.escape(str(record["timestamp"]))}</b> —
              {record["people_count"]} people</p>
            </article>
            """
        )

    records_html = report_df[
        ["timestamp", "people_count", "risk_level"]
    ].to_html(index=False, border=0, classes="records")
    safe_event_name = html.escape(str(event_name))
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Crowd Safety Report - {safe_event_name}</title>
  <style>
    body {{ font-family: Arial, sans-serif; color: #1f2937; margin: 32px; }}
    h1, h2 {{ color: #17365d; }}
    .summary {{ display: flex; gap: 12px; flex-wrap: wrap; }}
    .metric {{ background: #eef4fb; padding: 14px 20px; border-radius: 8px; }}
    .records {{ border-collapse: collapse; width: 100%; margin: 16px 0; }}
    .records th, .records td {{ border: 1px solid #d1d5db; padding: 8px; text-align: left; }}
    .records th {{ background: #eef4fb; }}
    .photos {{ display: flex; flex-wrap: wrap; gap: 16px; }}
    .photo-card {{ width: 300px; border: 1px solid #d1d5db; padding: 10px; border-radius: 8px; }}
    .photo-card img {{ max-width: 100%; height: auto; }}
  </style>
</head>
<body>
  <h1>Smart Crowd Detection &amp; Risk Report</h1>
  <p><b>Event:</b> {safe_event_name}<br>
     <b>Generated:</b> {generated_at}<br>
     <b>Thresholds:</b> Safe ≤ {safe_limit}, Warning ≤ {warning_limit},
     Danger &gt; {danger_limit}</p>
  <div class="summary">
    <div class="metric"><b>Observations</b><br>{len(report_df)}</div>
    <div class="metric"><b>Peak crowd</b><br>{int(report_df["people_count"].max())}</div>
    <div class="metric"><b>Average crowd</b><br>{report_df["people_count"].mean():.1f}</div>
    <div class="metric"><b>High-risk observations</b><br>
      {int((report_df["risk_level"] == "High").sum())}</div>
  </div>
  <h2>Charts and Diagrams</h2>
  {chart_html}
  <h2>AI Forecast</h2>
  {forecast_html}
  <h2>Density Records</h2>
  {records_html}
  <h2>Detection Photos</h2>
  <div class="photos">{"".join(photo_cards)}</div>
</body>
</html>"""

# ===================== EMERGENCY ALERT SIMULATION =====================
def trigger_emergency_alert(event_name, count, timestamp):
    """Display emergency alert popup and simulate notifications."""
    
    # Create alert container with styling
    alert_container = st.container()
    with alert_container:
        st.error("🚨 EMERGENCY ALERT: HIGH CROWD DENSITY DETECTED!")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"Event: {event_name}")
            st.markdown(f"People Count: {count}")
            st.markdown(f"Time: {timestamp}")
        with col2:
            st.markdown(f"Status: ⚠ CRITICAL")
            st.markdown(f"Action: Notifying Authorities")
        
        # Simulated notification messages
        if enable_notifications:
            st.markdown("---")
            st.subheader("📱 Simulated Notifications Sent:")
            
            notifications = [
                {
                    "type": "SMS",
                    "recipient": "Event Security Team",
                    "message": f"⚠ HIGH ALERT: Crowd density of {count} people detected at {event_name}. Immediate action required. Time: {timestamp}"
                },
                {
                    "type": "Email",
                    "recipient": "security@eventmanagement.com",
                    "message": f"High crowd density alert triggered at {event_name}. Current count: {count} people. Please dispatch additional security personnel."
                },
                {
                    "type": "SMS",
                    "recipient": "Local Police Department",
                    "message": f"Crowd control assistance requested at {event_name}. Density: {count} people. Location monitoring active."
                },
                {
                    "type": "Push Notification",
                    "recipient": "Event Management App",
                    "message": f"🚨 High crowd density at {event_name}. Crowd control measures activated."
                }
            ]
            
            for notif in notifications:
                with st.expander(f"✉ {notif['type']} to {notif['recipient']}", expanded=True):
                    st.code(notif['message'], language=None)
            
            # Save alert to history
            save_alert(event_name, count, timestamp, "High", notifications)
            
            st.success("✅ All notifications sent successfully!")

# ===================== INTERACTIVE MAP SIMULATION =====================
def show_location_map(event_data=None):
    """Display interactive hotspot map showing high-density locations."""
    
    st.subheader("🗺 Event Location Hotspot Map")
    st.markdown("Simulated map showing crowd density hotspots across event locations")
    
    # Create simulated location data
    if event_data:
        # Use actual event data
        locations = []
        for event in event_data:
            # Simulate coordinates (in real scenario, these would come from GPS/venue data)
            base_lat, base_lon = 12.9716, 77.5946  # Bengaluru coordinates
            locations.append({
                "event": event["event_name"],
                "count": event["people_count"],
                "lat": base_lat + np.random.uniform(-0.1, 0.1),
                "lon": base_lon + np.random.uniform(-0.1, 0.1),
                "timestamp": event["timestamp"]
            })
    else:
        # Generate sample hotspot data
        locations = [
            {"event": "Main Stage", "count": 45, "lat": 12.9716, "lon": 77.5946},
            {"event": "Food Court", "count": 28, "lat": 12.9750, "lon": 77.5980},
            {"event": "Entry Gate A", "count": 18, "lat": 12.9690, "lon": 77.5920},
            {"event": "Parking Area", "count": 12, "lat": 12.9680, "lon": 77.5900},
            {"event": "Exit Gate B", "count": 35, "lat": 12.9740, "lon": 77.6000},
        ]
    
    df_map = pd.DataFrame(locations)
    
    # Determine color based on crowd level
    def get_color(count):
        if count <= 10:
            return "green"
        elif count <= 15:
            return "orange"
        else:
            return "red"
    
    df_map['color'] = df_map['count'].apply(get_color)
    df_map['size'] = df_map['count'] * 2  # Size proportional to crowd
    
    # Create interactive map
    fig = px.scatter_map(
        df_map,
        lat="lat",
        lon="lon",
        hover_name="event",
        hover_data={"count": True, "lat": False, "lon": False, "color": False, "size": False},
        color="color",
        size="size",
        color_discrete_map={"green": "#00CC00", "orange": "#FFA500", "red": "#FF0000"},
        zoom=12,
        height=500
    )
    
    fig.update_layout(
        mapbox_style="open-street-map",
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        showlegend=False
    )
    
    st.plotly_chart(fig, width="stretch")
    
    # Legend
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("🟢 Low Density (≤10 people)")
    with col2:
        st.markdown("🟡 Moderate Density (11-15 people)")
    with col3:
        st.markdown("🔴 High Density (16+ people)")
    
    # Hotspot summary
    if not df_map.empty:
        st.markdown("---")
        st.subheader("📊 Hotspot Summary")
        high_risk_locations = df_map[df_map['color'] == 'red']
        if not high_risk_locations.empty:
            st.warning(f"⚠ {len(high_risk_locations)} high-risk location(s) detected!")
            for idx, row in high_risk_locations.iterrows():
                st.markdown(f"- {row['event']}: {row['count']} people")
        else:
            st.success("✅ No high-risk locations at this time.")

# ===================== MODE 1: CAPTURE & ANALYZE =====================
if mode == "📸 Capture & Analyze New Image":
    st.header("📸 Upload or Capture Image")
    
    # Event name input
    event_name = st.text_input("🎪 Enter Event Name:", placeholder="e.g., Concert 2025, Festival, Sports Match")
    
    source_option = st.radio("Select input method:", ["Upload from device", "Use camera"])
    
    if source_option == "Upload from device":
        uploaded_file = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            image = Image.open(uploaded_file).convert("RGB")
        else:
            image = None
    else:
        captured_image = st.camera_input("Take a picture")
        if captured_image:
            image = Image.open(captured_image).convert("RGB")
        else:
            image = None
    
    # ===================== MAIN LOGIC =====================
    if image and event_name:
        st.subheader("🔍 Detection Results")
        count, annotated_img = detect_people(image)
        risk_level, icon, message = classify_crowd(
            count, safety_threshold, warning_threshold, danger_threshold
        )
        
        # Get current timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.session_state.latest_analysis = {
            "event_name": event_name,
            "count": count,
            "risk_level": risk_level,
            "timestamp": timestamp,
        }
        
        st.image(annotated_img, caption=f"Detected {count} people", use_container_width=True)
        st.markdown(f"### {icon} Crowd Level: {risk_level}")
        st.info(message)
        st.markdown(f"📅 Time:** {timestamp}")
        show_live_detection_charts(
            event_name,
            count,
            timestamp,
            safety_threshold,
            warning_threshold,
            danger_threshold,
        )
        
        # Trigger emergency alert for high crowd
        if count >= danger_threshold and enable_alerts:
            st.markdown("---")
            trigger_emergency_alert(event_name, count, timestamp)
        
        # Save button
        if st.button("💾 Save This Record", type="primary"):
            # Save image
            img_filename = f"{event_name.replace(' ', '')}{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            img_path = os.path.join(IMAGES_DIR, img_filename)
            cv2.imwrite(img_path, cv2.cvtColor(annotated_img, cv2.COLOR_RGB2BGR))
            
            # Save event data
            save_event(event_name, count, timestamp, img_path)
            st.success(f"✅ Record saved successfully for event: {event_name}")
        
        # Suggestions
        st.markdown("---")
        st.markdown("#### 🧭 Safety Suggestions")
        if risk_level == "High":
            st.warning("""
            - Avoid entering the area if possible
            - Move calmly and avoid pushing
            - Follow emergency exit signs
            - Inform event organizers or security
            - Wait for crowd to disperse before entering
            """)
        elif risk_level == "Moderate":
            st.info("""
            - Keep safe distance from others
            - Stay near exits
            - Stay alert and avoid panic
            - Monitor crowd movement
            """)
        elif risk_level == "Low":
            st.success("""
            - Situation is safe ✅
            - Continue monitoring if the crowd grows
            - Stay aware of your surroundings
            """)
    elif image and not event_name:
        st.warning("⚠ Please enter an event name to continue.")
    else:
        st.info("Enter event name and upload/capture an image to begin detection.")

# ===================== MODE 2: SEARCH EVENT HISTORY =====================
elif mode == "🔍 Search Event History":
    st.header("🔍 Search Event History")
    
    # Get all unique event names
    all_events = load_events()
    event_names = sorted(list(set([e["event_name"] for e in all_events])))
    
    if not event_names:
        st.info("No events recorded yet. Capture some images first!")
    else:
        search_event = st.selectbox("Select an event to view:", [""] + event_names)
        
        if search_event:
            event_data = get_event_data(search_event)
            
            if event_data:
                st.subheader(f"📊 Analysis for: {search_event}")
                st.markdown(f"Total Records: {len(event_data)}")
                
                # Create dataframe for graph
                df = pd.DataFrame(event_data)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df = df.sort_values('timestamp')
                df['time_only'] = df['timestamp'].dt.strftime('%I:%M %p')

                show_analysis_diagram()
                show_event_analytics(
                    df,
                    safety_threshold,
                    warning_threshold,
                    danger_threshold,
                )
                
                # ===================== AI CROWD FORECASTING & PREDICTIVE RISK MODULE =====================
                st.subheader("🤖 AI Crowd Forecast (Next 60 Minutes)")
                forecast_display = None
                if len(df) >= 5:  # Prophet needs a few data points
                    try:
                        from prophet import Prophet
                    except Exception:
                        st.warning("Prophet is not installed. Run pip install prophet in your environment to enable AI forecasting.")
                        Prophet = None

                    if Prophet is not None:
                        # Prepare data for Prophet
                        df_prophet = df[['timestamp', 'people_count']].rename(columns={'timestamp': 'ds', 'people_count': 'y'})
                        df_prophet['ds'] = pd.to_datetime(df_prophet['ds'])

                        # Fit model
                        model_prophet = Prophet(interval_width=0.9, daily_seasonality=True)
                        model_prophet.fit(df_prophet)

                        # Predict next 60 minutes (per-minute freq)
                        future = model_prophet.make_future_dataframe(periods=60, freq='min')
                        forecast = model_prophet.predict(future)

                        # Prepare display
                        forecast_display = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]
                        latest_time = df_prophet['ds'].max()

                        # Predicted crowd in 20 minutes
                        future_20min = latest_time + pd.Timedelta(minutes=20)
                        # find nearest predicted row
                        pred_rows = forecast_display.loc[forecast_display['ds'] >= future_20min]
                        if not pred_rows.empty:
                            pred_20min = pred_rows['yhat'].iloc[0]
                        else:
                            pred_20min = forecast_display['yhat'].iloc[-1]

                        # Use the app's crowd_threshold (sidebar) as risk threshold
                        ai_threshold = crowd_threshold
                        current_count = int(df['people_count'].iloc[-1])
                        predicted_crowd_count = int(round(pred_20min))

                        forecast_col1, forecast_col2, forecast_col3 = st.columns(3)
                        with forecast_col1:
                            st.metric("Current crowd", current_count)
                        with forecast_col2:
                            st.metric("Predicted in 20 min", int(round(pred_20min)))
                        with forecast_col3:
                            forecast_peak = int(round(forecast_display["yhat"].max()))
                            st.metric("Forecast peak", forecast_peak)

                        # ---------------------
                        # 🧩 Step 2 — AUTO ALERT SYSTEM (evaluated after prediction)
                        # ---------------------
                        event_location = "Main Venue"  # change if you have location per-event

                        # Auto-trigger emergency when threshold exceeded
                        if enable_alerts and (current_count > danger_threshold or predicted_crowd_count > danger_threshold):
                            st.error("🚨 Critical crowd level detected! Activating automatic SOS system...")

                            # Send EMAIL to Police (POLICE_EMAIL env expected)
                            send_email(
                                to_email=os.getenv("POLICE_EMAIL", ALERT_RECIPIENT),
                                subject="🚨 SOS: Overcrowding Alert",
                                body=f"""
                                Immediate attention required!

                                Event: {search_event}
                                Current Count: {current_count}
                                Predicted (20 min): {predicted_crowd_count}
                                Location: {event_location}
                                """
                            )

                            # Send Telegram alerts
                            send_telegram_alert("🚨 SOS Alert! Overcrowding detected. Please guide people to exits immediately.")
                            send_telegram_alert("🚨 AI Alert: Crowd density critical! Evacuation protocol activated.")

                            # Optional — play emergency voice
                            try:
                                sos_message = "Attention! Overcrowding detected. Please move calmly towards the nearest exit. Follow security instructions."
                                tts = gTTS(sos_message)
                                sos_audio = io.BytesIO()
                                tts.write_to_fp(sos_audio)
                                sos_audio.seek(0)
                                st.audio(sos_audio, format='audio/mp3', autoplay=True)
                            except Exception as _e:
                                st.warning("Voice alert could not be played (gTTS/IO issue).")

                            # Also call your trigger_sos helper (shows map / extra steps)
                            try:
                                trigger_sos(
                                    event_name=search_event,
                                    event_location=event_location,
                                    current_count=current_count,
                                    predicted_crowd_count=predicted_crowd_count,
                                    danger_threshold=danger_threshold
                                )
                            except Exception:
                                pass

                        elif current_count > warning_threshold:
                            st.warning("⚠ High crowd density detected — monitoring closely.")
                            # Optional lightweight notification
                            send_telegram_alert("⚠ Warning: High crowd detected, please monitor the area.")

                        # AI RISK PREDICTION LOGIC
                        if pred_20min > ai_threshold:
                            st.markdown("""
                            <div style="background-color:#FFCCCC; padding:12px; border-radius:8px; text-align:center;">
                            ⚠ <b>AI Early Warning:</b> Based on current trend, a <b>high crowd risk</b> is likely in the next 20 minutes!
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Add SOS trigger here (kept for backward compatibility)
                            trigger_sos(
                                event_name=search_event,
                                event_location="Main Venue",  # You can make this dynamic
                                current_count=int(df['people_count'].iloc[-1]),
                                predicted_crowd_count=int(pred_20min),
                                danger_threshold=ai_threshold
                            )
                        else:
                            st.success(f"✅ Crowd level stable. Predicted crowd in 20 min: {int(pred_20min)} people")

                        # Visualization
                        fig_ai = go.Figure()
                        fig_ai.add_trace(go.Scatter(
                            x=df_prophet['ds'],
                            y=df_prophet['y'],
                            mode='lines+markers',
                            name='Actual Crowd',
                            line=dict(color='blue')
                        ))
                        fig_ai.add_trace(go.Scatter(
                            x=forecast_display['ds'],
                            y=forecast_display['yhat'],
                            mode='lines',
                            name='Predicted Trend',
                            line=dict(color='orange', dash='dash')
                        ))
                        fig_ai.add_trace(go.Scatter(
                            x=forecast_display['ds'],
                            y=forecast_display['yhat_upper'],
                            mode='lines',
                            name='Upper Bound',
                            line=dict(color='lightcoral', dash='dot'),
                            opacity=0.3
                        ))
                        fig_ai.add_trace(go.Scatter(
                            x=forecast_display['ds'],
                            y=forecast_display['yhat_lower'],
                            mode='lines',
                            name='Lower Bound',
                            line=dict(color='lightgreen', dash='dot'),
                            opacity=0.3
                        ))
                        fig_ai.update_layout(
                            title="🧠 AI Crowd Density Forecast (Next 60 Minutes)",
                            xaxis_title="Time",
                            yaxis_title="People Count",
                            template="plotly_white",
                            legend=dict(orientation="h", y=-0.2),
                            height=420
                        )
                        for threshold, color, label in [
                            (safety_threshold, "#59a14f", "Safe"),
                            (warning_threshold, "#f28e2b", "Warning"),
                            (danger_threshold, "#e15759", "Danger"),
                        ]:
                            fig_ai.add_hline(
                                y=threshold,
                                line_dash="dash",
                                line_color=color,
                                annotation_text=f"{label}: {threshold}",
                                annotation_position="top left",
                            )
                        st.plotly_chart(fig_ai, width="stretch")
                        st.caption(
                            "The shaded forecast range shows model uncertainty. "
                            "Crossing the danger line means security should prepare an evacuation response."
                        )

                        # ===================== 🌡 HEAT MAP WITH LIVE CROWD MOVEMENT =====================
                        st.markdown("### 🌡 Live Heat Map – Crowd Flow & Density")

                        st.markdown("""
                        > "The system uses a live heat map to visualize crowd movement — red zones indicate dense or slow-moving crowds, helping security teams to respond faster."
                        """)

                        # Simulated crowd movement data (you can replace this with real coordinates later)
                        heatmap_data = pd.DataFrame({
                            'x': np.random.uniform(0, 10, 100),
                            'y': np.random.uniform(0, 10, 100),
                            'intensity': np.random.randint(1, 100, 100)
                        })

                        # Create heatmap using Plotly
                        fig_heat = go.Figure(
                            data=go.Densitymapbox(
                                lat=12.9716 + (heatmap_data['x'] - 5) / 100,  # simulated lat movement
                                lon=77.5946 + (heatmap_data['y'] - 5) / 100,  # simulated lon movement
                                z=heatmap_data['intensity'],
                                radius=20,
                                colorscale="YlOrRd",
                                showscale=True,
                            )
                        )

                        fig_heat.update_layout(
                            mapbox_style="open-street-map",
                            mapbox_center={"lat": 12.9716, "lon": 77.5946},
                            mapbox_zoom=13,
                            height=500,
                            margin={"r": 0, "t": 0, "l": 0, "b": 0}
                        )

                        st.plotly_chart(fig_heat, width="stretch")

                        # Add simple flow arrows (simulated direction)
                        st.markdown("""
                        <style>
                        .flow-arrow {
                            text-align: center;
                            font-size: 20px;
                            animation: moveArrow 2s infinite alternate;
                        }
                        @keyframes moveArrow {
                            0% { transform: translateX(0px); }
                            100% { transform: translateX(20px); }
                        }
                        </style>

                        <div class='flow-arrow'>➡ ➡ ➡ Crowd Moving Toward Main Stage ➡ ➡ ➡</div>
                        """, unsafe_allow_html=True)

                        st.info("🧭 Live Heat Map Active: Red zones show slow-moving, dense areas. Use this to direct security and crowd flow.")

                        # Continue with existing code...
                else:
                    st.warning("📊 Need at least 5 data points to perform AI forecasting. Please collect more event data.")
                # ===================== end AI module =====================

                report_html = build_event_report(
                    search_event,
                    event_data,
                    df,
                    safety_threshold,
                    warning_threshold,
                    danger_threshold,
                    forecast_display,
                )
                report_filename = (
                    f"{search_event.strip().replace(' ', '_')}_crowd_report.html"
                )
                st.download_button(
                    "📥 Download Complete Crowd Report",
                    data=report_html,
                    file_name=report_filename,
                    mime="text/html",
                    type="primary",
                    help=(
                        "Downloads charts, density records, forecast, thresholds, "
                        "risk summary, and all saved detection photos."
                    ),
                )
                st.caption(
                    "The report updates automatically from the currently selected event "
                    "and the latest sidebar thresholds."
                )
                
                # Crowd statistics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Peak Crowd", df['people_count'].max())
                with col2:
                    st.metric("Average Crowd", f"{df['people_count'].mean():.1f}")
                with col3:
                    st.metric("Lowest Crowd", df['people_count'].min())
                
                # Display the most recent image
                latest_record = df.iloc[-1]
                if os.path.exists(latest_record['image_path']):
                    st.markdown("### 📸 Most Recent Crowd Image")
                    st.image(latest_record['image_path'], width="stretch")
                else:
                    st.warning("Latest image not found")
                
                # Risk assessment based on latest crowd
                risk_level, icon, suggestion = classify_crowd(
                    latest_record['people_count'], safety_threshold, warning_threshold, danger_threshold
                )
                st.markdown(f"### Risk Level: {icon} {risk_level}")
                if risk_level == "High":
                    st.warning("⚠ HIGH RISK! Do NOT go to this event.")
                else:
                    st.info(f"💡 Suggestion: {suggestion}")
                
                # Simple 1-hour ahead crowd prediction (linear regression)
                if len(df) >= 2:
                    # Fit linear trend
                    df['timestamp_num'] = df['timestamp'].astype(int) / 10**9  # convert to seconds
                    coef = np.polyfit(df['timestamp_num'], df['people_count'], 1)
                    slope, intercept = coef
                    next_hour_ts = (df['timestamp'].iloc[-1] + pd.Timedelta(hours=1)).timestamp()
                    predicted_count = slope * next_hour_ts + intercept
                    predicted_count = max(0, int(predicted_count))
                    st.markdown(f"### ⏳ Predicted Crowd 1 Hour Later: {predicted_count} people")
                    
                    pred_risk, pred_icon, _ = classify_crowd(
                        predicted_count, safety_threshold, warning_threshold, danger_threshold
                    )
                    st.markdown(f"Predicted Risk: {pred_icon} {pred_risk}")
                
                # Show individual historical records
                st.markdown("### 📋 Historical Records")
                for idx, record in enumerate(event_data, 1):
                    with st.expander(f"Record {idx} - {record['timestamp']} ({record['people_count']} people)"):
                        col1, col2 = st.columns([2, 1])
                        with col1:
                            if os.path.exists(record['image_path']):
                                st.image(record['image_path'], width="stretch")
                            else:
                                st.warning("Image not found")
                        with col2:
                            st.markdown(f"Event: {record['event_name']}")
                            st.markdown(f"Time: {record['timestamp']}")
                            st.markdown(f"People Count: {record['people_count']}")
                            risk_level, icon, _ = classify_crowd(
                                record['people_count'], safety_threshold, warning_threshold, danger_threshold
                            )
                            st.markdown(f"Risk Level: {icon} {risk_level}")

# ===================== MODE 3: ALERT HISTORY =====================
elif mode == "🚨 View Alert History":
    st.header("🚨 Emergency Alert History")
    
    alerts = load_alerts()
    
    if not alerts:
        st.info("No emergency alerts have been triggered yet.")
    else:
        st.markdown(f"Total Alerts: {len(alerts)}")
        
        # Create dataframe
        df_alerts = pd.DataFrame(alerts)
        df_alerts['timestamp'] = pd.to_datetime(df_alerts['timestamp'])
        df_alerts = df_alerts.sort_values('timestamp', ascending=False)
        
        # Summary metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Alerts", len(alerts))
        with col2:
            unique_events = df_alerts['event_name'].nunique()
            st.metric("Events with Alerts", unique_events)
        with col3:
            max_crowd = df_alerts['people_count'].max()
            st.metric("Highest Crowd", max_crowd)
        
        st.markdown("---")
        
        # Display alerts table
        st.subheader("📋 Alert Records")
        display_df = df_alerts[['timestamp', 'event_name', 'people_count', 'risk_level']].copy()
        display_df['timestamp'] = display_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
        st.dataframe(display_df, width="stretch")
        
        # Detailed view
        st.markdown("---")
        st.subheader("🔍 Detailed Alert View")
        for idx, alert in df_alerts.iterrows():
            with st.expander(f"⚠ {alert['event_name']} - {alert['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"Event: {alert['event_name']}")
                    st.markdown(f"Time: {alert['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
                    st.markdown(f"People Count: {alert['people_count']}")
                    st.markdown(f"Risk Level: 🔴 {alert['risk_level']}")
                
                with col2:
                    st.markdown("Notifications Sent:")
                    for notif in alert['notifications_sent']:
                        st.markdown(f"- {notif['type']} → {notif['recipient']}")

# ===================== MODE 4: LOCATION HOTSPOT MAP =====================
elif mode == "🗺 Location Hotspot Map":
    st.header("🗺 Event Location Hotspot Map")
    
    all_events = load_events()
    
    if not all_events:
        st.info("No event data available yet. Using sample hotspot data for demonstration.")
        show_location_map()
    else:
        # Option to view specific event or all events
        event_names = ["All Events"] + sorted(list(set([e["event_name"] for e in all_events])))
        selected_event = st.selectbox("Select event to view on map:", event_names)
        
        if selected_event == "All Events":
            show_location_map(all_events)
        else:
            event_specific_data = get_event_data(selected_event)
            show_location_map(event_specific_data)

# ===================== FOOTER =====================
st.markdown("---")
st.caption("Developed with ❤ using Streamlit & YOLOv8 — Crowd Safety Awareness Project")
