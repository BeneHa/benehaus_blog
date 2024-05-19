import datetime
import json
import os
import io 
import pandas as pd
from pandas.tseries.offsets import MonthBegin
import codecs

import folium
from folium.plugins import HeatMap

import azure.functions as func
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient, ContentSettings


def get_blob_client(container):
    # blob client, use managed identity
    default_credential = DefaultAzureCredential()
    client = BlobServiceClient(f"https://{os.environ['blob_storage_name']}.blob.core.windows.net/", credential=default_credential)
    return client.get_container_client(container=container)

def prepare_df(container_client):
    # get all tours and fetch details for each
    saved_tours = [n['name'] for n in container_client.list_blobs(name_starts_with="tours/")]
    data_list = []

    for t in saved_tours:
        tour_data = json.load(container_client.download_blob(blob=t))
        tour_data = {k:v for (k,v) in tour_data.items() if k in ["date", "name", "sport", "_embedded", "elevation_up", "duration", "distance"]}
        tour_data["coordinates"] = tour_data["_embedded"]["coordinates"]["items"]
        tour_data.pop("_embedded")
        if tour_data["duration"] > 1800:
            data_list.append(tour_data)
    return pd.DataFrame.from_records(data_list)

def heatmap_func(df):
    df2 = df.explode("coordinates")
    x = df2.coordinates.str
    df2["lat"] = df2.coordinates.str["lat"]
    df2["lon"] = df2.coordinates.str["lng"]

    df2.pop("coordinates")

    LAT_MIN = 47.7
    LAT_MAX = 48.55
    LON_MIN = 10.75
    LON_MAX = 12.25

    # sampling to reduce amount of points
    df_sampled = df2.iloc[::10]

    df3 = df_sampled.groupby(["lat", "lon"]).size().reset_index(name='counts')
    df_np = df3.to_numpy()

    hm = folium.Map(location=[(LAT_MIN + LAT_MAX) / 2, (LON_MIN + LON_MAX) / 2], 
                tiles='openstreetmap',
                zoom_start=10)
    HeatMap(df_np, min_opacity=0.4, blur = 3, radius = 3, gradient = {0.4: "blue", 0.7: "lime", 0.9: "red"}).add_to(folium.FeatureGroup(name='Heat Map').add_to(hm))
    folium.LayerControl().add_to(hm)

    return hm


def barplot_func(df):
    df_dist = df[df["date"].str.contains(r"2022|2023|2024|2025")]
    df_dist.pop("coordinates")
    df_dist["date"] = df_dist["date"].apply(pd.to_datetime)

    # fill empty months
    max_date = max(df_dist["date"])
    for year in range(2022, max_date.year):
        for month in ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"]:
            df_new = pd.DataFrame([[pd.to_datetime(f'{year}-{month}-01 10:00:00.0000000000', format='%Y-%m-%d %H:%M:%S.%f', utc=True), "0", 0, "0", "bike", 0]],
                                columns=["date", "name", "distance", "duration", "sport", "elevation_up"])
            df_dist = pd.concat([df_dist, df_new])

    df_dist['year_month'] = df_dist['date'].dt.normalize().map(MonthBegin().rollback)
    df_dist['year_month'] = df_dist["year_month"].astype(str).str.slice(0,7)

    df_dist["distance"] = df_dist["distance"] / 1000
    df_grouped = df_dist.groupby(["year_month"], dropna=False)[["distance", "elevation_up"]].sum().reset_index()
    df_grouped.distance = df_grouped.distance.round(0)
    df_grouped.elevation_up = df_grouped.elevation_up.round(0)

    js_string = f"""// automatically generated file, do not change here!
        var xValues = {df_grouped["year_month"].tolist()};
        var yValues = {df_grouped["distance"].tolist()};
        var altValues= {df_grouped["elevation_up"].tolist()};
        var barColorDist ="blue";
        var barColorAlt ="grey";

        new Chart("barplot", {{
        type: "bar",
        data: {{
            labels: xValues,
            datasets: [{{
                label: 'Distance',
                backgroundColor: barColorDist,
                data: yValues,
                yAxisID: 'y-axis-distance'
            }},
            {{
                label: 'Altitude',
                backgroundColor: barColorAlt,
                data: altValues.map(value => value / 10),
                yAxisID: 'y-axis-altitude'
            }}]
        }},
        options: {{
            legend: {{display: true}},
            title: {{
            display: false,
            }},
            tooltips: {{
                callbacks: {{
                    label: function(tooltipItem, data) {{
                        var datasetLabel = data.datasets[tooltipItem.datasetIndex].label || '';
                        var value = tooltipItem.yLabel;
                        if (tooltipItem.datasetIndex === 1) {{
                            value = value * 10; // Convert scaled value back to real value
                            return datasetLabel + ': ' + value + ' m';
                        }} else {{
                            return datasetLabel + ': ' + value + ' km';
                        }}
                    }}
                }}
            }},
            scales: {{
                yAxes: [{{
                    id: 'y-axis-distance',
                    type: 'linear',
                    position: 'left',
                    ticks: {{
                        beginAtZero: true,
                        callback: function(value, index, values) {{
                            return value + ' km';
                        }}
                    }},
                    scaleLabel: {{
                        display: true,
                        labelString: 'Distance (km)'
                    }}
                }}, {{
                    id: 'y-axis-altitude',
                    type: 'linear',
                    position: 'right',
                    ticks: {{
                        beginAtZero: true,
                        callback: function(value, index, values) {{
                            return value * 10 + ' m';
                        }}
                    }},
                    scaleLabel: {{
                        display: true,
                        labelString: 'Altitude (m)'
                    }}
                }}],
                xAxes: [{{
                    barPercentage: 1.0,
                categoryPercentage: 0.5
                }}]
            }}
        }} }});
    """
    return js_string


def main(mytimer: func.TimerRequest) -> None:
    utc_timestamp = datetime.datetime.utcnow().replace(
        tzinfo=datetime.timezone.utc).isoformat()
    print(utc_timestamp)

    # Preparation
    client = get_blob_client("komootdata")
    df = prepare_df(client)

    heatmap = heatmap_func(df)
    map_bytes_io = io.BytesIO()
    heatmap.save(map_bytes_io, close_file=False)

    container_client = get_blob_client(container="komootplots")
    container_client.upload_blob("bike_heatmap.html", map_bytes_io.getvalue(),
                                    overwrite=True, content_settings=ContentSettings(content_type="text/html"))

    # Distance bar diagram
    plt = barplot_func(df.copy())

    map_bytes_io = io.BytesIO()
    StreamWriter = codecs.getwriter('utf-8')
    wrapper_file = StreamWriter(map_bytes_io)
    print(plt, file=wrapper_file)    

    container_client = get_blob_client("$web")
    container_client.upload_blob("assets/js/barplot.js",  map_bytes_io.getvalue(),
                                   overwrite=True) 
