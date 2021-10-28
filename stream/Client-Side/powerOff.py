#!/usr/bin/env python

import RPi.GPIO as GPIO
import subprocess


GPIO.setmode(GPIO.BOARD)
GPIO.setup(5, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.wait_for_edge(5, GPIO.FALLING)

subprocess.call(['sudo', 'shutdown', '-h', 'now'], shell=False)