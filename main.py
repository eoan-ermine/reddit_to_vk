import vk
import praw
import configparser
import requests
import schedule
import time
import io
import shutil

IMAGE_FORMATS = [".png", ".jpg", ".jpeg"]

def job():
    config = configparser.ConfigParser()
    config.read('config.ini')

    session = vk.Session(access_token=config.get("vk", "access_token"))
    api = vk.API(session, v='5.131')

    reddit = praw.Reddit(
        client_id=config.get("reddit", "client_id"),
        client_secret=config.get("reddit", "client_secret"),
        user_agent="reposter by u/eoanermine_",
    )
    subreddit = reddit.subreddit(config.get("reddit", "subreddit_name"))
    for submission in subreddit.new():
        url = submission.url
        description = submission.title
        permalink = submission.permalink

        print(f"URL: {url}\tDescription: {description}\tPermalink: {permalink}")

        if any([url.endswith(item) for item in IMAGE_FORMATS]):
            upload_url = api.photos.getWallUploadServer(
                group_id = config.get("vk", "group_id")
            )["upload_url"]

            response = requests.get(url, stream=True)
            with open('img.png', 'wb') as out_file:
                shutil.copyfileobj(response.raw, out_file)
            del response

            resp = requests.post(upload_url, files={
                "photo": open("img.png", "rb")
            }).json()
            
            photo_obj = api.photos.saveWallPhoto(
                group_id = config.get("vk", "group_id"),
                photo = resp["photo"],
                server = resp["server"],
                hash = resp["hash"]
            )[0]

            owner_id = photo_obj["owner_id"]
            photo_id = photo_obj["id"]
            photo_id = f"photo{owner_id}_{photo_id}"

            print(api.wall.post(
                owner_id="-" + config.get("vk", "group_id"),
                from_group=1,

                message=description,
                attachments = photo_id,
                
                copyright=f"http://reddit.com{permalink}",
            ))


job()