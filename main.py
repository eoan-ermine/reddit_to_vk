import vk
import praw
import configparser
import requests
import time
import io
import shutil
import pickle

IMAGE_FORMATS = [".png", ".jpg", ".jpeg"]


class VisitedStorage:
    def __init__(self, database_path: str = "database.pickle"):
        self.database_path = database_path
        self.visited = {}

    def contains(self, value):
        return value in self.visited

    def add(self, value):
        self.visited[value] = True

    def load(self):
        with open(self.database_path, "rb") as file:
            self.visited = pickle.load(file)

    def dump(self):
        with open(self.database_path, "wb") as file:
            pickle.dump(self.visited, file)

    def __enter__(self):
        try:
            self.load()
        except FileNotFoundException:
            self.dump()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.dump()
        if exc_val:
            raise


class RedditToVK:
    def __init__(self, config_path: str = "config.ini"):
        self.config_path = config_path

        self.read_config()
        self.setup_api()

    def read_config(self):
        config = configparser.ConfigParser()
        config.read(self.config_path)

        self.reddit = {}
        self.vk = {}

        self.reddit["client_id"] = config.get("reddit", "client_id")
        self.reddit["client_secret"] = config.get("reddit", "client_secret")
        self.reddit["subreddit_name"] = config.get("reddit", "subreddit_name")

        self.vk["access_token"] = config.get("vk", "access_token")
        self.vk["group_id"] = config.get("vk", "group_id")

        self.delay = config.get("global", "delay")

    def setup_reddit(self):
        self.reddit = praw.Reddit(
            client_id=self.reddit["client_id"],
            client_secret=self.reddit["client_secret"],
            user_agent="RedditToVK by u/eoanermine_",
        )

    def setup_vk(self):
        session = vk.Session(access_token=self.vk["access_token"])
        self.vk = vk.API(session, v="5.131")

    def setup_api(self):
        self.setup_reddit()
        self.setup_vk()

    def run(self, dry=False):
        subreddit = reddit.subreddit(self.reddit["subreddit_name"])
        for submission in subreddit.hot(limit=15):
            url = submission.url
            description = submission.title
            permalink = submission.permalink

            id = submission.name
            with VisitedStorage() as storage:
                if storage.contains(id):
                    continue
                storage.add(id)

            if dry:
                continue

            if any([url.endswith(item) for item in IMAGE_FORMATS]):
                upload_url = api.photos.getWallUploadServer(
                    group_id=self.vk["group_id"]
                )["upload_url"]

                response = requests.get(url, stream=True)
                with open("last_image.png", "wb") as out_file:
                    shutil.copyfileobj(response.raw, out_file)
                del response

                resp = requests.post(
                    upload_url, files={"photo": open("last_image.png", "rb")}
                ).json()

                photo_obj = api.photos.saveWallPhoto(
                    group_id=self.vk["group_id"],
                    photo=resp["photo"],
                    server=resp["server"],
                    hash=resp["hash"],
                )[0]

                owner_id = photo_obj["owner_id"]
                photo_id = photo_obj["id"]
                photo_id = f"photo{owner_id}_{photo_id}"

                api.wall.post(
                    owner_id="-" + self.vk["group_id"],
                    from_group=1,
                    message=description,
                    attachments=photo_id,
                    copyright=f"http://reddit.com{permalink}",
                )

    def serve(self):
        while True:
            self.run()
            time.sleep(self.delay)
