python /home/pi/gaia/gaia.py&
chromium-browser --incognito --kiosk http://127.0.0.1:5000&
cd /home/pi/core
nodejs server.js -p 8080 --listen "0.0.0.0" -a : -w ~/
