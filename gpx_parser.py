import streamlit as st
import cv2
import numpy as np
from PIL import Image
import requests
import gpxpy
import gpxpy.gpx
import pandas as pd
import plotly.express as px
import haversine as hs
from haversine import Unit




st.write("Streamlit is also great for more traditional ML use cases like computer vision or NLP. Here's an example of edge detection using OpenCV. 👁️") 

uploaded_file = st.file_uploader("Upload a track", type=["gpx"])
if uploaded_file:
    gpx_file = uploaded_file.getvalue().decode("utf-8")
    gpx = gpxpy.parse(gpx_file)

a = 0
route_info = list()
for track in gpx.tracks:
    for segment in track.segments:
        for point in segment.points:
            if a == 0:
                time_init = point.time
                distance = 0
            else:
                loc1 = (prev_lat,prev_lon)
                loc2 = (point.latitude,point.longitude)
                distance = hs.haversine(loc1,loc2,unit=Unit.METERS)
            route_info.append({
                'latitude': point.latitude,
                'longitude': point.longitude,
                'elevation': point.elevation,
                'time': str(point.time-time_init),
                'distance': distance                 
            })
            prev_lat = point.latitude
            prev_lon = point.longitude
            a+=1


df = pd.DataFrame(route_info)


df['elevationDiff'] = df['elevation'] - df['elevation'].shift(-1)
df['elevationDiffSmothed'] = df['elevationDiff'].rolling(window=91).mean()
totalAscend  = df[df['elevationDiffSmothed'] > 0.00]['elevationDiffSmothed'].sum()

heightDiff = df['elevation'].max() - df['elevation'].min()

df['distanceAcc'] = df['distance'].cumsum()
totalDist = df['distance'].sum()

st.write('     number of points:',len(df))
st.write('Total Ascend (metres):', int(totalAscend))
st.write('Max height diff (metres):', int(heightDiff))
st.write('Distance (metre):',int(totalDist))
st.write('Time:', df.iloc[-1]['time'])
fig = px.line_map(
    df,
    lat="latitude",
    lon="longitude",
    height = 600,
    zoom = 13,
    #color = 'elevation'
)

# Set the background map style (e.g., "open-street-map", "carto-positron")
fig.update_layout(map_style="open-street-map")

fig = px.area(df[::10], x = 'distanceAcc', y = 'elevation',range_y=[df['elevation'].min()-10, df['elevation'].max() + 10])

st.plotly_chart(fig)
