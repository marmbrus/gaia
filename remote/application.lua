local ow_pin = 1
ds18b20.setup(ow_pin)

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
  sig = crypto.toHex(crypto.hmac("sha1", data, SK))
  http.put(
    'http://192.168.1.64:5000/record',
    'Content-Type: application/json\r\nAuthorization: '..sig..'\r\n',
    data,
    function(code, data)
      if (code < 0) then
        print("HTTP request failed")
      else
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
      print("Illuminance: "..lux.." lx") 
  end
    
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

cron.schedule("*/5 * * * *", read)