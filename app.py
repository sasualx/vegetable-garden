from flask import Flask, request, jsonify, send_file
from PCA9685 import PCA9685
import RPi.GPIO as GPIO
import smbus2
import bme280
import os
import pytz
import subprocess
from datetime import datetime

# Relay Setup
Relay_Ch1 = 26
Relay_Ch2 = 20
Relay_Ch3 = 21

# Environmental Sensor Setup
address = 0x77
bus = smbus2.SMBus(1)
calibration_params = bme280.load_calibration_params(bus, address)

# Setup PWM hat. This could be done with the PWM GPIO pins on the pi directly,
# but using the hat makes it easier and more scalable.
pwm = PCA9685(0x40, debug=False)
pwm.setPWMFreq(120)

# Initial outputs
ch_pwm = {
    '0': 0,
    '1': 0,
    '2': 40
}

app = Flask(__name__)
app.lights = 0
app.dehumidifier = 1


def setup_relay():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)

    GPIO.setup(Relay_Ch1, GPIO.OUT)
    GPIO.setup(Relay_Ch2, GPIO.OUT)
    GPIO.setup(Relay_Ch3, GPIO.OUT)

@app.route('/dehumidifier_off', methods=['GET'])
def turn_dehumidifier_off():
    app.dehumidifier = 0
    GPIO.output(Relay_Ch2, GPIO.HIGH)
    return jsonify({'success': True, 'message': 'Dehumidifier turned off'})


@app.route('/dehumidifier_on', methods=['GET'])
def turn_dehumidifier_on():
    app.dehumidifier = 1
    GPIO.output(Relay_Ch2, GPIO.LOW)
    return jsonify({'success': True, 'message': 'Dehumidifier turned on'})


def set_pwm(values):
    for channel, value in values.items():
        if channel in [2, '2'] or app.lights or value == 0:
            pwm.setServoPulse(int(channel), int(value))


@app.route('/turn_on', methods=['GET'])
def turn_on():
    app.lights = 1
    change_pwm_values({'0': 24, '1': 24})
    set_pwm(ch_pwm)
    return jsonify({'state': app.lights})


def change_pwm_values(values):
    for k in values.keys():
        if k not in [0, 1, '0', '1'] or app.lights:
            ch_pwm[k] = max(0, min(99, values[k]))
    set_pwm(ch_pwm)


@app.route('/update_snapshot', methods=['GET', 'POST'])
def update_snapshot():
    # Get the current date and time in ISO 8601 format (to minutes)
    timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M")

    shutter_speed = '3000' if ch_pwm['0'] == 99 else '4000' if ch_pwm['0'] > 75 else '8333' if ch_pwm[
                                                                                                   '0'] > 30 else 20000
    # Construct the command

    command = [
        'libcamera-still',
        '-o', f'/home/pi/growbox/images/image{timestamp}.jpg',
        '--rotation', '180',
        '--shutter', str(shutter_speed),
        '--brightness', '-0.2'
    ]

    # Run the command
    subprocess.run(command)
    return jsonify({'success': True, 'message': 'pic updated'})


@app.route('/image', methods=['GET', 'POST'])
def get_image():
    directory_path = '/home/pi/growbox/images/'
    images = os.listdir(directory_path)

    images.sort(reverse=True)
    if images:
        return send_file('images/' + images[0], mimetype='image/jpeg')
    else:
        return "No images found", 404


@app.route('/light_state', methods=['GET'])
def light_state():
    return jsonify({'state': app.lights})


@app.route('/turn_off', methods=['GET'])
def turn_off():
    app.lights = 0
    turn_dehumidifier_on()
    set_pwm({0: 0, 1: 0})
    return jsonify({'state': app.lights})


@app.route('/light_switch', methods=['GET', 'POST'])
def light_switch():
    if app.lights == 1:
        app.lights = 0
        set_pwm({0: 0, 1: 0})
    else:
        app.lights = 1
        change_pwm_values({'0': 50, '1': 50})
        set_pwm(ch_pwm)
    return jsonify({'state': 'success'})


@app.route('/sensor_data', methods=['GET'])
def get_sensor_data():
    # Logic to read sensor data goes here
    data = bme280.sample(bus, address, calibration_params)

    desired_timezone = pytz.timezone('Europe/Berlin')

    timestamp_tz = data.timestamp.replace(tzinfo=pytz.utc).astimezone(desired_timezone)
    sensor_data = {
        'timestamp': timestamp_tz.strftime('%Y/%m/%d %H:%M:%S'),
        'temperature': data.temperature,
        'humidity': data.humidity,
        'pressure': data.pressure,
        'top_led': ch_pwm['0'] if app.lights else 0,
        'side_led': ch_pwm['1'] if app.lights else 0,
        'fan': ch_pwm['2'],
        'lights': app.lights,
        'dehumidifier': app.dehumidifier
    }
    return jsonify(sensor_data)


@app.route('/get_pwm', methods=['GET'])
def get_pwm():
    if 'channel' in request.args:
        return jsonify({'pwm_value': ch_pwm[request.args['channel']]})
    if app.lights:
        return jsonify(ch_pwm)
    else:
        return jsonify({
            '0': 0, '1': 0, '2': ch_pwm['2']
        })


# Example route to set PWM values
@app.route('/set_values', methods=['POST'])
def set_values():
    pwm_values = request.json  # Assuming JSON payload like {'pin': 18, 'duty_cycle': 50}
    change_pwm_values(pwm_values)
    return jsonify({'success': True, 'message': 'PWM set'})


if __name__ == '__main__':
    set_pwm(ch_pwm)
    setup_relay()
    if datetime.now().time() <= datetime.strptime("18:00",
                                                  "%H:%M").time() or datetime.now().time() >= datetime.strptime(
            "23:00", "%H:%M").time():
        app.lights = 1
        change_pwm_values({'0': 24, '1': 24})
        set_pwm(ch_pwm)
    app.run(host='0.0.0.0', port=8000)  # Run Flask app on all available interfaces
