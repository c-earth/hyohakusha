"""Record HTTP camera frames concurrently with bounded TCP control.

Class inputs: IP and new output folder. Outputs: JPEGs and JSON timestamps.
The worker owns HTTP only; no TCP/rover commands. Host time brackets are not
exposure timestamps. Requests have a 1.5 s timeout and 2 MB size limit.
"""

import json
import threading
import time
import urllib.request
from datetime import datetime, timezone

import cv2
import numpy as np


class TimedCameraRecorder:
    """Own one bounded HTTP worker with timestamped frame evidence.

Constructor inputs: address string and new Path folder. Attributes: stop event,
frames list (completed entries), error string or None, worker thread. Up to 60
frames; callers must stop/close after a trial. No motor/control access exists.
"""

    def __init__(self, address, folder):
        """Create folder and initialize stopped worker; no return value."""
        self.address = address
        self.folder = folder
        self.folder.mkdir(parents=True, exist_ok=False)
        self.frames = []
        self.error = None
        self.epoch_ns = None
        self.stop_event = threading.Event()
        self.worker = threading.Thread(target=self.record, name='calibration-http-camera', daemon=True)

    def start(self):
        """Start HTTP worker; no inputs/return value or TCP action."""
        self.worker.start()

    def record(self):
        """Capture/decode/save bounded JPEGs until stopped; no inputs/return."""
        try:
            while not self.stop_event.is_set() and len(self.frames) < 60:
                begin_ns = time.monotonic_ns()
                begin_utc = datetime.now(timezone.utc).isoformat()
                with urllib.request.urlopen(f'http://{self.address}/capture', timeout=1.5) as reply:
                    data = reply.read(2_000_001)
                end_ns = time.monotonic_ns()
                if len(data) > 2_000_000 or cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR) is None:
                    raise ValueError('Invalid/oversized camera frame')
                name = f'frame-{len(self.frames):04d}.jpg'
                (self.folder/name).write_bytes(data)
                self.frames.append(dict(file=name, request_ns=begin_ns, received_ns=end_ns,
                                        request_utc=begin_utc, received_utc=datetime.now(timezone.utc).isoformat()))
                self.stop_event.wait(0.03)
        except Exception as error:
            self.error = str(error)

    def close(self):
        """Stop/join HTTP worker and save manifest; return completed frame list."""
        self.stop_event.set()
        self.worker.join(timeout=2)
        if self.worker.is_alive():
            self.error = 'Camera worker did not finish within 2 s'
        if self.epoch_ns is not None:
            for frame in self.frames:
                frame['request_ms'] = (frame['request_ns']-self.epoch_ns)/1e6
                frame['received_ms'] = (frame['received_ns']-self.epoch_ns)/1e6
        (self.folder/'frames.json').write_text(json.dumps(dict(frames=self.frames, error=self.error), indent=2), encoding='utf-8')
        return self.frames
