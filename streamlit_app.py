import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static

# Assume data is already loaded into the system
@st.cache
def load_data():
    data = pd.read_csv('main_data.csv')
    data['datetime'] = pd.to_datetime(data['datetime'])
    data.set_index('datetime', inplace=True)
    return data

data = load_data()

# Sidebar
st.sidebar.header("Filter Options")
pollutant = st.sidebar.selectbox("Select Pollutant", ['PM2.5', 'PM10', 'SO2', 'NO2', 'CO', 'O3'])
start_date, end_date = st.sidebar.date_input(
    "Select Date Range", 
    [data.index.min().date(), data.index.max().date()]
)

# Filter data by date range
filtered_data = data[(data.index >= pd.to_datetime(start_date)) & (data.index <= pd.to_datetime(end_date))]

# Title
st.title("Air Quality Monitoring Dashboard 🌍")

# 1. Business Question 1 - Annual Trend (2013-2017)
st.subheader(f"1. {pollutant} - Trend Analysis (2013-2017) by Station")
st.line_chart(filtered_data.resample('M').mean()[pollutant])

# 2. Business Question 2 - Seasonal Patterns
st.subheader(f"2. {pollutant} - Seasonal Patterns (Monthly Averages)")
seasonal_data = filtered_data.groupby(filtered_data.index.month)[pollutant].mean()
st.line_chart(seasonal_data)

# 3. Business Question 3 - Urban vs Suburban Comparison
st.subheader(f"3. {pollutant} - Urban vs Suburban Comparison")
urban_data = filtered_data[filtered_data['area_type'] == 'Urban'].resample('M').mean()[pollutant]
suburban_data = filtered_data[filtered_data['area_type'] == 'Suburban'].resample('M').mean()[pollutant]

comparison_df = pd.DataFrame({
    'Urban': urban_data,
    'Suburban': suburban_data
})
st.line_chart(comparison_df)

# Map Visualization
st.subheader(f"{pollutant} Distribution Across Stations")

def create_map(data, pollutant):
    station_avg = data.groupby('station')[pollutant].mean().reset_index()
    station_locations = {
        'Aotizhongxin': [39.982, 116.397],
        'Changping': [40.220, 116.234],
        'Dingling': [40.290, 116.220],
        'Dongsi': [39.929, 116.417],
        'Guanyuan': [39.929, 116.339],
        'Gucheng': [39.911, 116.163],
        'Huairou': [40.374, 116.623],
        'Nongzhanguan': [39.933, 116.472],
        'Shunyi': [40.126, 116.655],
        'Tiantan': [39.886, 116.407],
        'Wanliu': [39.967, 116.307],
        'Wanshouxigong': [39.883, 116.358]
    }

    m = folium.Map(location=[39.9042, 116.4074], zoom_start=10)

    for _, row in station_avg.iterrows():
        station = row['station']
        if station in station_locations:
            folium.CircleMarker(
                location=station_locations[station],
                radius=10,
                popup=f"{station} - {pollutant}: {row[pollutant]:.2f} µg/m³",
                color='crimson' if row[pollutant] > 100 else 'orange' if row[pollutant] > 50 else 'green',
                fill=True,
                fill_opacity=0.7
            ).add_to(m)
    
    return m

folium_map = create_map(filtered_data, pollutant)
folium_static(folium_map)

# Display Raw Data
st.subheader("Raw Data")
st.dataframe(filtered_data.head(100))
