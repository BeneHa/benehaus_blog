import datetime
import json
import os
from io import BytesIO
import pandas as pd

import folium
from folium.plugins import HeatMap
import matplotlib.pyplot as plt

import azure.functions as func
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient, ContentSettings


def get_blob_client(containername):
    # blob client, use managed identity
    default_credential = DefaultAzureCredential()
    client = BlobServiceClient(f"https://{os.environ['blob_storage_name']}.blob.core.windows.net/", credential=default_credential)
    return client.get_container_client(container=containername)

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
    df2["lat"] = df.coordinates.str["lat"]
    df2["lon"] = df.coordinates.str["lng"]
    
    df2.pop("coordinates")

    LAT_MIN = 47.7
    LAT_MAX = 48.55
    LON_MIN = 10.75
    LON_MAX = 12.25

    df3 = df2.groupby(["lat", "lon"]).size().reset_index(name='counts')
    df_np = df3.to_numpy()

    hm = folium.Map(location=[(LAT_MIN + LAT_MAX) / 2, (LON_MIN + LON_MAX) / 2], 
                tiles='stamentoner',
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
            df_new = pd.DataFrame([[pd.to_datetime(f'{year}-{month}-01 10:00:00.0000000000', format='%Y-%m-%d %H:%M:%S.%f'), "0", 0, "0", "bike", 0]],
                                columns=["date", "name", "distance", "duration", "sport", "elevation_up"])
            df_dist = pd.concat([df_dist, df_new])

    df_dist['year_month'] = df_dist['date'] + pd.offsets.MonthBegin(-1)
    df_dist['year_month'] = df_dist["year_month"].astype(str).str.slice(0,7)

    df_dist["distance"] = df_dist["distance"] / 1000
    df_grouped = df_dist.groupby(["year_month"])["distance"].sum().reset_index()

    fix, ax = plt.subplots(figsize=(10,6))
    ax.bar(df_grouped["year_month"], df_grouped["distance"])
    return fix, ax

def main(mytimer: func.TimerRequest) -> None:
    utc_timestamp = datetime.datetime.utcnow().replace(
        tzinfo=datetime.timezone.utc).isoformat()
    print(utc_timestamp)

    # Preparation
    client = get_blob_client("komootdata")
    df = prepare_df(client)

    heatmap = heatmap_func(df)
    map_bytes_io = BytesIO()
    heatmap.save(map_bytes_io, close_file=False)

    container_client = get_blob_client(container="komootplots")
    container_client.upload_blob("bike_heatmap.html", map_bytes_io.getvalue(),
                                    overwrite=True, content_settings=ContentSettings(content_type="text/html"))


    map_bytes_io = BytesIO()
    # Distance bar diagram
    fix, ax = barplot_func(df.copy())
    plt.setp(ax.get_xticklabels(), rotation=270, ha='right')

    plt.savefig(map_bytes_io)
    container_client = get_blob_client("komootplots")
    container_client.upload_blob("bike_barplot.png", map_bytes_io.getvalue(),
                                   overwrite=True) 