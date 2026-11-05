# Real-Time Vision-Based Crowd Risk Detection System

## One-Minute Project Summary

The Real-Time Vision-Based Crowd Risk Detection System is an AI-powered safety
application for monitoring crowds in public spaces. It uses YOLOv8 computer vision
to detect and count people from images, classifies the crowd into risk levels, and
uses historical data to forecast possible crowd growth. When a dangerous crowd
level is detected, the system displays an emergency warning and provides
notification and evacuation support for security teams.

## Presentation Slide Content

### Slide 1: Project Title

**Real-Time Vision-Based Crowd Risk Detection and Smart Evacuation System**

An AI-based solution for early crowd-risk detection and emergency response.

### Slide 2: Problem Statement

- Overcrowding can become dangerous within a short period.
- Manual security monitoring is slow and difficult to scale.
- Security teams may not receive enough warning before a crowd emergency.
- Emergency communication must be fast, clear, and centralized.

### Slide 3: Project Objectives

- Detect people automatically from images or camera feeds.
- Estimate the current crowd size.
- Classify the crowd safety level.
- Forecast future crowd growth.
- Generate alerts before the situation becomes critical.
- Support calm and safe evacuation.

### Slide 4: Proposed Solution

The system combines computer vision, risk analysis, forecasting, and emergency
communication in one Streamlit dashboard.

```text
Image or Camera Input
          ↓
YOLOv8 Person Detection
          ↓
Crowd Counting
          ↓
Risk Classification
          ↓
Crowd Forecasting
          ↓
Alert and Evacuation Support
          ↓
Dashboard and Historical Logs
```

### Slide 5: Core Features

- YOLOv8-based person detection
- Bounding boxes around detected people
- Configurable safe, warning, and danger thresholds
- Low, Moderate, and High crowd-risk classification
- Historical event logging
- Prophet-based crowd forecasting
- Interactive hotspot map
- Alert history dashboard
- Emergency banner and status indicators
- Voice evacuation announcement and siren
- Safe-route map display

### Slide 6: Alert and Emergency Workflow

When the detected crowd reaches the danger threshold:

1. The dashboard displays a critical emergency alert.
2. The event name, crowd count, risk level, and timestamp are shown.
3. Notification messages are prepared for the event security team, police, email,
   and event management application.
4. A voice message instructs people to move calmly toward the nearest exit.
5. Safe evacuation routes are displayed.
6. The alert is stored in `crowd_data/alerts.json`.
7. An alert cooldown prevents duplicate records during application refreshes.

The application supports real email and Telegram delivery through environment
variables. It also supports notification simulation for demonstrations without
requiring external credentials.

### Slide 7: Risk Classification

| Risk Level | Meaning | Suggested Action |
| --- | --- | --- |
| Low | Crowd is within the safe limit | Continue normal monitoring |
| Moderate | Crowd is growing and requires attention | Monitor movement and keep exits clear |
| High | Crowd exceeds the danger limit | Notify security and begin crowd-control actions |

The thresholds can be adjusted from the application sidebar for different venue
sizes and safety policies.

### Slide 8: Technology Stack

| Layer | Technology |
| --- | --- |
| Programming language | Python |
| User interface | Streamlit |
| Object detection | YOLOv8 and Ultralytics |
| Image processing | OpenCV and Pillow |
| Data analysis | Pandas and NumPy |
| Charts and maps | Plotly and Streamlit maps |
| Forecasting | Facebook Prophet |
| Notifications | Gmail SMTP and Telegram Bot API |
| Voice alert | gTTS |
| Data storage | JSON files |

### Slide 9: System Benefits

- Faster awareness of dangerous crowd levels
- Supports early intervention instead of late reaction
- Reduces dependence on manual counting
- Provides a clear audit trail of events and alerts
- Gives security teams one dashboard for monitoring and response
- Uses density information without facial recognition or identity tracking

### Slide 10: Application Areas

- Stadiums and sports events
- Railway and metro stations
- Religious gatherings
- Public festivals and concerts
- Demonstrations and public meetings
- Shopping centers and transport hubs
- Smart-city public safety operations

### Slide 11: Future Enhancements

- Live CCTV and RTSP video-stream integration
- Multi-camera monitoring with camera-specific zones
- Real GPS-based evacuation routes
- Mobile notifications for security staff
- Operator authentication and role-based access
- Cloud deployment and centralized monitoring
- Edge inference on Jetson or similar devices
- Crowd-flow and abnormal-behavior analysis

## Final Presentation Statement

This project demonstrates how AI and computer vision can support public safety by
turning crowd images into actionable risk information. Instead of only reporting
how many people are present, the system combines detection, prediction, alerting,
and evacuation guidance to help security teams respond earlier and more
effectively.
