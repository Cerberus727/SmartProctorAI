import json
import os

def get_rects(detections, class_name):
    return [det['bbox'] for det in detections if det['class_name'] == class_name]

def generate_session_summary(start_time, end_time, events_filepath, summary_filepath):
    total_phone_time = 0
    total_looking_away_time = 0
    total_no_face_time = 0
    total_multiple_person_time = 0
    max_risk = 0.0

    # Parse events if file exists
    if os.path.exists(events_filepath):
        with open(events_filepath, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue
                
                event = data.get("event")
                duration = data.get("duration", 0)
                risk_score = data.get("risk_score", 0)

                # Track highest risk score
                if risk_score > max_risk:
                    max_risk = risk_score

                # Aggregate relevant durations
                if event == "PHONE":
                    total_phone_time += duration
                elif event == "LOOKING_AWAY":
                    total_looking_away_time += duration
                elif event in ("NO_FACE", "FACE_NOT_VISIBLE", "NO_FACE_DETECTED"):
                    total_no_face_time += duration
                elif event in ("MULTIPLE_PERSON", "MULTIPLE_FACES_DETECTED"):
                    total_multiple_person_time += duration

    # Compute total duration
    total_duration = end_time - start_time

    # Determine overall risk
    if total_phone_time > 5 or total_no_face_time > 15:
        overall_risk = "HIGH"
    elif total_looking_away_time > 10:
        overall_risk = "MEDIUM"
    else:
        overall_risk = "LOW"

    # Create summary dictionary
    summary = {
        "total_duration": round(total_duration, 2),
        "phone_time": round(total_phone_time, 2),
        "looking_away_time": round(total_looking_away_time, 2),
        "no_face_time": round(total_no_face_time, 2),
        "multiple_person_time": round(total_multiple_person_time, 2),
        "max_risk": round(max_risk, 2),
        "overall_risk": overall_risk
    }

    # Save to JSON
    with open(summary_filepath, "w") as f:
        json.dump(summary, f, indent=4)

    # Print summary
    print("\n" + "="*30)
    print("      SESSION SUMMARY")
    print("="*30)
    for key, value in summary.items():
        print(f"{key.replace('_', ' ').capitalize()}: {value}")
    print("="*30 + "\n")
