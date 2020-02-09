"""
Based on https://github.com/gilbertfrancois/video-capture-async
"""

from django.conf import settings
from django.utils import timezone

import threading
import cv2
import time
import os


class VideoCaptureThreading:
    def __init__(self, src=0, width=640, height=480):
        self.src = src
        self.cap = cv2.VideoCapture(self.src)
        self.width = width
        self.height = height
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.grabbed, self.frame = self.cap.read()
        self.started = False
        self.read_lock = threading.Lock()
        if not os.path.exists(settings.CAPTURE_DIR):
            os.makedirs(settings.CAPTURE_DIR)

    def set(self, var1, var2):
        self.cap.set(var1, var2)

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
            grabbed, frame = self.cap.read()
            cv2.imwrite(os.path.join(settings.CAPTURE_DIR, "%s.png" % int(timezone.now().timestamp() * 1000)), frame)
            time.sleep(settings.CAPTURE_TIME_DELAY_SECONDS - time.time() + start_time)
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
        self.thread.join()

    def __exit__(self, exec_type, exc_value, traceback):
        self.cap.release()
