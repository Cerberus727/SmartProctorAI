# Remote Proctoring System

A robust, localized, computer-vision based proctoring system to monitor examinees in real-time. It uses YOLOv8 for object detection and MediaPipe for facial geometry & behavior analysis to calculate risk scores based on restricted behavior during exams. 

## Features
* **Face Tracking & Head Pose:** Ensures the examinee is looking forward. Checks for looking away or looking down.
* **Gaze Estimation:** Calculates direction of pupils to assess attention off-screen.
* **Multi-Face Detection:** Triggers an alarm and tracks total time if more than one person enters the examinee's camera frame.
* **Electronics Detection:** Uses YOLOv8 to aggressively monitor restricted devices such as Cell Phones, Laptops, Keyboards, Mice, TVs, or Remotes within the camera view.
* **Risk Engine & Alert Manager:** Constantly computes an adaptive risk score and logs infractions locally.
* **Session Summaries:** Exports an aggregated human-readable summary out to JSON upon program exit (total time looking away, on phone, multple faces, etc.).

## Setup Instructions

### 1. Prerequisites
Make sure you have Python (>=3.8) installed on your system.

### 2. Prepare Virtual Environment
It is recommended to run this within a virtual environment.

```bash
python -m venv venv

# Activate on Windows
.\venv\Scripts\activate

# Activate on Mac/Linux
source venv/bin/activate
```

### 3. Install Dependencies
Make sure you install the required computer vision libraries (YOLO, MediaPipe, OpenCV):

```bash
# General packages
pip install -r requirements.txt

# Also ensure you have MediaPipe installed 
pip install mediapipe==0.10.9
```

*Note: Models automatically download their initial weights the first time they run if absent.*

### 4. Running the Application
Ensure your active working directory is at the root of the project.

Run the main dashboard loop:
```bash
python proctoring_system/main.py
```
Press `q` anytime to exit the camera feed. 

### 5. Testing YOLO Behavior Explicitly
If you just want to stress-test your object detection/device filtering algorithms:
```bash
python proctoring_system/test_best.py
```

## Logs and Behaviors 
- A comprehensive sequence of flags triggered during the session is output sequentially into `events.json`. 
- An overall duration aggregation is printed into the terminal and saved inside `session_summary.json` at the conclusion of every execution cycle from `main.py`.

## Directory Structure
- `config/` - Houses unified thresholds and settings.
- `core/` - The logic systems controlling behavioral queues, aggregate risk score computations, and event handling.
- `input/` - Manages video/webcam frame buffering.
- `models/` - Wrappers initializing logic around `YOLOv8`, `FaceMesh`, and `HeadPose` estimation pipelines.
- `utils/` - Global drawing functions for user bounding box interfaces and logging parsers.
