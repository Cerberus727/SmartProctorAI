import cv2

def draw_boxes(frame, detections):
    for det in detections:
        x1, y1, x2, y2 = det['bbox']
        
        # Replace raw labels with clean text
        if det['class_name'] == 'person':
            label = "Person Detected"
            color = (0, 255, 0)
        elif det['class_name'] == 'cell phone':
            label = "Phone Detected"
            color = (0, 0, 255)
        else:
            label = det['class_name'].title() + " Detected"
            color = (255, 0, 0)
        
        # Keep drawing clean and recognizable
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        
        # Draw background for text to ensure readability
        (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        cv2.rectangle(frame, (x1, y1 - 20), (x1 + w, y1), color, -1)
        # Choose text color based on background luminance roughly, here black or white
        text_color = (0, 0, 0) if color[1] > 150 else (255, 255, 255)
        cv2.putText(frame, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, text_color, 1)

def draw_tracks(frame, tracks, debug=False):
    if not debug:
        return
        
    for object_id, (centroid, rect) in tracks.items():
        text = f"ID {object_id}"
        
        # Ensure labels are readable
        (w, h), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
        text_x, text_y = centroid[0] - 10, centroid[1] - 10
        cv2.rectangle(frame, (text_x, text_y - h - 5), (text_x + w, text_y + 5), (0, 0, 255), -1)
        cv2.putText(frame, text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        
        cv2.circle(frame, (centroid[0], centroid[1]), 4, (0, 0, 255), -1)

def draw_ui(frame, data):
    # Base padding
    h, w, _ = frame.shape
    y_offset = 30
    x_offset = 15
    line_height = 25
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.7
    font_thickness = 2
    
    debug_mode = data.get('debug', False)

    # 1. Display Formatted Risk Score
    risk = data.get('risk_score', 0.0)
    risk_color = (0, 0, 255) if risk > 0.5 else ((0, 165, 255) if risk > 0.2 else (0, 255, 0))
    cv2.putText(frame, f"Risk Score: {risk:.2f}", (x_offset, y_offset), font, font_scale, risk_color, font_thickness)
    y_offset += line_height + 5

    # 2. Display Temporal Model Prediction
    temporal_pred = data.get('temporal_pred')
    if isinstance(temporal_pred, dict):
        temp_score = temporal_pred['score']
        temp_state = temporal_pred['state']
    else:
        temp_score = temporal_pred if temporal_pred is not None else 0.0
        temp_state = 'RED' if temp_score > 0.6 else 'GREEN'
    if temporal_pred is not None:
        temporal_color = (0, 0, 255) if temp_state == 'RED' else ((0, 255, 255) if temp_state == 'YELLOW' else (0, 255, 0))
        cv2.putText(frame, f"Temporal Pre: {temp_score:.2f} [{temp_state}]", (x_offset, y_offset), font, font_scale, temporal_color, font_thickness)
        y_offset += line_height + 5

    # 3. Display Gaze
    gaze = data.get('gaze', 'unknown').upper()
    gaze_color = (0, 255, 0) if gaze == "CENTER" else (0, 0, 255)
    cv2.putText(frame, f"Gaze: {gaze}", (x_offset, y_offset), font, font_scale, gaze_color, font_thickness)
    y_offset += line_height + 5

    # 4. Display Verified Status (Right Side)
    is_verified = data.get('is_verified', True) # By default, true until facenet runs
    v_text = "FACE VERIFIED" if is_verified else "UNVERIFIED PERSON"
    v_color = (0, 255, 0) if is_verified else (0, 0, 255)
    (v_w, v_h), _ = cv2.getTextSize(v_text, font, font_scale, font_thickness)
    cv2.putText(frame, v_text, (w - v_w - 20, 30), font, font_scale, v_color, font_thickness)

    # Display Head Pose (Debug Only)
    if debug_mode:
        pose = data.get('head_pose', {'yaw': 0.0, 'pitch': 0.0})
        cv2.putText(frame, f"Yaw: {pose['yaw']:.2f}", (x_offset, y_offset), font, font_scale, (255, 255, 0), font_thickness)
        y_offset += line_height
        cv2.putText(frame, f"Pitch: {pose['pitch']:.2f}", (x_offset, y_offset), font, font_scale, (255, 255, 0), font_thickness)
        y_offset += line_height

    # Show active events (Right Side below Verified Status)
    events = data.get('events', [])
    if events:
        evt_y = 60
        cv2.putText(frame, "Alerts:", (w - 200, evt_y), font, 0.6, (0, 0, 255), 2)
        evt_y += line_height
        for e in events:
            # Ensure text wraps or aligns right so it doesn't leave the screen 
            cv2.putText(frame, f"- {e}", (w - 240, evt_y), font, 0.5, (0, 0, 255), 1)
            evt_y += line_height