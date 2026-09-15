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

    gpx.simplify(max_distance=2.0) 

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
    # clean data
    elevation_upper_limit = df['elevation'].mean() + 2 * df['elevation'].std()
    elevation_lower_limit = df['elevation'].mean() - 2 * df['elevation'].std()
    df = df[(df['elevation'] < elevation_upper_limit) & (df['elevation'] > elevation_lower_limit)]

    speed_upper_limit = df['speed'].mean() + 3 * df['speed'].std()
    speed_lower_limit = df['speed'].mean() - 3 * df['speed'].std()
    df = df[(df['speed'] < speed_upper_limit) & (df['speed'] > speed_lower_limit)]

    # Elevation
    df['elevationDiff'] = df['elevation'] - df['elevation'].shift(1)
    totalAscend  = df[df['elevationDiff'] > 0.00]['elevationDiff'].sum()

    heightDiff = df['elevation'].max() - df['elevation'].min()

    # Distance, recalculate after samples dropped
    df['lat_prev'] = df['latitude'].shift(1)
    df['long_prev'] = df['longitude'].shift(1)
    df['time_prev'] = df['time'].shift(1)
    df['time_sec'] = pd.to_timedelta(df['time']).dt.total_seconds()
    df['dist_2'] = df.apply(lambda row: hs.haversine((row['latitude'], row['longitude']),(row['lat_prev'], row['long_prev']),unit=Unit.METERS), axis=1)
    window_size = 21
    df['speed_2'] = 3.6 * df['dist_2'].rolling(window = window_size,center=True).sum() / (df['time_sec'].rolling(window = window_size,center=True).max() - df['time_sec'].rolling(window = window_size,center=True).min())

    df['distanceAcc'] = df['dist_2'].cumsum()
    totalDist = df['distance'].sum()

    st.write('Number of points        :', len(df))
    st.write('Total Ascend (metres)   :', int(totalAscend))
    st.write('Max height diff (metres):', int(heightDiff))
    st.write('Distance (metres)       :',int(totalDist))
    st.write('Time                    :', df.iloc[-1]['time'])


    fig = px.area(df[::5], x = 'distanceAcc', y = 'elevation',range_y=[df['elevation'].min()-10, df['elevation'].max() + 10], line_shape='spline')

    st.plotly_chart(fig)

    
    fig = px.area(df[::5],x = 'distanceAcc', y = 'speed_2', line_shape='spline')
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
    st.map(df[['latitude', 'longitude']], size = 10)

