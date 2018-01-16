#!/bin/bash

/home/pi/.local/bin/nodemcu-uploader --port $1 --start_baud 9600 upload credentials.lua
/home/pi/.local/bin/nodemcu-uploader --port $1 --start_baud 9600 upload application.lua
/home/pi/.local/bin/nodemcu-uploader --port $1 --start_baud 9600 upload init.lua