# Real-Time Vision-Based Crowd Risk Prediction and Smart Evacuation System

An AI-powered Streamlit application that detects people in crowd images,
classifies crowd risk, forecasts crowd growth, displays understandable charts,
and supports emergency communication and evacuation guidance.

**Administrator:** Mohamed Dadapeer

## Contents

- [Project overview](#project-overview)
- [Features](#features)
- [System architecture](#system-architecture)
- [Project structure](#project-structure)
- [Requirements](#requirements)
- [Installation and setup](#installation-and-setup)
- [Configuration](#configuration)
- [Using the dashboard](#using-the-dashboard)
- [Risk and prediction logic](#risk-and-prediction-logic)
- [Notifications](#notifications)
- [Reports and stored data](#reports-and-stored-data)
- [Training workflow](#training-workflow)
- [Troubleshooting](#troubleshooting)
- [Privacy and safety](#privacy-and-safety)
- [Limitations and future work](#limitations-and-future-work)

## Project overview

The system helps event operators understand crowd conditions from images or
camera captures. It uses YOLOv8 to detect people, converts the detection count
into a configurable risk level, and stores event observations for trend
analysis. When enough observations exist, Prophet forecasts the next 60 minutes
of crowd levels.

The dashboard is designed for demonstrations and local event monitoring. It
does not replace trained security personnel, emergency services, or a certified
life-safety system.

## Features

### Detection and risk analysis

- Upload a JPG, JPEG, or PNG image.
- Capture an image with a camera-enabled browser.
- Detect people with Ultralytics YOLOv8.
- Display bounding boxes and the detected people count.
- Classify observations as **No people**, **Low**, **Moderate**, or **High**.
- Configure safe, warning, and danger thresholds from the sidebar.

### Charts and diagrams

- Live chart showing the current count against safety thresholds.
- Crowd-density trend for the selected event.
- Crowd-size frequency histogram.
- Risk-level frequency chart.
- Crowd timeline with safe, warning, and danger lines.
- Forecast trend with uncertainty range and threshold lines.
- Visual workflow diagram explaining image-to-alert processing.

### Forecasting

- Uses Prophet when an event contains at least five observations.
- Forecasts one minute at a time for the next 60 minutes.
- Shows the estimated crowd in 20 minutes.
- Shows the forecast peak and prediction uncertainty.
- Displays an early warning when the predicted crowd crosses the configured
  prediction threshold.

### Emergency response

- Manual emergency button in the sidebar.
- Emergency banner, voice message, siren, and evacuation instructions.
- Safe-route demonstration map.
- Optional email and Telegram notifications.
- Telegram incident summary containing event, count, risk, time, thresholds,
  forecast information, and required action.

### History, maps, and reports

- Save annotated detection images and event observations.
- Search event history by event name.
- View alert history and notification records.
- Display event locations and hotspot summaries.
- Download a self-contained HTML report with charts, density records,
  forecast data, thresholds, summary metrics, and saved photos.

## System architecture

```text
Image upload / camera capture
            |
            v
      YOLOv8 inference
            |
            v
   Person count + annotated image
            |
            v
 Configurable risk classification
            |
       +----+----+
       |         |
       v         v
 JSON event   Dashboard charts
 history      and visual analysis
       |
       v
 Prophet forecast (5+ observations)
       |
       v
 Early warning / emergency response
       |
 +-----+-----------+-------------+
 |                 |             |
 v                 v             v
Email          Telegram       Voice/map
alerts         alerts         evacuation UI
```

### Main runtime components

| Component | Responsibility |
| --- | --- |
| Streamlit | User interface and session state |
| Ultralytics YOLOv8 | Person detection and annotation |
| OpenCV and Pillow | Image conversion and saving |
| Pandas and NumPy | Event data preparation and statistics |
| Plotly | Interactive charts and maps |
| Prophet | Crowd time-series forecasting |
| JSON files | Local event and alert persistence |
| SMTP | Optional email delivery |
| Telegram Bot API | Optional Telegram delivery |
| gTTS | Optional voice announcement generation |

## Project structure

```text
.
├── app.py                 # Main Streamlit dashboard
├── train_model.py         # Separate TensorFlow training/experimentation script
├── new.py                 # Small datetime test script
├── requirements.txt       # Runtime Python dependencies
├── yolov8n.pt             # Default local YOLOv8 weights
├── labels.csv             # Training metadata
├── labels.npy             # Numpy training data
├── crowd_data/
│   ├── events.json        # Saved event observations
│   ├── alerts.json        # Saved emergency alert records
│   └── images/            # Annotated detection images
└── .env                   # Local secrets; do not commit
```

## Requirements

- Windows, macOS, or Linux
- Python 3.9 or newer recommended
- A browser for Streamlit
- Camera permission if using camera capture
- Internet access for optional Telegram, email, and gTTS features
- Sufficient memory for YOLOv8 and Prophet

The main application dependencies are listed in `requirements.txt`. The
training script has additional TensorFlow and TensorFlow Hub requirements and
is separate from the dashboard runtime.

## Installation and setup

Run these commands from the project directory.

### 1. Create a virtual environment

Windows PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

If PowerShell blocks activation:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

### 2. Install dependencies

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 3. Start the dashboard

```powershell
python -m streamlit run app.py
```

Open the local address shown by Streamlit, normally:

```text
http://localhost:8501
```

The included `yolov8n.pt` file allows the application to start immediately.
For custom weights, place `best.pt` in the project directory or set:

```powershell
$env:YOLO_MODEL_PATH="C:\path\to\best.pt"
python -m streamlit run app.py
```

## Configuration

Create a local `.env` file in the project directory. Never commit this file
or paste its contents into a public issue, screenshot, or chat.

```env
YOLO_MODEL_PATH=C:\path\to\best.pt

# Optional email alerts
EMAIL_USER=your_email@gmail.com
EMAIL_PASS=your_gmail_app_password
ALERT_EMAIL=security@example.com
POLICE_EMAIL=police@example.com

# Optional Telegram bot alerts
TELEGRAM_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Optional awareness images
AWARE_IMG_1=interface images\1.jpeg
AWARE_IMG_2=interface images\2.jpeg
AWARE_IMG_3=interface images\3.jpeg
```

### Telegram setup

1. Create a bot with `@BotFather` using `/newbot`.
2. Keep the token private.
3. Open the new bot and send `/start`.
4. Obtain the numeric chat ID for the conversation.
5. Set both `TELEGRAM_TOKEN` and `TELEGRAM_CHAT_ID`.
6. Restart Streamlit after changing `.env`.

A phone number cannot be used as a Telegram bot chat ID. If a token is exposed,
revoke it with `@BotFather` and create a replacement immediately.

### Sidebar controls

- **Crowd threshold:** prediction warning threshold used by the dashboard.
- **Safe threshold:** maximum count considered Low.
- **Warning threshold:** maximum count considered Moderate.
- **Danger threshold:** counts above this value are High risk.
- **Enable Emergency Alerts:** enables automatic emergency behavior.
- **Enable Notification Simulation:** shows simulated notification records.

## Using the dashboard

### Analyze a new image

1. Select **Capture & Analyze New Image**.
2. Enter an event name.
3. Upload an image or use the camera.
4. Review the annotated image, count, risk, suggestions, and live charts.
5. Select **Save This Record** to add the observation to event history.

### Search event history

1. Select **Search Event History**.
2. Choose an event.
3. Review its metrics, charts, records, photos, and forecast.
4. Select **Download Complete Crowd Report** for a self-contained HTML report.

At least five observations are required for the Prophet forecast. Charts and
historical summaries still work with fewer observations.

### Emergency response

The sidebar emergency button toggles the emergency state. When activated, the
dashboard displays the emergency banner and attempts to send a Telegram report
if valid Telegram credentials are configured. The latest analyzed event is used
for the report.

## Risk and prediction logic

Risk classification uses the current detected count:

| Condition | Level | Meaning |
| --- | --- | --- |
| Count is zero | No people | No people detected |
| Count ≤ safe threshold | Low | Continue normal monitoring |
| Count ≤ warning threshold | Moderate | Keep exits clear and monitor |
| Count > warning threshold | High | Begin crowd-control response |

The thresholds are user-configurable. The application provides guidance only;
operators must validate conditions on site.

## Notifications

### Email

Email requires a Gmail App Password or a compatible SMTP account. Missing
credentials are reported in the application console and no email is sent.

### Telegram

Telegram uses the Bot API through `TELEGRAM_TOKEN` and `TELEGRAM_CHAT_ID`.
The application sends a readable incident summary rather than exposing secrets.
A Telegram bot cannot initiate a private conversation until the user has
opened the bot and sent a message such as `/start`.

### Voice and evacuation UI

The dashboard can generate a gTTS voice announcement, display evacuation
instructions, show a demonstration safe-route map, and display a siren element.
These are user-interface aids and must not be treated as a certified alarm
system.

## Reports and stored data

Event records are stored in `crowd_data/events.json`:

```json
{
  "event_name": "Example Event",
  "people_count": 12,
  "timestamp": "2026-11-05 15:00:00",
  "image_path": "crowd_data\\images\\example.jpg"
}
```

Alert records are stored in `crowd_data/alerts.json` and contain the event,
count, timestamp, risk level, and notification records.

The HTML report is generated from the currently selected event and current
threshold settings. It includes:

- Summary metrics
- Crowd-size frequency chart
- Risk-frequency chart
- Crowd timeline
- Forecast chart when available
- Threshold values
- Density records
- Saved detection photos

The map uses demonstration coordinates unless event-specific location data is
provided. Do not interpret sample map coordinates as live GPS data.

## Training workflow

`train_model.py` is an older, separate TensorFlow workflow for experimentation.
Before using it:

- Install its TensorFlow and TensorFlow Hub dependencies.
- Update `DATASET_PATH`, `META_FILE`, and `FRAME_DIR`.
- Replace the example absolute Windows paths with paths on your machine.
- Confirm the dataset and metadata columns match the script.

The Streamlit dashboard uses YOLOv8 weights and does not automatically run the
training script.

## Troubleshooting

### The app does not start

Confirm the virtual environment is active and reinstall dependencies:

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

### The model cannot be loaded

Confirm `yolov8n.pt` exists in the project directory, or set a valid
`YOLO_MODEL_PATH`.

### Telegram does not send

- Confirm both Telegram environment variables are present.
- Confirm the token was not revoked.
- Open the bot and send `/start`.
- Confirm `TELEGRAM_CHAT_ID` is numeric.
- Restart Streamlit after editing `.env`.
- Check the terminal output for Telegram API errors.

### Forecast is not shown

Collect and save at least five observations for the same event. Prophet also
requires valid timestamps and numeric crowd counts.

### A saved image is missing

Keep the `crowd_data/images/` directory and its files together with
`crowd_data/events.json`. The JSON stores paths to the saved images.

## Privacy and safety

- The application counts detected people and does not require facial identity.
- Do not upload sensitive images without appropriate permission.
- Protect `.env`, bot tokens, SMTP credentials, and generated reports.
- Use access control before deploying the dashboard beyond a trusted local
  environment.
- Human operators and emergency services remain responsible for decisions.

## Limitations and future work

- Current input is image upload or browser camera capture; production CCTV/RTSP
  streaming is not implemented.
- Hotspot and evacuation coordinates are demonstration data.
- JSON storage is suitable for a local prototype; a database is recommended
  for concurrent operators.
- Alert delivery depends on external credentials and network availability.
- Future improvements include multi-camera monitoring, zone-level tracking,
  people-in/out flow, dynamic routes, fall detection, authentication, database
  storage, and production-grade notification delivery.

## Administrator

**Mohamed Dadapeer**

Project administrator and developer for the Real-Time Vision-Based Crowd Risk
Prediction and Smart Evacuation System.
