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
    client = BlobServiceClient(f"https://{os.environ['AzureWebJobsStorage__accountName']}.blob.core.windows.net/", credential=default_credential)
    return client.get_container_client(container=container)

def prepare_df(container_client):
    # get all tours and fetch details for each
    saved_tours = [n['name'] for n in container_client.list_blobs(name_starts_with="tours/")]
    data_list = []

    for t in saved_tours:
        tour_data = json.load(container_client.download_blob(blob=t))
        tour_data = {k:v for (k,v) in tour_data.items() if k in ["date", "name", "sport", "_embedded", "elevation_up", "duration", "distance"]}

        if tour_data["sport"] in ["bike", "bike touring", "bicycle", "gravel", "mtb_easy", "racebike", "touringbicycle", "mtb"]:
            tour_data["sport"] = "biking"
        elif tour_data["sport"] in ["hiking", "mountaineering", "hike"]:
            tour_data["sport"] = "hiking"
        elif tour_data["sport"] in ["skitour"]:
            tour_data["sport"] = "skitour"
        else:
            tour_data["sport"] = "other"
        tour_data["coordinates"] = tour_data["_embedded"]["coordinates"]["items"]
        tour_data.pop("_embedded")
        if tour_data["duration"] > 1800:
            data_list.append(tour_data)
    return pd.DataFrame.from_records(data_list)

def heatmap_func(df):
    df2 = df.explode("coordinates")
    df2["lat"] = df2.coordinates.str["lat"]
    df2["lon"] = df2.coordinates.str["lng"]

    df2.pop("coordinates")

    # sampling to reduce amount of points
    df_sampled = df2.iloc[::15]

    sport_colors = {
        "biking": "rgba(0, 0, 255, 0.4)",
        "hiking": "rgba(255, 0, 0, 0.8)",
        "skitour": "rgba(0, 255, 0, 0.8)",
        "other": "rgba(255, 165, 0, 0.8)"
    }

    hm = folium.Map(location=[44.81, 20.39],
                    tiles='openstreetmap',
                    zoom_start=10)

    # Group by date and sport
    grouped = df_sampled.groupby(['date', 'sport'])
    sport_groups = {sport: folium.FeatureGroup(name=sport, show=True) for sport in sport_colors.keys()}

    for (date, sport), group in grouped:
        coordinates = list(zip(group['lat'], group['lon']))
        if len(coordinates) > 1:
            folium.PolyLine(locations=coordinates, color=sport_colors.get(sport, 'black'), weight=2.5, opacity=1).add_to(sport_groups[sport])

    for sport, group in sport_groups.items():
        group.add_to(hm)

    folium.LayerControl().add_to(hm)

    return hm



def barplot_func(df):
        # Filter and prepare distances for recent years
        df_dist = df[df["date"].str.contains(r"2022|2023|2024|2025|2026")].copy()
        if "coordinates" in df_dist.columns:
                df_dist.pop("coordinates")
        # robustly parse dates, coercing invalid values to NaT
        df_dist["date"] = pd.to_datetime(df_dist["date"], errors='coerce')

        # ensure at least one row to avoid errors
        if df_dist.empty:
                df_grouped = pd.DataFrame({"year_month": [], "distance": [], "elevation_up": []})
        else:
                # fill empty months up to the last available year
                max_date = max(df_dist["date"]) if not df_dist.empty else pd.to_datetime("2022-01-01")
                rows = []
                for year in range(2022, max_date.year + 1):
                        for month in range(1, 13):
                                rows.append(pd.Timestamp(year=year, month=month, day=1, hour=10))
                filler = pd.DataFrame({"date": rows, "name": None, "distance": 0, "duration": 0, "sport": "biking", "elevation_up": 0})
                df_dist = pd.concat([df_dist, filler], ignore_index=True)

                # ensure the combined column is datetimelike and drop any rows where parsing failed
                df_dist['date'] = pd.to_datetime(df_dist['date'], errors='coerce')
                df_dist = df_dist.dropna(subset=['date'])

                df_dist['year_month'] = df_dist['date'].dt.to_period('M').astype(str)
                df_dist = df_dist[df_dist['sport'] == 'biking']
                df_dist["distance"] = df_dist["distance"] / 1000
                df_grouped = df_dist.groupby(["year_month"], dropna=False)[["distance", "elevation_up"]].sum().reset_index()
                df_grouped.distance = df_grouped.distance.round(0)
                df_grouped.elevation_up = df_grouped.elevation_up.round(0)

        # Generate a standalone HTML page with Chart.js
        x_vals = json.dumps(df_grouped["year_month"].tolist())
        y_vals = json.dumps(df_grouped["distance"].tolist())

        html = """<!doctype html>
<html lang=\"en\"> 
<head>
    <meta charset=\"utf-8\"> 
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\"> 
    <title>Bike Distance Barplot</title>
    <script src=\"https://cdn.jsdelivr.net/npm/chart.js\"></script>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 10px; background:#fff }}
        .container {{ max-width: 1000px; margin: auto }}
        canvas {{ width:100% !important; height:400px !important }}
    </style>
</head>
<body>
    <div class=\"container\">
        <canvas id=\"barplot\"></canvas>
    </div>
    <script>
        var xValues = {x_vals};
        var yValues = {y_vals};

        new Chart(document.getElementById('barplot').getContext('2d'), {
            type: 'bar',
            data: {
                labels: xValues,
                datasets: [
                    {
                        label: 'Distance (km)',
                        backgroundColor: 'rgba(54, 162, 235, 0.8)',
                        data: yValues,
                        yAxisID: 'y-axis-distance'
                    }
                ]
            },
            options: {
                responsive: true,
                scales: {
                    yAxes: [
                        {
                            id: 'y-axis-distance',
                            type: 'linear',
                            position: 'left',
                            ticks: { beginAtZero: true }
                        }
                    ]
                },
                tooltips: {
                    callbacks: {
                        label: function(tooltipItem, data) {
                            var label = data.datasets[tooltipItem.datasetIndex].label || '';
                            var value = tooltipItem.yLabel;
                            return label + ': ' + value + ' km';
                        }
                    }
                }
            }
        });
    </script>
</body>
</html>
"""
        # replace only the JSON placeholders to avoid f-string brace parsing issues
        html = html.replace('{x_vals}', x_vals).replace('{y_vals}', y_vals)
        return html


def main(myblob: func.InputStream) -> None:
    utc_timestamp = datetime.datetime.now(datetime.UTC).replace(
        tzinfo=datetime.timezone.utc).isoformat()

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
    barplot_html = barplot_func(df.copy())

    map_bytes_io = io.BytesIO()
    StreamWriter = codecs.getwriter('utf-8')
    wrapper_file = StreamWriter(map_bytes_io)
    print(barplot_html, file=wrapper_file)

    container_client = get_blob_client(container="komootplots")
    container_client.upload_blob("bike_barplot.html", map_bytes_io.getvalue(),
                                   overwrite=True, content_settings=ContentSettings(content_type="text/html"))
