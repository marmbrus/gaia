#!/bin/bash

echo VERSION=\'`git rev-parse --short HEAD`\' > version.lua

/home/pi/.local/bin/nodemcu-uploader --port $1 --start_baud 57600 --baud 57600 upload credentials.lua
/home/pi/.local/bin/nodemcu-uploader --port $1 --start_baud 57600 --baud 57600 upload application.lua
/home/pi/.local/bin/nodemcu-uploader --port $1 --start_baud 57600 --baud 57600 upload init.lua
/home/pi/.local/bin/nodemcu-uploader --port $1 --start_baud 57600 --baud 57600 upload version.lua