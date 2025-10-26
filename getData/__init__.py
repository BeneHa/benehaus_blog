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


def main(mytimer: func.TimerRequest) -> None:
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
                     "tour_recorded" in v and
                     ("jogging" not in v)}
    for t in missing_tours:
        tour_details = api.fetch_tour(str(t))

        container_client.upload_blob(data=json.dumps(tour_details), name=f"tours/{t}.json")
