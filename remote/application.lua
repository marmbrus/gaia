dofile("version.lua")

local ow_pin = -1
local dht_pin = 1
local status_pin = 0

local lux_sda = -1
local lux_scl = -1

local color_sda = -1
local color_scl = -1

local weight_clk= -1
local weight_dt= -1

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
      else
        gpio.write(status_pin, gpio.HIGH)
        print(code, data)
      end
    end)
end

function read ()
  if lux_sda ~= -1 then
    status = tsl2561.init(5, 6, tsl2561.ADDRESS_FLOAT, tsl2561.PACKAGE_T_FN_CL)
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
  
  if dht_pin ~= -1 then
    status, temp, humi, temp_dec, humi_dec = dht.read(dht_pin)
    a = {}
    a["sensor"] = wifi.sta.getmac().."-dht"
    a["temperature_c"] = temp
    a["humidity"] = humi
    record(a)
  end
  
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
  
  if weight_clk ~= -1 then
    raw = 0
    for i=1,10 do 
      raw = raw + hx711.read() 
    end
    raw = raw / 10
    a = {}
    a["sensor"] = wifi.sta.getmac().."-weight"
    a["raw"] = raw
    a["grams"] = -0.002274989854*(raw+69177.6)
    record(a)
  end
  
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

cron.schedule("* * * * *", read)