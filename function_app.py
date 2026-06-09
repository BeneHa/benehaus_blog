import datetime
import logging
import json
import os
import io
import gpxpy
import time
import requests


import azure.functions as func
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
from azure.keyvault.secrets import SecretClient



def get_strava_token(client_id:str, client_secret:str, refresh_token:str):
    # Get Strava oauth token. First we need the code from the first redirect of the auth url, then we can request the oauth access token
    params = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token
    }
    r = requests.post("https://www.strava.com/api/v3/oauth/token", params=params)
    return r.json()["access_token"], r.json()["refresh_token"]

def check_request_exception(r, success_log:str):
    if str(r.status_code)[0] == "2":
        logging.info(success_log)
    else:
        raise Exception(f"{r.reason}, {r.text}, {r.json()}")

def translate_sport(komoot_sport:str):
    # Translate sports category
    if komoot_sport in ["bike", "bike touring", "bicycle", "gravel", "mtb_easy", "racebike", "touringbicycle", "mtb"]:
        return "Ride"
    elif komoot_sport in ["hiking", "mountaineering", "hike"]:
        return "Hike"
    elif komoot_sport in ["skitour"]:
        return "AlpineSki"
    elif komoot_sport in ["jogging"]:
        return "Run"
    else:
        return "Run"

app = func.FunctionApp()

@app.blob_trigger(arg_name="myblob", source="EventGrid", path="komootdata/tours/{name}",connection="blobtriggerconnection")
def main_sync_data(myblob: func.InputStream) -> None:
    logging.info(f"Running for new blob {myblob}")
    # blob client, use managed identity
    default_credential = DefaultAzureCredential()
    blob_client = BlobServiceClient(os.environ['storage_account_name'], credential=default_credential)
    container_client = blob_client.get_container_client(container="komootdata")

    strava_access_token, strava_refresh_token = get_strava_token(os.environ["strava_userid"], os.environ["strava_client_secret"], os.environ["strava_refresh_token"])
    # Read strava information from key-vault backed env secrets
    # Write the refresh token to the key vault so the next run of this function can use it
    secret_client = SecretClient(vault_url=os.environ["key_vault_url"], credential=default_credential)
    secret_client.set_secret("strava-refresh-token", strava_refresh_token)


    file_path = myblob.name.replace("komootdata/", "")
    route = json.loads(container_client.download_blob(file_path).readall())

    # Create a new GPX track
    gpx = gpxpy.gpx.GPX()
    gpx_track = gpxpy.gpx.GPXTrack()
    gpx.tracks.append(gpx_track)

    # Create a new segment in the GPX track
    gpx_segment = gpxpy.gpx.GPXTrackSegment()
    gpx_track.segments.append(gpx_segment)

    start_time = datetime.datetime.fromisoformat(route["date"])
    # Add points to the GPX segment
    for point in route["_embedded"]["coordinates"]["items"]:
        # Komoot data has time in miliseconds since start, gpx needs iso datetime per point
        point_time = start_time + datetime.timedelta(milliseconds = point["t"])
        gpx_segment.points.append(
            gpxpy.gpx.GPXTrackPoint(point["lat"], point["lng"], elevation=point["alt"], time=point_time)
        )

    # write to io as Azure functions do not have writable file system
    gpx_data = io.StringIO(gpx.to_xml())



    headers = {
        "Authorization": f"Bearer {strava_access_token}"
    }

    # Create the activity in strava
    files = {
        "file": ("route.gpx", gpx_data, "application/gpx+xml")
    }
    params = {
        "data_type": "gpx",
        "name": route["name"] if not(route["name"].startswith("Road Ride to")) else "Radtour",
        "commute": "false",
    }
    r = requests.post(f"https://www.strava.com/api/v3/uploads", headers=headers, params=params, files=files)
    strava_id_upload = r.json()["id"]
    check_request_exception(r, f"Completed tour upload for upload ID {strava_id_upload}.")
    
    # Get activity id
    time.sleep(10) # Activity in strava needs some time to be ready
    r_id = requests.get(f"https://www.strava.com/api/v3/uploads/{strava_id_upload}", headers=headers)
    check_request_exception(r_id, "Activity ID fetched.")
    strava_id_activity = r_id.json()["activity_id"]
    response_error = r_id.json()["error"]

    # Update relevant details
    komoot_route_id = route["id"]
    params = {
        "type": translate_sport(route["sport"]),
        "description": f"Automatically synched from komoot"
    }
    r_details = requests.put(f"https://www.strava.com/api/v3/activities/{strava_id_activity}", headers=headers, params=params)

    check_request_exception(r_details, "Completed tour details for activity ID {strava_id_activity}.")




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
        html, body {{ height:100%; margin:0; padding:0; background:#fff; font-family: Arial, sans-serif }}
        .container {{ max-width: 1000px; margin: 10px auto; height: calc(100vh - 40px); box-sizing: border-box }}
        canvas {{ width:100% !important; height: calc(100vh - 120px) !important }}
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


@app.blob_trigger(arg_name="myblob", source="EventGrid", path="komootdata/tours/{name}",connection="blobtriggerconnection")
def main_process_data(myblob: func.InputStream) -> None:
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


import datetime
import logging
import requests
import base64
import json
import os

import azure.functions as func
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient

class BasicAuthToken(requests.auth.AuthBase):
    def __init__(self, key, value):
        self.key = key
        self.value = value

    def __call__(self, r):
        authstr = "Basic " + base64.b64encode(
            bytes(self.key + ":" + self.value, "utf-8")
        ).decode("utf-8")
        r.headers["Authorization"] = authstr
        return r

class KomootApi:
    def __init__(self):
        self.user_id = ""
        self.token = ""

    def __build_header(self):
        if self.user_id != "" and self.token != "":
            return {
                "Authorization": "Basic {0}".format(
                    base64.b64encode(
                        bytes(self.user_id + ":" + self.token, "utf-8")
                    ).decode()
                )
            }
        return {}

    @staticmethod
    def __send_request(url, auth, critical=True):
        r = requests.get(url, auth=auth)
        if r.status_code != 200:
            print("Error " + str(r.status_code) + ": " + str(r.json()))
            if critical:
                exit(1)
        return r

    def login(self, email, password):
        logging.info("Logging in to komoot")

        try:
            logging.info(f"user: {email}, pw: {password}")
            r = self.__send_request(
                "https://api.komoot.de/v006/account/email/" + email + "/",
                BasicAuthToken(email, password),
            )
        except Exception as e:
            logging.error(str(e))

        self.user_id = r.json()["username"]
        self.token = r.json()["password"]

        print("Logged in as '" + r.json()["user"]["displayname"] + "'")

    def fetch_tours(self, tourType="all", silent=False):
        if not silent:
            print("Fetching tours of user '" + self.user_id + "'...")

        r = self.__send_request(
            "https://api.komoot.de/v007/users/"
            + self.user_id
            + "/tours/?limit=3000&format=coordinate_array",
            BasicAuthToken(self.user_id, self.token),
        )

        results = {}
        tours = r.json()["_embedded"]["tours"]
        print(os.getcwd())
        for tour in tours:
            if tourType != "all" and tourType != tour["type"]:
                continue
            results[tour["id"]] = (
                tour["name"]
                + " ("
                + tour["sport"]
                + "; "
                + str(int(tour["distance"]) / 1000.0)
                + "km; "
                + tour["type"]
                + ")"
            )

        return results

    def fetch_tour(self, tour_id):
        print("Fetching tour '" + tour_id + "'...")

        r = self.__send_request(
            "https://api.komoot.de/v007/tours/"
            + tour_id
            + "?_embedded=coordinates,way_types,"
            "surfaces,directions,participants,"
            "timeline&directions=v2&fields"
            "=timeline&format=coordinate_array"
            "&timeline_highlights_fields=tips,"
            "recommenders",
            BasicAuthToken(self.user_id, self.token),
        )

        return r.json()

    def fetch_highlight_tips(self, highlight_id):
        print("Fetching highlight '" + highlight_id + "'...")

        r = self.__send_request(
            "https://api.komoot.de/v007/highlights/" + highlight_id + "/tips/",
            BasicAuthToken(self.user_id, self.token),
            critical=False,
        )

        return r.json()

@app.timer_trigger(
    schedule="0 0 0,15,18,21 * * *",
    arg_name="mytimer",
    run_on_startup=False
)
def main_get_data(mytimer: func.TimerRequest) -> None:
    utc_timestamp = datetime.datetime.utcnow().replace(
        tzinfo=datetime.timezone.utc).isoformat()
    logging.info(f"Started function at {utc_timestamp}.")

    # blob client, use managed identity
    default_credential = DefaultAzureCredential()
    client = BlobServiceClient(os.environ['storage_account_name'], credential=default_credential)
    container_client = client.get_container_client(container="komootdata")

    # set up api and login
    api = KomootApi()
    api.login(os.environ["komoot_username"], os.environ["komoot_password"])

    # get all tours and fetch details for each
    saved_tours = [n['name'].split('/')[1].replace('.json', '') for n in container_client.list_blobs(name_starts_with="tours/")]
    tours = api.fetch_tours()
    missing_tours = {k:v for (k,v) in tours.items() if
                     str(k) not in saved_tours and
                     "tour_recorded" in v}
    for t in missing_tours:
        tour_details = api.fetch_tour(str(t))

        container_client.upload_blob(data=json.dumps(tour_details), name=f"tours/{t}.json")
