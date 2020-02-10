"""
Based on https://github.com/gilbertfrancois/video-capture-async
"""

from django.utils import timezone
import threading
import cv2
import time
import os
import imutils


class Capture:
    def __init__(self, src=0, width=640, height=480):
        self.src = src
        self.camera = cv2.VideoCapture(self.src)
        self.width = width
        self.height = height
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    def set(self, var1, var2):
        self.camera.set(var1, var2)

    def cleanup(self):
        self.camera.release()

    def __exit__(self, exec_type, exc_value, traceback):
        self.cleanup()


class Record:
    def __init__(self, capture, record_dir, record_time_delay=1, record_size_limit=1):
        self.capture = capture
        self.record_dir = record_dir
        self.record_time_delay = record_time_delay
        self.record_size_limit = record_size_limit
        self.started = False
        self.thread = None
        self.read_lock = threading.Lock()
        if not os.path.exists(record_dir):
            os.makedirs(record_dir)

    def start(self):
        if self.started:
            print('[!] Threaded video capturing has already been started.')
            return None
        self.started = True
        self.thread = threading.Thread(target=self.update, args=())
        self.thread.start()
        return self

    def update(self):
        while self.started:
            start_time = time.time()
            grabbed, frame = self.capture.camera.read()
            if frame is not None:
                if frame.shape[1] != self.capture.width:
                    frame = imutils.resize(frame, width=self.capture.width)
                timestamp = timezone.now().timestamp() * 1000
                tot_bytes = sum(os.path.getsize(os.path.join(self.record_dir, f)) for f in os.listdir(self.record_dir))
                if tot_bytes / 1073741824 < self.record_size_limit:
                    cv2.imwrite(os.path.join(self.record_dir, "%s.png" % int(timestamp)), frame)
                else:
                    print('[!] Not saving image, directory size too large.')
            time.sleep(self.record_time_delay - time.time() + start_time)
            with self.read_lock:
                self.grabbed = grabbed
                self.frame = frame

    def read(self):
        with self.read_lock:
            frame = self.frame.copy()
            grabbed = self.grabbed
        return grabbed, frame

    def stop(self):
        self.started = False
        if self.thread is not None:
            self.thread.join()
