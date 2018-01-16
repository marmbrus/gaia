-- check onewire
ow.setup(5)
print(ow.reset(5))

local status_pin = 0
gpio.mode(status_pin, gpio.OUTPUT)
gpio.write(status_pin, gpio.LOW)
gpio.write(0, gpio.HIGH)

pwm.setup(0, 1, 512)

bin/zookeeper-server-start etc/kafka/zookeeper.properties
bin/kafka-server-start etc/kafka/server.properties


file.remove("init.lua")