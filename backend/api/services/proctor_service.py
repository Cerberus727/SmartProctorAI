import sys, os, cv2, threading, queue, time, importlib.util
import logging

try:
    import torch
    original_load = torch.load
    def _patched_load(*args, **kwargs):
        kwargs['weights_only'] = False
        return original_load(*args, **kwargs)
    torch.load = _patched_load
except ImportError:
    pass

try:
    import mediapipe
    import mediapipe.python.solutions
except ImportError:
    pass

logger = logging.getLogger(__name__)

proctor_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../proctoring_system'))
if proctor_dir not in sys.path:
    sys.path.append(proctor_dir)

frame_queue = queue.Queue(maxsize=1)
stop_event = threading.Event()
_thread = None
stream_lock = threading.Lock()
active_streams = 0

def _mock_imshow(winname, mat):
    if stop_event.is_set():
        raise InterruptedError("Stopped")
    try:
        if frame_queue.full():
            frame_queue.get_nowait()
        frame_queue.put(mat.copy())
    except Exception:
        pass

def _mock_waitKey(delay):
    if stop_event.is_set():
        return ord('q')
    return 1

def _mock_destroyAllWindows():
    pass

cv2.imshow = _mock_imshow
cv2.waitKey = _mock_waitKey
cv2.destroyAllWindows = _mock_destroyAllWindows

main_py_path = os.path.join(proctor_dir, "main.py")
spec = importlib.util.spec_from_file_location("proctor_main", main_py_path)
proctor_main = importlib.util.module_from_spec(spec)
sys.modules["proctor_main"] = proctor_main
spec.loader.exec_module(proctor_main)

# Keep track of multiple clients but use one thread
client_lock = threading.Lock()
clients_connected = 0

def start_proctor_engine():
    global _thread
    
    with stream_lock:
        if _thread is not None and _thread.is_alive():
            if stop_event.is_set():
                _thread.join(timeout=3)
            else:
                return False 

        stop_event.clear()

        while not frame_queue.empty():
            try: frame_queue.get_nowait()
            except: break

        events_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../events.json'))
        if os.path.exists(events_path):
            try: os.remove(events_path)
            except: pass

        os.chdir(proctor_dir)
        def thread_wrapper():
            try:
                proctor_main.main()
            except BaseException as e:
                print("Proctor loop caught exit signal:", e)
        _thread = threading.Thread(target=thread_wrapper, daemon=True)
        _thread.start()
        return True


def stop_proctor_engine(force=False):
    global clients_connected
    with stream_lock:
        if not force and clients_connected > 0:
            return
        stop_event.set()


def generate_frames():
    global clients_connected
    with stream_lock:
        clients_connected += 1

    try:
        while not stop_event.is_set():
            try:
                frame = frame_queue.get(timeout=0.2)
                ret, buffer = cv2.imencode('.jpg', frame)
                if not ret: continue
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
            except queue.Empty:
                if stop_event.is_set() or (_thread is None or not _thread.is_alive()):
                    break
                continue
    finally:
        with stream_lock:
            clients_connected -= 1
            if clients_connected <= 0:
                stop_event.set()
