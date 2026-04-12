from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
import json
import os
import io
from datetime import datetime
import tempfile
import torch
import torchaudio

# --- GLOBALLY LOAD SILERO VAD FOR BROWSER AUDIO STREAMS ---
print("[INFO] Loading Silero VAD model in WebSockets for frontend streaming...")
try:
    silero_model, utils = torch.hub.load(repo_or_dir='snakers4/silero-vad',
                                         model='silero_vad',
                                         force_reload=False,
                                         trust_repo=True)
    get_speech_timestamps = utils[0]
    silero_model.eval()
except Exception as e:
    silero_model = None
    get_speech_timestamps = None
    print(f"[WARN] Failed to load Silero VAD in WebSockets: {e}")

router = APIRouter()

connections = []

@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    connections.append(ws)
    print("BACKEND: WS CONNECTED. Current connections:", len(connections))
    
    # Local session tracking for audio chunks to avoid false positives
    speech_counter = 0

    try:
        while True:
            # We use `receive()` to capture both text metadata or binary audio frames
            message = await ws.receive()
            
            if message.get("text") is not None:
                pass  # Future text commands (e.g., {"type": "audio"})
                
            elif message.get("bytes") is not None:
                audio_bytes = message["bytes"]
                if silero_model is None:
                    continue
                
                try:
                    # 1. Save byte chunk to a temporary file for torchaudio decoder
                    # Browsers send WebM (Chrome) or MP4 (Safari) in binary
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_audio:
                        temp_audio.write(audio_bytes)
                        temp_path = temp_audio.name
                        
                    # 2. Decode using torchaudio
                    waveform, sample_rate = torchaudio.load(temp_path)
                    os.remove(temp_path)
                    
                    # 3. Fast Resample/Mono conversion if required by Silero
                    if sample_rate != 16000:
                        resampler = torchaudio.transforms.Resample(orig_freq=sample_rate, new_freq=16000)
                        waveform = resampler(waveform)
                        
                    if waveform.shape[0] > 1:
                        waveform = torch.mean(waveform, dim=0, keepdim=True)
                        
                    audio_tensor = waveform.squeeze()
                    
                    # Normalize dynamic volume to make voices pop
                    max_val = torch.max(torch.abs(audio_tensor))
                    if max_val > 0.001:
                        audio_tensor = audio_tensor / max_val
                        
                    # 4. Pass normalized tensor to Silero Model
                    speech_timestamps = get_speech_timestamps(
                        audio_tensor, 
                        silero_model, 
                        sampling_rate=16000,
                        threshold=0.3,
                        min_speech_duration_ms=100
                    )
                    
                    # 5. Smoothing and Alert Logic
                    if len(speech_timestamps) > 0:
                        speech_counter += 1
                        print(f"[WS AUDIO] Speech Detected! Sequence: {speech_counter}")
                    else:
                        speech_counter = max(0, speech_counter - 1)
                        
                    if speech_counter >= 2:
                        print(f"[WS AUDIO] Triggering SPEECH_DETECTED Alert!")
                        # Log to events.json so AlertContext / event_watcher instantly picks it up!
                        events_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../events.json"))
                        log_entry = {
                            "event": "SPEECH_DETECTED",
                            "start_time": datetime.now().isoformat(),
                            "duration": 1.0,
                            "risk_score": 0.3
                        }
                        try:
                            with open(events_path, "a") as f:
                                f.write(json.dumps(log_entry) + "\n")
                        except:
                            pass
                        
                except Exception as e:
                    # Usually happens if the chunk is too small/invalid to be parsed as a full file
                    pass
    except Exception as e:
        if ws in connections:
            connections.remove(ws)
        print("BACKEND: WS DISCONNECTED. Current connections:", len(connections))

async def broadcast_event(event_data):
    if "timestamp" not in event_data:
        event_data["timestamp"] = str(datetime.now())
    print("BACKEND BROADCASTING:", event_data)
    for conn in connections:
        try:
            await conn.send_json(event_data)
        except Exception as e:
            print("BACKEND SEND ERROR:", e)

# The watcher that links detections to websocket events!
async def event_watcher():
    events_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../events.json"))
    last_size = 0
    print(f"BACKEND: Starting event watcher on {events_path} ...")
    
    while True:
        try:
            if os.path.exists(events_path):
                current_size = os.path.getsize(events_path)
                if current_size > last_size:
                    with open(events_path, "r") as f:
                        f.seek(last_size)
                        new_lines = f.readlines()
                        last_size = current_size
                    
                    for line in new_lines:
                        line = line.strip()
                        if line:
                            event_data = json.loads(line)
                            ev_type = event_data.get("event")
                            if ev_type:
                                # MANDATORY: connect detection to backend broadcast
                                await broadcast_event(event_data)
                elif current_size < last_size:
                    last_size = 0
        except Exception as e:
            print("BACKEND EVENT WATCHER ERROR:", e)
        await asyncio.sleep(1)

@router.on_event("startup")
async def startup_event():
    asyncio.create_task(event_watcher())

