# AI Remote Proctoring Platform

A full-stack, real-time AI proctoring platform that integrates advanced computer vision pipelines (YOLOv8, MediaPipe, FaceNet, and an LSTM-based Temporal Cheating model) directly into a React-based online testing environment.

## System Architecture
* **Frontend**: React, Vite, Tailwind CSS (Interactive test-taking environment, student/admin dashboards).
* **Backend**: FastAPI, SQLAlchemy, WebSockets (Secure exam serving, live proctoring events, DB management).
* **AI Engine**: Python, PyTorch, OpenCV (FaceNet identity verification, Custom LSTM sequence model, Risk & Behavior engines).

## Key Features
* **Pre-Exam Face Verification**: Enforces a secure FaceNet enrollment phase (`/verify`) gathering facial embeddings before test access is granted.
* **Temporal Cheating Detection**: A custom-trained LSTM model processes behavioral event sequences over time to identify complex anomalous patterns.
* **Face Tracking & Head Pose**: Ensures the examinee is looking forward. Triggers alerts for looking away/down.
* **Gaze Estimation**: Computes pupil orientation to assess attention off-screen.
* **Multi-Face Detection**: Identifies if multiple people enter the camera frame during the exam.
* **Prohibited Objects Detection**: Leverages YOLOv8 to aggressively monitor restricted devices like Cell Phones and Books.
* **Real-Time Websocket Alerts**: The ML pipeline triggers infractions stored on the backend which reflect instantly on the user's React dashboard.
* **Auto-Submission**: Enforces automatic test termination upon reaching maximum violation thresholds.

## Installation & Setup

### 1. Prerequisites
* **Python** (>= 3.8)
* **Node.js** (>= 18)

### 2. Setup the Python Environment
We highly recommend running the backend and ML services within a virtual environment.

```bash
# From the root directory:
cd DeepLearningFaceDetection

# Create a virtual environment
python -m venv venv

# Activate on Windows
.\venv\Scripts\activate
# Activate on Mac/Linux
source venv/bin/activate

# Install required backend and ML dependencies
pip install -r requirements.txt
pip install -r backend/requirements.txt
pip install mediapipe==0.10.9
```
*Note: PyTorch models (FaceNet, Temporal, YOLOv8) will auto-download their weight checkpoints on the first run.*

### 3. Setup the Frontend Environment
Open a separate terminal for the React frontend:

```bash
cd frontend
npm install
```

## Running the Application

To run the full stack locally, you need to spin up both the backend API server and the frontend React app.

### Terminal 1: Start the Backend & ML Service
Ensure your Python virtual environment is active.

```bash
# Navigate to the backend directory
cd backend

# Run the FastAPI server via Uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Terminal 2: Start the Frontend
```bash
# Navigate to the frontend directory
cd frontend

# Spin up the Vite development server
npm run dev
```

The platform will now be accessible in your browser at: `http://localhost:5173`

### Standard Testing Flow:
1. Student accesses **Student Dashboard**.
2. Clicks **Start Test**.
3. Enters the **Verification Phase**, where FaceNet captures and verifies 10 embedding references.
4. Auto-redirects to the **Live Test Phase**, actively protected by the YOLO + Behavior Engine + Temporal model.

## System Logs and Behavior
- Real-time ML infractions are appended chronologically to `<root>/events.json`.
- The FastAPI backend systematically watches this file and broadcasts live alert events over WebSockets to the React frontend.
- Risk Engine scoring logic and trigger metrics can be tuned inside `proctoring_system/core/risk_engine.py` and `proctoring_system/config/settings.py`.
