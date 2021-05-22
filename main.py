import os
import pafy
import logging
from telegram.ext import Updater, MessageHandler, Filters
from pprint import pprint

logging.basicConfig(
    filename='logs.log',
    format='%(asctime)s %(levelname)s %(name)s %(message)s',
    level=logging.INFO
)

# get bot token from environment variable
TOKEN = os.environ.get('TELEGRAM_PODCAST_MINER_BOT_TOKEN', None)
logging.info('get bot token from env')


class Podcast:
    def __init__(self, url: str):
        self.url = url
        self.video_id = None

        self.author_name = None
        self.title = None
        self.duration = None

        self.audio_file_path = None

    def _set_duration(self, duration: str):
        qw = [int(el) for el in duration.split(':')]
        self.duration = 3600 * qw[0] + 60 * qw[1] + qw[2]

    def make(self):
        video = pafy.new(self.url)

        self.author_name = video.author
        self.title = video.title
        self.video_id = video.videoid
        self._set_duration(video.duration)

        # self.audio_file_path will be like 'download_podcasts/video_id.mp3'
        self.audio_file_path = 'download_podcasts/'
        self.audio_file_path += self.video_id
        self.audio_file_path += '.mp3'

        # download podcast
        stream = video.getbestaudio()
        stream.download(filepath=self.audio_file_path)


# clean download_podcasts if it`s too big
def download_podcasts_cleaning():
    path_base = os.getcwd() + '/download_podcasts'
    files_sizes = [os.path.getsize(path_base + '/' + f) for f in os.listdir(path_base)]
    podcasts_size = sum(files_sizes)
    max_podcasts_size = 52428800  # 50MiB

    if podcasts_size > max_podcasts_size:
        path_base = 'download_podcasts/'

        for filename in os.listdir('download_podcasts'):
            os.remove(path_base + filename)

        logging.info(f'clean download_podcasts')


def send_podcast(update, context):
    url = update.message.text

    podcast = Podcast(url)
    try:
        podcast.make()
        logging.info(f'make podcast with id {podcast.video_id}')
    except Exception as e:
        update.message.reply_text(
            'Something go wrong. Maybe your link or video id is incorrect'
        )
        logging.error(f'can`t make podcast: {e}')
        return

    audio_file_path = podcast.audio_file_path
    author_name = podcast.author_name
    title = podcast.title
    duration = podcast.duration

    # print("author name:", author_name)

    with open(audio_file_path, 'rb') as audio_file:
        update.message.reply_audio(audio_file, performer=author_name,
                                   title=title, duration=duration)

    logging.info(f'send podcast with id {podcast.video_id}')

    download_podcasts_cleaning()


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
