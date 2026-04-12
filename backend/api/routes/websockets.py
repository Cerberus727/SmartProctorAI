from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
import json
import os
from datetime import datetime

router = APIRouter()

connections = []

@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    connections.append(ws)
    print("BACKEND: WS CONNECTED. Current connections:", len(connections))
    try:
        while True:
            await ws.receive_text()
    except:
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

