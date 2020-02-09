'''
**********************************************************************
* Filename    : views
* Description : views for server
* Author      : Cavon
* Brand       : SunFounder
* E-mail      : service@sunfounder.com
* Website     : www.sunfounder.com
* Update      : Cavon    2016-09-13    New release
**********************************************************************
'''

from django.shortcuts import render_to_response
from django.conf import settings
from .driver import camera, stream
from remote_control.templates.models import RecordDriver
from remote_control.templates.utils import VideoCaptureThreading
from picar import back_wheels, front_wheels
from django.http import HttpResponse
import picar


try:
    picar.setup()
    fw = front_wheels.Front_Wheels(debug=False, db=settings.DB_FILE)
    bw = back_wheels.Back_Wheels(debug=False, db=settings.DB_FILE)
    cam = camera.Camera(debug=False, db=settings.DB_FILE)
    cam.ready()
    bw.ready()
    fw.ready()
except:
    print('Cannot setup picar, are your running on a Raspberry Pi?')

SPEED = 60
bw_status = 0

if settings.STREAM:
    print(stream.start())
else:
    capture = VideoCaptureThreading(width=160, height=120)


def home(request):
    return render_to_response("base.html")


def run(request):
    global SPEED, bw_status, action, SAVE_IMAGES
    debug = ''
    if 'action' in request.GET:
        SAVE_IMAGES = True
        action = request.GET['action']
        # ============== Back wheels =============
        if action == 'bwready':
            bw.ready()
            bw_status = 0
        elif action == 'forward':
            bw.speed = SPEED
            bw.forward()
            bw_status = 1
            debug = "speed =", SPEED
        elif action == 'backward':
            bw.speed = SPEED
            bw.backward()
            bw_status = -1
        elif action == 'stop':
            bw.stop()
            bw_status = 0
        # ============== Front wheels =============
        elif action == 'fwready':
            fw.ready()
        elif action == 'fwleft':
            fw.turn_left()
        elif action == 'fwright':
            fw.turn_right()
        elif action == 'fwstraight':
            fw.turn_straight()
        elif 'fwturn' in action:
            fw.turn(int(action.split(':')[1]))
        # ================ Camera =================
        elif action == 'camready':
            cam.ready()
        elif action == "camleft":
            cam.turn_left(40)
        elif action == 'camright':
            cam.turn_right(40)
        elif action == 'camup':
            cam.turn_up(20)
        elif action == 'camdown':
            cam.turn_down(20)
        elif not settings.STREAM and action == 'startcapture':
            capture.start()
        elif not settings.STREAM and action == 'stopcapture':
            capture.stop()
        elif not settings.STREAM and action == 'startfsd':
            pass
        elif not settings.STREAM and action == 'stopfsd':
            pass
    if 'speed' in request.GET:
        speed = int(request.GET['speed'])
        if speed < 0:
            speed = 0
        if speed > 100:
            speed = 100
        SPEED = speed
        if bw_status != 0:
            bw.speed = SPEED
        debug = "speed =", speed
    if 'action' in request.GET or 'speed' in request.GET:
        RecordDriver.objects.create(action=action, speed=SPEED)
    if settings.STREAM:
        host = stream.get_host().decode('utf-8').split(' ')[0]
        return render_to_response("run.html", {'host': host})
    else:
        return render_to_response("run_modified.html")


def cali(request):
    if 'action' in request.GET:
        action = request.GET['action']
        # ========== Camera calibration =========
        if action == 'camcali':
            print('"%s" command received' % action)
            cam.calibration()
        elif action == 'camcaliup':
            print('"%s" command received' % action)
            cam.cali_up()
        elif action == 'camcalidown':
            print('"%s" command received' % action)
            cam.cali_down()
        elif action == 'camcalileft':
            print('"%s" command received' % action)
            cam.cali_left()
        elif action == 'camcaliright':
            print('"%s" command received' % action)
            cam.cali_right()
        elif action == 'camcaliok':
            print('"%s" command received' % action)
            cam.cali_ok()

        # ========= Front wheel cali ===========
        elif action == 'fwcali':
            print('"%s" command received' % action)
            fw.calibration()
        elif action == 'fwcalileft':
            print('"%s" command received' % action)
            fw.cali_left()
        elif action == 'fwcaliright':
            print('"%s" command received' % action)
            fw.cali_right()
        elif action == 'fwcaliok':
            print('"%s" command received' % action)
            fw.cali_ok()

        # ========= Back wheel cali ===========
        elif action == 'bwcali':
            print('"%s" command received' % action)
            bw.calibration()
        elif action == 'bwcalileft':
            print('"%s" command received' % action)
            bw.cali_left()
        elif action == 'bwcaliright':
            print('"%s" command received' % action)
            bw.cali_right()
        elif action == 'bwcaliok':
            print('"%s" command received' % action)
            bw.cali_ok()
        else:
            print('command error, error command "%s" received' % action)
    return render_to_response("cali.html")


def connection_test(request):
    return HttpResponse('OK')
