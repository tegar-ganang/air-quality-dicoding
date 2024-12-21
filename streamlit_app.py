import streamlit as st
import pandas as pd
import folium
import matplotlib.pyplot as plt
from streamlit_folium import folium_static
from dataprep.eda import create_report
from streamlit.components.v1 import html

# Load Data
@st.cache
def load_data():
    data = pd.read_csv('main_data.csv')
    data['datetime'] = pd.to_datetime(data['datetime'])
    data.set_index('datetime', inplace=True)
    return data

data = load_data()

# Station locations
station_info = {
    'Aotizhongxin': {'location': [39.982, 116.397], 'type': 'Urban'},
    'Changping': {'location': [40.220, 116.234], 'type': 'Suburban'},
    'Dingling': {'location': [40.290, 116.220], 'type': 'Suburban'},
    'Dongsi': {'location': [39.929, 116.417], 'type': 'Urban'},
    'Guanyuan': {'location': [39.929, 116.339], 'type': 'Urban'},
    'Gucheng': {'location': [39.911, 116.163], 'type': 'Urban'},
    'Huairou': {'location': [40.374, 116.623], 'type': 'Suburban'},
    'Nongzhanguan': {'location': [39.933, 116.472], 'type': 'Urban'},
    'Shunyi': {'location': [40.126, 116.655], 'type': 'Suburban'},
    'Tiantan': {'location': [39.886, 116.407], 'type': 'Urban'},
    'Wanliu': {'location': [39.967, 116.307], 'type': 'Urban'},
    'Wanshouxigong': {'location': [39.883, 116.358], 'type': 'Urban'}
}
# Sidebar
st.sidebar.header("Filter Options")
pollutant = st.sidebar.selectbox("Select Pollutant", ['NO2', 'PM10', 'SO2', 'CO', 'O3', 'PM2.5'])
start_date, end_date = st.sidebar.date_input(
    "Select Date Range", 
    [data.index.min().date(), data.index.max().date()]
)
station_selected = st.sidebar.multiselect(
    "Select Station (Select 'All' for all stations)", 
    ['All'] + list(station_info.keys()), 
    default='All'
)

pollutant_thresholds = {
    'PM2.5': {'good': 50, 'bad': 100},
    'PM10': {'good': 75, 'bad': 150},
    'SO2': {'good': 20, 'bad': 80},
    'NO2': {'good': 40, 'bad': 100},
    'CO': {'good': 4, 'bad': 10},
    'O3': {'good': 60, 'bad': 120}
}

good_threshold = pollutant_thresholds[pollutant]['good']
bad_threshold = pollutant_thresholds[pollutant]['bad']

# Filter data by date range
filtered_data = data[(data.index >= pd.to_datetime(start_date)) & (data.index <= pd.to_datetime(end_date))]

# Filter data by selected stations
if 'All' not in station_selected:
    filtered_data = filtered_data[filtered_data['station'].isin(station_selected)]

avg_pollutant = filtered_data.groupby('station')[pollutant].mean()

good_air = avg_pollutant[avg_pollutant < good_threshold].sort_values()
bad_air = avg_pollutant[avg_pollutant > bad_threshold].sort_values(ascending=False)

# Title
st.title("Air Quality Monitoring Dashboard 🌍")

# Display Metrics for Good Air Quality Stations
st.subheader(f"🏞️ Good Air Quality Stations ({pollutant} < {good_threshold} µg/m³)")
for station, value in good_air.items():
    station_type = station_info[station]['type']
    st.metric(label=f"{station} ({station_type})", value=f"{value:.2f} µg/m³", delta="Good", delta_color="normal")

# Display Metrics for Bad Air Quality Stations
st.subheader(f"🏙️ Bad Air Quality Stations ({pollutant} > {bad_threshold} µg/m³)")
for station, value in bad_air.items():
    station_type = station_info[station]['type']
    st.metric(label=f"{station} ({station_type})", value=f"{value:.2f} µg/m³", delta="Bad", delta_color="inverse")

# 1. Business Question 1 - Annual Trend (2013-2017) by Station
st.subheader(f"1. {pollutant} - Annual Trend (2013-2017) by Station")
annual_trend = filtered_data.resample('M').mean()
annual_trend_by_station = filtered_data.groupby([filtered_data.index.year, 'station'])[pollutant].mean().unstack()

plt.figure(figsize=(14, 7))
for station in annual_trend_by_station.columns:
    plt.plot(annual_trend_by_station.index, annual_trend_by_station[station], label=f"{station} ({pollutant})")

plt.title(f'Annual Trend of {pollutant} (2013-2017) by Station')
plt.xlabel('Year')
plt.ylabel(f'{pollutant} (µg/m³)')
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
plt.grid(True)
st.pyplot(plt)

# 2. Business Question 2 - Seasonal Patterns by Station
st.subheader(f"2. {pollutant} - Seasonal Patterns by Station")
seasonal_data = filtered_data.groupby([filtered_data.index.month, 'station'])[pollutant].mean().unstack()

plt.figure(figsize=(14, 7))
for station in seasonal_data.columns:
    plt.plot(seasonal_data.index, seasonal_data[station], label=f"{station} ({pollutant})")

plt.title(f'Seasonal Variation of {pollutant} by Station')
plt.xlabel('Month')
plt.ylabel(f'Average {pollutant} (µg/m³)')
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
plt.grid(True)
st.pyplot(plt)


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
    m = folium.Map(location=[39.9042, 116.4074], zoom_start=10)

    for _, row in station_avg.iterrows():
        station = row['station']
        if station in station_info:
            folium.CircleMarker(
                location=station_info[station],
                radius=10,
                popup=f"{station} - {pollutant}: {row[pollutant]:.2f} µg/m³",
                color='crimson' if row[pollutant] > 100 else 'orange' if row[pollutant] > 50 else 'green',
                fill=True,
                fill_opacity=0.7
            ).add_to(m)
    
    return m

folium_map = create_map(filtered_data, pollutant)
folium_static(folium_map)

# EDA Report Section
st.subheader("Exploratory Data Analysis (EDA) Report")

if st.button("Generate EDA Report"):
    report = create_report(filtered_data)
    report.save("dataprep_report.html")

    with open("dataprep_report.html", "r", encoding="utf-8") as f:
        html_content = f.read()
        html(html_content, height=1000, scrolling=True)
