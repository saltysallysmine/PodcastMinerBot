import os
import pafy
from telegram.ext import Updater, MessageHandler, Filters
from pprint import pprint

# get bot token from environment variable
TOKEN = os.environ.get('TELEGRAM_PODCAST_MINER_BOT_TOKEN', None)


class Podcast:
    def __init__(self, url: str):
        self.url = url

        self.video_id = None
        self._set_video_id(url)

        self.author_name = None
        self.title = None
        self.duration = None

        self.audio_file_path = None

    def _set_video_id(self, url):
        # https://www.youtube.com/watch?v=Zf2jljuUpMQ
        self.video_id = url[-11:]

    def _set_duration(self, duration: str):
        qw = [int(el) for el in duration.split(':')]
        self.duration = 3600 * qw[0] + 60 * qw[1] + qw[0]

    def make(self):
        video = pafy.new(self.video_id)

        self.author_name = video.username
        self.title = video.title
        self._set_duration(video.duration)

        self.audio_file_path = \
            f'download_podcasts/{self.title} - {self.author_name}.mp3'

        stream = video.getbestaudio()
        filename = stream.download(filepath=self.audio_file_path)


def send_podcast(update, context):
    url = update.message.text

    podcast = Podcast(url)
    try:
        podcast.make()
    except Exception as e:
        print(e)

    audio_file_path = podcast.audio_file_path
    # author_name = podcast.author_name
    # this is crutch !!!!!!!!!!!!!!!!!!!!!!
    author_name = 'PodcastMinerBot'
    title = podcast.title
    duration = podcast.duration

    # print("author name:", author_name)

    with open(audio_file_path, 'rb') as audio_file:
        update.message.reply_audio(audio_file, performer=author_name,
                                   title=title, duration=duration)


def main():
    updater = Updater(TOKEN, use_context=True)

    dp = updater.dispatcher

    text_handler = MessageHandler(Filters.text, send_podcast)
    dp.add_handler(text_handler)

    # cycle of getting and processing messages
    updater.start_polling()

    # while not end
    updater.idle()


if __name__ == '__main__':
    main()
