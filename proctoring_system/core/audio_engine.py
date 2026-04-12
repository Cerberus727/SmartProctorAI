import threading
import time
import numpy as np
import torch

try:
    import sounddevice as sd
except ImportError:
    sd = None
    print("[WARN] sounddevice not installed. Audio monitoring is temporarily disabled.")
    print("       To enable: pip install sounddevice")

# 1. LOAD MODEL GLOBALLY ONCE TO AVOID RELOADING DELAYS
print("[INFO] Loading Silero VAD model...")
try:
    silero_model, utils = torch.hub.load(repo_or_dir='snakers4/silero-vad',
                                         model='silero_vad',
                                         force_reload=False,
                                         trust_repo=True)
    (get_speech_timestamps, save_audio, read_audio, VADIterator, collect_chunks) = utils
    silero_model.eval()
    print("[INFO] Silero VAD model loaded successfully.")
except Exception as e:
    silero_model = None
    get_speech_timestamps = None
    print(f"[WARN] Failed to load Silero VAD model: {e}")


def detect_speech_silero(duration=0.5, fs=16000):
    """
    Records audio for `duration` seconds and passes it to Silero VAD.
    Returns whether speech was detected inside the chunk.
    """
    if not sd or silero_model is None:
        return {"speech": False, "segments": []}
        
    try:
        # Record audio block (non-blocking in main thread, blocks its own background thread)
        audio_data = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='float32')
        sd.wait()
        
        # 2. AUDIO CAPTURE: Convert numpy block [N, 1] to torch 1D Tensor [N]
        audio_tensor = torch.from_numpy(audio_data).float().squeeze()
        
        # Audio normalisation (Boost volume, ignore flat silence)
        max_val = torch.max(torch.abs(audio_tensor))
        if max_val > 0.001: # Avoid amplifying pure static
            audio_tensor = audio_tensor / max_val
            
        # Pass to VAD with a lower sensitivity threshold (default is 0.5)
        speech_timestamps = get_speech_timestamps(
            audio_tensor, 
            silero_model, 
            sampling_rate=fs,
            threshold=0.3,
            min_speech_duration_ms=100
        )
        
        is_speech = len(speech_timestamps) > 0
        if is_speech:
            print(f"[Audio] Silero VAD: Speech Detected! Segments: {speech_timestamps}")
        else:
            # Print heart-beat max audio level if no speech detected just to verify it hears us
            pass
            
        return {
            "speech": is_speech,
            "segments": speech_timestamps
        }
    except Exception as e:
        print(f"[ERROR] Audio capture/VAD error: {e}")
        return {"speech": False, "segments": []}

class AudioEngine:
    """
    Lightweight, background-threaded audio event engine using Silero VAD.
    Runs asynchronously to ensure it never blocks the video processing loop.
    """
    def __init__(self, sample_rate=16000, duration=0.5):
        self.sample_rate = sample_rate
        self.duration = duration
        
        self.last_audio_result = {"speech": False, "segments": []}
        self.is_running = False
        self.thread = None

    def start(self):
        if not sd or silero_model is None:
            return
            
        self.is_running = True
        self.thread = threading.Thread(target=self._audio_capture_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.is_running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)

    def _audio_capture_loop(self):
        while self.is_running:
            self.last_audio_result = detect_speech_silero(
                duration=self.duration, 
                fs=self.sample_rate
            )
            # Small sleep to prevent tight CPU looping string execution
            time.sleep(0.01)

    def get_audio_event(self) -> dict:
        """
        Returns the instantaneous audio analysis state. Fast O(1) read for the main process_frame loop.
        """
        return {
            "speech": self.last_audio_result.get("speech", False)
        }
