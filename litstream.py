#!/home/pi/growbox/venv/bin/python3
import streamlit as st
from io import BytesIO
from PIL import Image
import requests
from datetime import datetime, timedelta
import pandas as pd
import altair as alt
import time

st.set_page_config(
    page_title="Growbox",
    page_icon="chart_with_upwards_trend",
    layout="wide",
)

all_data = pd.read_csv('environment_log.csv', delimiter=',')

all_data['Time and Date'] = pd.to_datetime(all_data['Time and Date'])
now = datetime.now()
time_threshold = now - timedelta(hours=24)
data = all_data[all_data['Time and Date'] > time_threshold]

address = 'http://localhost:8000'


# Function to fetch the image
def get_image_from_endpoint(url):
    response = requests.get(url)
    response.raise_for_status()  # Ensure we notice bad responses
    return Image.open(BytesIO(response.content))


# URL of your image endpoint
image_url = address + "/image"

# Fetch and display the image
image = get_image_from_endpoint(image_url)
st.image(image, caption="Plant snapshot")

if 'refresh' not in st.session_state:
    st.session_state.refresh = 0


# Function to increment the state
def refresh_state():
    time.sleep(5)
    st.session_state.refresh += 1


def load_css():
    st.markdown("""
        <style>
        .primary {
            background-color: green;
            color: white;
            border: none;
            padding: 10px 20px;
            text-align: center;
            text-decoration: none;
            display: inline-block;
            font-size: 16px;
            margin: 4px 2px;
            cursor: pointer;
            border-radius: 12px;
        }
        .secondary {
            background-color: red;
            color: white;
            border: none;
            padding: 10px 20px;
            text-align: center;
            text-decoration: none;
            display: inline-block;
            font-size: 16px;
            margin: 4px 2px;
            cursor: pointer;
            border-radius: 12px;
        }
        </style>
    """, unsafe_allow_html=True)


def get_status():
    response = requests.get(address + '/light_state')
    return response.json().get('state')


# Function to toggle the status via the API
def toggle_status():
    requests.get(address + '/light_switch')


status = get_status()

# Set button color based on status

button_class = 'primary' if status == 0 else 'secondary'

# Display the button
if st.button(f"Turn {'Off' if status == 1 else 'On'}", key='toggle_button', help='Click to toggle', type=button_class):
    # Toggle the status and update the button color
    toggle_status()
    st.rerun()

if st.button("Update Snapshot", key="update_snapshot"):
    requests.get(address + "/update_snapshot")

st.button("Refresh", on_click=refresh_state)

pwm_values = requests.get(address + '/get_pwm').json()


# Function to update PWM values
def update_pwm(channel, key):
    value = st.session_state[key]
    response = requests.post(address + '/set_values', json={channel: value})


st.session_state.top_pwm = pwm_values['0']
st.session_state.side_pwm = pwm_values['1']
st.session_state.fan_pwm = pwm_values['2']

# Slider for API request - Top LED
top_led_slider = st.slider('Top LED', 0, 99, pwm_values['0'], key='top_fan', on_change=update_pwm, args=(0, 'top_fan'))

# Slider for API request - Side LED
side_led_slider = st.slider('Side LED', 0, 99, pwm_values['1'], key='side_fan', on_change=update_pwm,
                            args=(1, 'side_fan'))

# Slider for API request - Fan
fan_slider = st.slider('Fan', 0, 99, pwm_values['2'], on_change=update_pwm, args=(2, 'fan'), key='fan')

# Data Visualization
temp_chart = alt.Chart(data).mark_line(color='blue').encode(
    x='Time and Date:T',
    y=alt.Y('Temperature:Q', title='Temperature',
            scale=alt.Scale(domain=[data['Temperature'].min(), data['Temperature'].max()])),
)
# Create Altair chart for value2
humidity_chart = alt.Chart(data).mark_line(color='red').encode(
    x='Time and Date:T',
    y=alt.Y('Humidity:Q', title='Humidity',
            scale=alt.Scale(domain=[data['Humidity'].min(), data['Humidity'].max()])),
)

top_led_chart = alt.Chart(data).mark_line(color='red').encode(
    x='Time and Date:T',
    y=alt.Y('LED', title='LED')
)
side_led_chart = alt.Chart(data).mark_line(color='red').encode(
    x='Time and Date:T',
    y=alt.Y('Side LED', title='Side LED')
)

fan_chart = alt.Chart(data).mark_line(color='red').encode(
    x='Time and Date:T',
    y=alt.Y('Fan', title='Fan')
)
pressure_chart = alt.Chart(data).mark_line(color='red').encode(
    x='Time and Date:T',
    y=alt.Y('Pressure (hPa)', title='Pressure (hPa)')
)

dehumidifier_chart = alt.Chart(data).mark_line(color='green').encode(
    x='Time and Date:T',
    y=alt.Y('dehumidifier', title='dehumidifier')
)

st.altair_chart(temp_chart, use_container_width=True)
st.altair_chart(humidity_chart, use_container_width=True)
st.altair_chart(dehumidifier_chart, use_container_width=True)
st.altair_chart(top_led_chart, use_container_width=True)
st.altair_chart(fan_chart, use_container_width=True)
