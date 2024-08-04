import os
import requests
import time
import csv
import math
from datetime import datetime

running = True

min_temp = 27.0
max_temp = 27.2
cnt = 7

address = 'http://localhost:8000'


def increase_light(val0, val1, temp):
    val_delta = int(math.ceil((min_temp - temp) * 2))
    requests.post(address + '/set_values',
                  json={'0': val0 + val_delta, '1': val1 + val_delta})


def decrease_light(val0, val1, temp):
    val_delta = int(math.ceil((temp - max_temp) * 4))
    if val_delta >= val0:
        val_delta = val0 - 2
    requests.post(address + '/set_values',
                  json={'0': val0 - val_delta, '1': val1 - val_delta})


file_name = 'environment_log.csv'
file_exists = os.path.isfile(file_name)
file = open(file_name, mode='a')
writer = csv.writer(file)

# Write the header to the file if the file does not exist
if not file_exists:
    writer.writerow(
        ['Time and Date', 'Temperature', 'Humidity', 'Pressure (hPa)', 'Top LED', 'Side LED', 'Fan', 'dehumidifier'])

# loop forever
while running:
    try:
        # Read sensor data and write it to csv
        cnt = cnt + 1
        data = requests.get(address + '/sensor_data').json()

        # Save time, date, temperature, humidity, and pressure in .txt file
        writer.writerow([data['timestamp'],
                         '{:.2f}'.format(data['temperature']),
                         '{:.2f}'.format(data['humidity']),
                         '{:.2f}'.format(data['pressure']),
                         str(data['top_led']),
                         str(data['side_led']),
                         str(data['fan']),
                         str(data['dehumidifier'])
                         ])
        file.flush()

        print(data, cnt)

        # Automate dehumidifier based on humidity
        if data['humidity'] > 60 and data['dehumidifier'] == 0:
            requests.get(address + '/dehumidifier_on')
            requests.post(address + '/set_values',
                          json={'0': data['top_led'] - 40, '1': data['side_led'] - 40})
            cnt = 5
        if data['humidity'] < 56 and data['dehumidifier'] == 1:
            requests.get(address + '/dehumidifier_off')
            requests.post(address + '/set_values',
                          json={'0': data['top_led'] + 40, '1': data['side_led'] + 40})
            cnt = 5

        # Adjust Lighting every 60 seconds based on temperature
        if cnt >= 6:
            if data['temperature'] > max_temp:
                decrease_light(data['top_led'], data['side_led'], data['temperature'])
                cnt = 0
            if data['temperature'] < min_temp:
                increase_light(data['top_led'], data['side_led'], data['temperature'])
                cnt = 0

        time.sleep(10)

    except KeyboardInterrupt:
        print('Program stopped')
        running = False
        file.close()
    except Exception as e:
        print('An unexpected error occurred:', str(e))
        time.sleep(10)
