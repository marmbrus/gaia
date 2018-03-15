dofile("version.lua")

local ow_pin = -1
local dht_pin = -1
local status_pin = 0

local lux_sda = -1 --6  --2
local lux_scl = -1 -- 5 --3

local color_sda = -1
local color_scl = -1

local weight_clk= 5
local weight_dt= 6

local tare_pin = 2
local calibate_pin = 1

gpio.mode(status_pin, gpio.OUTPUT)
gpio.write(status_pin, gpio.HIGH)

if ow_pin ~= -1 then
  ds18b20.setup(ow_pin)
end

if color_sda ~= -1 then
  i2c.setup(0, color_sda, color_scl, i2c.SLOW)
  tcs34725.enable(function()
    print("TCS34275 Enabled")
  end)
end

if weight_clk ~= -1 then
  hx711.init(weight_clk, weight_dt)
end

sntp.sync(nil,
  function(sec, usec, server, info)
    print('sync', sec, usec, server)
  end,
  function()
   print('failed!')
  end,
  1000)

next_action = nil
function record (r)
  sec, usec, rate = rtctime.get()
  r["sec"] = sec
  r["usec"] = usec
  r["git_hash"] = VERSION
  enc = sjson.encoder(r)
  data = enc:read()
  print(data)
  sig = crypto.toHex(crypto.hmac("sha1", data, SK))
  
  gpio.write(status_pin, gpio.LOW)
  
  http.put(
    URL,
    'Content-Type: application/json\r\nAuthorization: '..sig..'\r\n',
    data,
    function(code, data)
      if (code < 0) then
        print("HTTP request failed")
        if next_action ~= nil then
          next_action()
        end
      else
        gpio.write(status_pin, gpio.HIGH)
        print(code, data)
        if next_action ~= nil then
          next_action()
        end
      end
    end)
end

function read_light ()
  if lux_sda ~= -1 then
    status = tsl2561.init(lux_sda, lux_scl, tsl2561.ADDRESS_FLOAT, tsl2561.PACKAGE_T_FN_CL)
    if status == tsl2561.TSL2561_OK then
        lux = tsl2561.getlux()
        broad, ir = tsl2561.getrawchannels()
        a = {}
        a["sensor"] = "tsl2561"
        a["lux"] = lux
        a["broad"] = broad
        a["ir"] = ir
        record(a)
    end
  end
end
  
function read_temp ()
  if dht_pin ~= -1 then
    status, temp, humi, temp_dec, humi_dec = dht.read(dht_pin)
    a = {}
    a["sensor"] = wifi.sta.getmac().."-dht"
    a["temperature_c"] = temp
    a["humidity"] = humi
    record(a)
  end
end

function read_color ()
  if color_sda ~= -1 then
    clear,red,green,blue=tcs34725.raw()
    a = {}
    a["sensor"] = wifi.sta.getmac().."-rbg"
    a["clear"] = clear
    a["red"] = red
    a["green"] = green
    a["blue"] = blue
    record(a)
  end
end

-- double M = 0.0;
-- double S = 0.0;
-- int k = 1;
-- foreach (double value in valueList) 
-- {
--     double tmpM = M;
--     M += (value - tmpM) / k;
--     S += (value - tmpM) * (value - M);
--     k++;
-- }
-- return Math.Sqrt(S / (k-2));

function raw_weight(samples)
  raw = 0
  m = 0
  s = 0
  for i=1,samples do 
    v = hx711.read()
    tmpM = m
    m = m + (v - tmpM) / i
    s = s + (v - tmpM) * (v - m)
    print(v)
    raw = raw + v
  end
  stddev = math.sqrt(s / (samples - 2))
  print("stddev: "..stddev)
  return raw / samples, stddev
end

function conf_switch(pin, file_name)
  gpio.mode(pin, gpio.INPUT, gpio.PULLUP)
  gpio.trig(pin, "down", function () 
    raw, stddev = raw_weight(10)
    print("Setting "..file_name.." to "..raw)
    
    f = file.open(file_name, "w")
    f.write(raw)
    f.close()
  end)
end

function read_conf(file_name)
  if file.stat(file_name) ~= nil then
    f = file.open(file_name, "r")
    weight = f.readline()
    f.close()
    print("Initilizing "..file_name.." "..weight)
    return weight
  end
  return 1000
end

if tare_pin ~= -1 then
  conf_switch(tare_pin, "weight.0")
end

if calibate_pin ~= -1 then
  conf_switch(calibate_pin, "weight.1000")
end

function read_weight ()
  if weight_clk ~= -1 then
    weight_0 = read_conf("weight.0")
    weight_1000 = read_conf("weight.1000")
    a = {}
    raw, stddev = raw_weight(10)
    a["sensor"] = wifi.sta.getmac().."-weight"
    a["raw"] = raw
    a["stddev"] = stddev
    a["zero"] = weight_0
    a["1kg"] = weight_1000
    a["grams"] = (a["raw"] - weight_0) * 1000 / (weight_1000 - weight_0)
    record(a)
  end
end

function read_ow ()
  if ow_pin ~= -1 then
    ds18b20.read(
        function(ind,rom,res,temp,tdec,par)
          print(temp)
          a = {}
          a["sensor"] = rom
          a["res"] = res
          a["temperature_c"] = temp
          a["tdesc"] = tdec
          a["par"] = par
          record(a)
        end,{})
  end
end

local x = 0
local diff = 10
function pulse()
  pin = 3
  pwm.setup(pin, 100, 0)
  pwm.start(pin)

  t = tmr.create()
  t:register(10, tmr.ALARM_AUTO, function() 
    x = x + diff
    if x == 1020 then
      diff = -10
    end
    if x == 0 then
      diff = 10
    end
    pwm.setduty(pin, duty)
  end)
  t:start()
end

-- file.remove("init.lua")
cron.reset()
-- cron.schedule("* * * * *", read_light)
cron.schedule("* * * * *", read_weight)
-- cron.schedule("* * * * *", read_temp)
-- cron.schedule("* * * * *", read)

-- next_action = function()
--   read_weight()
-- end
-- 
-- read_weight()