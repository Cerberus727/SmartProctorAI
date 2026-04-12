# Project Architecture: AI Remote Proctoring Platform

## Overview
The AI Remote Proctoring Platform is a robust, computer-vision based application designed to monitor examinees in real-time during remote assessments. It utilizes deep learning models (YOLOv8 and MediaPipe) to detect restricted behaviors, track facial geometry, and compute adaptive risk scores. The system is composed of three main layers: a React frontend, a FastAPI backend, and a core AI/ML proctoring engine.

---

## High-Level Architecture

The architecture follows a modern distributed stack, separating the user interface, the business logic/API layer, and the heavy-lifting computer vision ML pipelines.

### 1. Frontend (Client Layer)
- **Technology Stack:** React, Vite, TailwindCSS
- **Purpose:** Provides separate dashboards and interfaces for Students and Administrators/Proctors.
- **Key Components:**
  - **Student View (`Student.jsx`, `TestPage.jsx`):** Renders the exam interface and continually captures webcam feeds or triggers the monitoring pipeline.
  - **Admin View (`Admin.jsx`, `MonitorPage.jsx`):** Allows proctors or admins to create tests, view active student sessions, and receive real-time alerts.
  - **WebSocket/Alerts (`ProctorAlerts.jsx`, `AlertContext.jsx`):** Subscribes to real-time events from the backend to immediately notify admins of cheating or suspicious behavior.

### 2. Backend (API & Middleware Layer)
- **Technology Stack:** Python, FastAPI, SQLAlchemy, WebSockets
- **Purpose:** Acts as the central orchestrator routing data between the frontend dashboards, the database, and the proctoring ML engine.
- **Key Components:**
  - **REST API Routes (`auth`, `test`, `proctor`):** Handles user authentication, exam creation/management, and fetching proctoring logs or session summaries.
  - **WebSockets (`routes/websockets.py`):** Establishes two-way communication to push real-time computer vision events (e.g., "Multiple faces detected", "Phone detected") directly to the Admin dashboard.
  - **Database Layer (`database.py`, `domain.py`):** Persistent storage of users, tests, risk thresholds, and localized event logs.
  - **Proctoring Service (`proctor_service.py`):** Acts as the bridge that manages the ingestion of ML outputs and dispatches them to the proper data stores or WebSocket channels.

### 3. AI Proctoring System (Machine Learning Layer)
- **Technology Stack:** Python, OpenCV, YOLOv8, MediaPipe, PyTorch/Keras
- **Purpose:** The core computer vision engine that processes video frames to detect anomalies.
- **Key Components:**
  - **YOLO Detector (`yolo_detector.py`):** Aggressively monitors the frame for restricted objects such as cell phones, laptops, keyboards, and TVs.
  - **Face & Gaze Estimators (`face_mesh.py`, `gaze_estimator.py`, `head_pose.py`):** Tracks the examinee's face to ensure they are looking forward, calculating gaze direction and head pose.
  - **Activity & Temporal Inference (`activity_detector.py`, `temporal_inference.py`):** Analyzes behaviors over time (using `temporal_proctor_trained_on_processed.pt` / `cheating_model_binary.pth`) rather than single-frame anomalies, which radically reduces false positives.
  - **Risk & Event Engine (`risk_engine.py`, `event_engine.py`):** Calculates an adaptive risk score based on the severity and duration of detected infractions. Outputs structured events (`events.json`) and session summaries (`session_summary.json`).

---

## System Workflow & Data Flow

1. **Session Initiation:**
   - A student logs in via the React frontend and starts an exam.
   - The browser prompts for webcam access.
   - A WebSocket connection is established with the FastAPI backend.

2. **Continuous Monitoring:**
   - Video frames are actively processed by the ML Engine (`proctoring_system/main.py`).
   - *Face Module:* Verifies the identity of the student and checks for additional faces.
   - *Behavior Module:* Estimates head pose and gaze pupil direction to flag looking away or looking down.
   - *Object Module:* YOLOv8 sweeps the background for restricted electronics.
   - *Temporal Module:* Feeds sequential historical states into a temporal model (e.g., LSTM/Transformer) to confirm if an activity is genuinely anomalous cheating behavior.

3. **Risk Scoring & Event Generation:**
   - The `Risk Engine` adjusts the student's live "Risk Score".
   - If a specific threshold is breached (e.g., cell phone visible for > 2 seconds), the `Alert Manager` generates an incident payload.
   
4. **Broadcasting & Logging:**
   - The generated event is pushed to the FastAPI backend.
   - The backend records the event in the database for auditing and broadcasts it over WebSockets to any connected proctors.
   - The Admin frontend dashboard receives the WebSocket message and surfaces a high-priority alert for the specified student.
   
5. **Session Conclusion:**
   - When the exam is submitted or terminated, the ML layer aggregates all data into a complete `session_summary.json`.
   - The backend finalizes the session log, allowing administrators to review a playback of flagged timestamps and overall session risk metrics.