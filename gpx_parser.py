import streamlit as st
import numpy as np
from PIL import Image
import requests
import gpxpy
import gpxpy.gpx
import pandas as pd
import plotly.express as px
import haversine as hs
from haversine import Unit




st.write("Upload a GPX file to get basic statistics") 

uploaded_file = st.file_uploader("Upload a track", type=["gpx"])
if uploaded_file:
    gpx_file = uploaded_file.getvalue().decode("utf-8")
    gpx = gpxpy.parse(gpx_file)

    route_info = list()
    fst_point = True
    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                if fst_point:
                    time_init = point.time
                    distance = 0
                    speed = 0
                    fst_point = False
                else:
                    loc1 = (prev_lat,prev_lon)
                    loc2 = (point.latitude,point.longitude)
                    distance = hs.haversine(loc1,loc2,unit=Unit.METERS)
                    speed = 3.6 * distance / (point.time - prev_time).total_seconds()
                route_info.append({
                    'latitude': point.latitude,
                    'longitude': point.longitude,
                    'elevation': point.elevation,
                    'time': str(point.time-time_init),
                    'distance': distance,
                    'speed': speed
                })
                prev_lat = point.latitude
                prev_lon = point.longitude
                prev_time = point.time


    df = pd.DataFrame(route_info)
    elevation_upper_limit = df['elevation'].mean() + 2 * df['elevation'].std()
    elevation_lower_limit = df['elevation'].mean() - 2 * df['elevation'].std()
    df = df[(df['elevation'] < elevation_upper_limit) & (df['elevation'] > elevation_lower_limit)]

    df['elevationDiff'] = df['elevation'] - df['elevation'].shift(1)
    df['elevationDiffSmothed'] = df['elevationDiff'].rolling(window=91).mean()
    totalAscend  = df[df['elevationDiffSmothed'] > 0.00]['elevationDiffSmothed'].sum()

    heightDiff = df['elevation'].max() - df['elevation'].min()

    df['distanceAcc'] = df['distance'].cumsum()
    totalDist = df['distance'].sum()

    st.write('Number of points        :', len(df))
    st.write('Total Ascend (metres)   :', int(totalAscend))
    st.write('Max height diff (metres):', int(heightDiff))
    st.write('Distance (metres)       :',int(totalDist))
    st.write('Time                    :', df.iloc[-1]['time'])


    fig = px.area(df[::10], x = 'distanceAcc', y = 'elevation',range_y=[df['elevation'].min()-10, df['elevation'].max() + 10])

    st.plotly_chart(fig)

    df['speedSmothed'] = df['speed'].rolling(window=31).mean()
    fig = px.area(df,x = 'distanceAcc', y = 'speedSmothed')
    st.plotly_chart(fig)

    fig = px.line_map(
        df[::5],
        lat="latitude",
        lon="longitude",
        height = 600,
        zoom = 13,
        #color = 'elevation'
    )

    # Set the background map style (e.g., "open-street-map", "carto-positron")
    fig.update_layout(map_style="open-street-map")
    #st.plotly_chart(fig)
    st.map(df[::3][['latitude', 'longitude']], size = 10)

