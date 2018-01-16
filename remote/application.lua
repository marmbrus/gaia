local ow_pin = -1
local dht_pin = 1
local status_pin = 0

gpio.mode(status_pin, gpio.OUTPUT)
gpio.write(status_pin, gpio.HIGH)

if ow_pin ~= -1 then
  ds18b20.setup(ow_pin)
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
  
  if dht_pin ~= -1 then
    status, temp, humi, temp_dec, humi_dec = dht.read(dht_pin)
    a = {}
    a["sensor"] = wifi.sta.getmac().."-dht"
    a["temperature_c"] = temp
    a["humidity"] = humi
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