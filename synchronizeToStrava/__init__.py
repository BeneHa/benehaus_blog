from datetime import datetime, timezone, timedelta
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
        raise Exception(f"{r.reason}, {r.text}")

def translate_sport(komoot_sport:str):
    # Translate sports category
    if komoot_sport in ["bike", "bike touring", "bicycle", "gravel", "mtb_easy", "racebike", "touringbicycle", "mtb"]:
        return "Ride"
    elif komoot_sport in ["hiking", "mountaineering", "hike"]:
        return "Hike"
    elif komoot_sport in ["skitour"]:
        return "AlpineSki"


def main(mytimer: func.TimerRequest) -> None:

    # blob client, use managed identity
    default_credential = DefaultAzureCredential()
    blob_client = BlobServiceClient(os.environ['storage_account_name'], credential=default_credential)
    container_client = blob_client.get_container_client(container="komootdata")

    # DEMO
    route = json.loads(container_client.download_blob("tours/1760939931.json").readall())

    # Read strava information from key-vault backed env secrets
    strava_access_token, strava_refresh_token = get_strava_token(os.environ["strava_userid"], os.environ["strava_client_secret"], os.environ["strava_refresh_token"])
    # Write the refresh token to the key vault so the next run of this function can use it
    secret_client = SecretClient(vault_url=os.environ["key_vault_url"], credential=default_credential)
    secret_client.set_secret("strava-refresh-token", strava_refresh_token)


    # Create a new GPX track
    gpx = gpxpy.gpx.GPX()
    gpx_track = gpxpy.gpx.GPXTrack()
    gpx.tracks.append(gpx_track)

    # Create a new segment in the GPX track
    gpx_segment = gpxpy.gpx.GPXTrackSegment()
    gpx_track.segments.append(gpx_segment)

    start_time = datetime.fromisoformat(route["date"])
    # Add points to the GPX segment
    for point in route["_embedded"]["coordinates"]["items"]:
        # Komoot data has time in miliseconds since start, gpx needs iso datetime per point
        point_time = start_time + timedelta(milliseconds = point["t"])
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
    check_request_exception(r, "Completed tour upload.")

    # Get activity id
    time.sleep(5) # Activity in strava needs some time to be ready
    r_id = requests.get(f"https://www.strava.com/api/v3/uploads/{strava_id_upload}", headers=headers)
    check_request_exception(r_id, "Activity ID fetched.")
    strava_id_activity = r_id.json()["activity_id"]


    # Update relevant details
    komoot_route_id = route["id"]
    params = {
        "type": translate_sport(route["sport"]),
        "description": f"Automatically synched from komoot, link: https://www.komoot.com/de-de/tour/{komoot_route_id}"
    }
    r_details = requests.put(f"https://www.strava.com/api/v3/activities/{strava_id_activity}", headers=headers, params=params)

    check_request_exception(r_details, "Completed tour details.")
