# vegetable-garden

This is an automation project for controlling a smart-garden style box for growing your vegetables with LED lights.

The project has 4 main components:
- app.py is the api server that the controlling raspberry pi runs
  -  It creates a flask app that opens api endpoints for controlling different aspects of the environment, which handles all the calls to the raspberry pi sensors and different hats.
  - api calls can be used to take a picture with the camera, update control values, and retrieve environment data.
- monitor.py
  - gets the sensor data and control values from the api server, writes those values into a csv file for plotting and posteriority
  - adjusts to the light and to the dehumidifier based on the sensor data retrieved, by making calls to the api endpoints that control those systems
- litstream.py is a web dashboard that uses streamlit
  - it shows the most rescent camera image
  - provides sliders to adjust the lights and fan manually
  - displays charts for the sensor values, light intensity and dehumidifier usage
- crontab
  - turns on/off the lights at different times in the day
  - takes snapshots with the camera every 15 minutes

The app.py needs to be run from the controlling raspberry pi, and the crontab needs to replace the pi's crontab file using `crontab -e`, but the other two components can be ran on any other system as long as the IP address of the controlling pi is adjusted.

### Electrical Setup
WARNING: I am in no way responsible for any problems caused by a faulty electrical setup. These systems should be wired by people who have a good grasp of what they are doing.

I have a number of LED boards that work with 24V, and I was also able to buy a few fans that work with 24V, so I got a 24V power supply. In order to power the pi from it, you have to have a way to step down the voltage. My initial option was a buck converter, but then I also got this [motor driver hat](https://www.waveshare.com/rpi-motor-driver-board.htm) which also has a 5v step down and can power the pi through the GPIO pins.

The Dehumidifier works with 9V, so I got a convertor that steps down 24V to 9V, and I plug the output of that into the relay board, and a cable from that to the dehumidifier, so that I can use the relay to turn it on or off. You will need a dehumidifier that automatically turns on when power is given, such as one with a physical button that you can leave in the on position.

Since I have a brushless fan for the exhaust, and my attempt to make a low pass filter to convert PWM signal to analogue voltage was imperfect, I also just take the 9V output to the exhaust fan so that it performs at a reasonable level without being too loud.

### Pi HATS
Besides the pi, the bme280 sensor and the camera, all the hats are optional. You will however need a relay or a relay hat if you want to turn any devices like the dehumidifier on or off.

For controlling the PWM devices, I went with a [servo driver hat](http://www.waveshare.com/wiki/Servo_Driver_HAT). I just use the provided library code, and easily control each output separately. This makes it very easy to add more pwm devices such as lamps and fans later.

For controlling any devices that don't have a pwm controller but work with pwm voltage, you can use the motor driver hat mentione in the electrical setup.

I got [this relay board](https://www.waveshare.com/rpi-relay-board.htm) since it has 3 relays and I can use it for future improvements as well. 

## Future Iterations

### Self Watering system
I already bought soil humidity sensors and pumps in order to one day implement a self watering system, but for now I'm fine watering my plants on my own.

### Use environment values rather than hardcoding the specific time the lights are on or off.