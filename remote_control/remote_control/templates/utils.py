"""
Based on https://github.com/gilbertfrancois/video-capture-async
"""

from django.conf import settings
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
    def __init__(self, capture):
        self.capture = capture
        self.started = False
        self.read_lock = threading.Lock()
        if not os.path.exists(settings.RECORD_DIR):
            os.makedirs(settings.RECORD_DIR)

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
            if frame.shape[1] != self.capture.width:
                frame = imutils.resize(frame, width=self.capture.width)
            cv2.imwrite(os.path.join(settings.RECORD_DIR, "%s.png" % int(timezone.now().timestamp() * 1000)), frame)
            time.sleep(settings.RECORD_TIME_DELAY_SECONDS - time.time() + start_time)
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


class FSD:
    def __init__(self, capture, front_wheels, back_wheels, camera):
        self.capture = capture
        self.front_wheels = front_wheels
        self.back_wheels = back_wheels
        self.camera = camera
        if self.back_wheels is not None:
            self.back_wheels.speed = 0

    def start(self):
        pass

    def stop(self):
        pass
