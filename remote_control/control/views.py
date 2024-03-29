"""
.. module:: control.views
   :synopsis: Views to control car
.. module author:: Adam Moss <adam.moss@nottingham.ac.uk>
"""

from typing import List
from django.shortcuts import render_to_response
from django.utils import timezone
from django.http import HttpResponse, StreamingHttpResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators import gzip

from remote_control.driver import camera, stream
from control.models import Recording
from control.utils import Capture

from picar import back_wheels, front_wheels
import picar

import json
import cv2
import git
import glob
import os
import logging
import numpy as np 

try:
    picar.setup()
    fw = front_wheels.Front_Wheels(debug=False, db=settings.CONFIG_FILE)
    bw = back_wheels.Back_Wheels(debug=False, db=settings.CONFIG_FILE)
    cam = camera.Camera(debug=False, db=settings.CONFIG_FILE)
    cam.ready()
    bw.ready()
    fw.ready()
    straight_angle = fw._straight_angle
    min_angle = fw._min_angle
    max_angle = fw._max_angle
except:
    fw = None
    bw = None
    cam = None
    straight_angle = 90
    min_angle = 45
    max_angle = 135
    print('[!] Cannot setup picar, are your running on a Raspberry Pi?')

capture = Capture(width=settings.CAPTURE_WIDTH, height=settings.CAPTURE_HEIGHT,
                  record_dir=settings.RECORD_DIR, record_time_delay=settings.RECORD_TIME_DELAY_SECONDS)

logging.basicConfig(format='%(asctime)s - %(message)s', filename="picar.log", level=logging.INFO)

try:
    import autopilot as ap
    fsd = ap.AutoPilot(capture, fw, bw, cam)
except:
    fsd = None
    print('[!] Could not import autopilot package, have you installed it?')

SPEED = 60
ANGLE = straight_angle

def get_fsd_modules() -> List[str]:
    modules = []
    if os.path.isdir(settings.MODULE_DIR):
        for d in os.listdir(settings.MODULE_DIR):
            if os.path.isdir(os.path.join(settings.MODULE_DIR, d)):
                if d not in ['__pycache__']:
                    modules.append(d)
    return modules


def home(request):
    return render_to_response("base.html")


def connection_test(request):
    return HttpResponse('OK')


@csrf_exempt
def car(request):
    global SPEED, ANGLE
    logging.info(request.body.decode('utf-8'))
    data = json.loads(request.body.decode('utf-8'))
    print(data)
    if 'angle' in data:
        angle = max(min(data['angle'], max_angle), min_angle)
        if angle != ANGLE:
            ANGLE = angle
            capture.record_suffix = '%s_%s' % (ANGLE, SPEED)
            fw.turn(angle)
    if 'speed' in data:
        speed = max(min(data['speed'], 100), -100)
        if speed != SPEED:
            SPEED = speed
            capture.record_suffix = '%s_%s' % (ANGLE, SPEED)
            if speed < 0:
                bw.backward()
                bw.speed = abs(speed)
            elif speed == 0:
                bw.stop()
            else:
                bw.forward()
                bw.speed = speed
    if 'record' in data:
        if data['record']:
            capture.start()
            Recording.objects.create()
        else:
            capture.stop()
    if 'delete' in data:
        if data['delete']:
            try:
                timestamp = Recording.objects.latest('timestamp').timestamp
            except:
                timestamp = timezone.now()
            files = glob.glob(settings.RECORD_DIR + '*')
            for f in files:
                if os.path.isfile(f) and int(f.split(settings.RECORD_DIR)[1].split('_')[0]) > timestamp.timestamp() * 1000:
                    os.remove(os.path.join(settings.RECORD_DIR, f))
    if 'fsd' in data and fsd is not None:
        if data['fsd']:
            fsd.start()
        else:
            fsd.stop()
    if 'fsd_model' in data and fsd is not None:
        fsd.load_model(data['fsd_model'])
    if 'action' in data:
        action = data['action']
        # ========== Camera calibration =========
        if action == 'camcali':
            cam.calibration()
        elif action == 'camcaliup':
            cam.cali_up()
        elif action == 'camcalidown':
            cam.cali_down()
        elif action == 'camcalileft':
            cam.cali_left()
        elif action == 'camcaliright':
            cam.cali_right()
        # ========= Front wheel cali ===========
        elif action == 'fwcali':
            fw.calibration()
        elif action == 'fwcalileft':
            fw.cali_left()
        elif action == 'fwcaliright':
            fw.cali_right()
        # ========= Back wheel cali ===========
        elif action == 'bwcali':
            bw.calibration()
        elif action == 'bwcalileft':
            bw.cali_left()
        elif action == 'bwcaliright':
            bw.cali_right()
        # ========= Save===========
        elif action == 'calisave':
            cam.cali_ok()
            fw.cali_ok()
            bw.cali_ok()
    return HttpResponse(status=200)


def control(request):
    try:
        cam.ready()
        bw.ready()
        fw.ready()
    except:
        pass
    fsd_modules = get_fsd_modules()
    if 'base' in fsd_modules:
        fsd_selection = 'base'
    elif len(fsd_modules) > 0:
        fsd_selection = fsd_modules[0]
    else:
        fsd_selection = None
    args = {
        'straight_angle': straight_angle,
        'min_angle': min_angle,
        'max_angle': max_angle,
        'fsd_modules': fsd_modules,
        'fsd_selection': fsd_selection,
    }
    return render_to_response("control.html", args)


def calibration(request):
    return render_to_response("calibration.html")


def get_config(request):
    conf = open(settings.CONFIG_FILE, 'r')
    lines = conf.readlines()
    conf.close()
    config = []
    for line in lines:
        if line[0] != '#':
            if len(line.split('=')) == 2:
                try:
                    config.append({'variable': line.split('=')[0], 'value': int(line.split('=')[1].rstrip('\n'))})
                except:
                    pass
    return HttpResponse(json.dumps(config), content_type='application/json')


@gzip.gzip_page
def current_image(request):
    """
    Get image in JPEG format. Could do this by using capture.get_current_image() if _update thread was running, but
    wanted to start and stop the thread by toggling record driving (so this may not be running). The reason why I grab
    several frames is due to the buffering issue described in
    https://stackoverflow.com/questions/24370725/opencv-videocapture-only-updates-after-5-reads
    """
    image = None
    cal_points = np.load('/home/pi/SunFounder_PiCar-V/remote_control/control/cal.npy') # calibration points
    
    for _ in range(5):
        ret, frame = capture.camera.read()
        frame[cal_points==1,0] = 255
        frame[cal_points==1,1] = 0
        frame[cal_points==1,2] = 0
        if frame is not None:
            ret, image = cv2.imencode('.JPEG', frame)
    if image is not None:
        content = (b'--frame\r\n' + b'Content-Type: image/jpeg\r\n\r\n' + image.tobytes() + b'\r\n\r\n')
        return HttpResponse(content, content_type="multipart/x-mixed-replace;boundary=frame")
    else:
        return HttpResponse(status=500)


def about(request):
    repo = git.Repo(search_parent_directories=True)
    args = {
        'commit': repo.head.commit
    }
    return render_to_response("about.html", args)
