"""
.. module:: control.utils
   :synopsis: Utility classes
.. module author:: Adam Moss <adam.moss@nottingham.ac.uk>
"""


import threading
import cv2
import imutils
import datetime

import time
import os


class Capture:
        
    file_limit = 1073741824
    record_suffix = ''
    
    def __init__(self, src=0, width=640, height=480, record_dir=None, record_time_delay=1, record_size_limit=1):
        self.camera = cv2.VideoCapture(src)
        self.width = width
        self.height = height
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.record_dir = record_dir
        self.record_time_delay = record_time_delay
        print(self.record_time_delay)
        self.record_size_limit = record_size_limit
        self.current_frame = None
        self._started = False
        self._terminate = False
        self._thread = None
        self.last_recorded = time.time()
        if record_dir is not None and not os.path.exists(record_dir):
            os.makedirs(record_dir)
  
    def set(self, var1, var2):
        self.camera.set(var1, var2)

    def cleanup(self):
        self.camera.release()
        
    def start(self):
        if self._started:
            print('[!] Threaded video capturing has already been started.')
            return None
        self._started = True
        self._terminate = False
        self._thread = threading.Thread(target=self._update, args=())
        self._thread.start()
        return self
    
    def _update(self):
        while not self._terminate:
            ret, frame = self.camera.read()
            if frame is not None:
                self.current_frame = frame
                if self.record_dir is not None and time.time() - self.last_recorded > self.record_time_delay:
                    if frame.shape[1] != self.width:
                        frame = imutils.resize(frame, width=self.width)
                    timestamp = datetime.datetime.now().timestamp() * 1000
                    tot_bytes = sum(os.path.getsize(os.path.join(self.record_dir, f)) for f in os.listdir(self.record_dir))
                    if tot_bytes / self.file_limit < self.record_size_limit:
                        if self.record_suffix:
                            filename = "%s_%s.png" % (int(timestamp), self.record_suffix)
                        else:
                            filename = "%s.png" % (int(timestamp))
                        cv2.imwrite(os.path.join(self.record_dir, filename), frame)
                    else:
                        print('[!] Not saving image, directory size too large.')
                    self.last_recorded = time.time()

    def stop(self):
        self._started = False
        self._terminate = True
        if self._thread is not None:
            self._thread.join()
                
    def get_current_frame(self):
        return self.current_frame
    
    def get_current_image(self, fmt='.JPEG'):
        ret, image = cv2.imencode(fmt, self.get_current_frame())
        return image.tobytes()

    def __exit__(self, exec_type, exc_value, traceback):
        self.cleanup()
