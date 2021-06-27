import os
from pytube import YouTube, Stream
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


class Podcast(YouTube):
    def __init__(self, url):
        super().__init__(url)

        self.audio_file_path = None

    def get_best_audio(self) -> Stream:
        def comparator(y):
            return y.type == 'audio' and y.mime_type == 'audio/mp4'

        audio_streams_list = list(
            filter(comparator, self.streams)
        )
        return max(audio_streams_list, key=lambda z: int(z.abr[:-4]))

    def download(self):
        audio_stream = self.get_best_audio()
        audio_stream.download(output_path='download_podcasts', filename=self.video_id)
        self.audio_file_path = f'download_podcasts/{self.video_id}.mp4'


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

    if url.lower() == 'пойдём копать картошку' or \
            url.lower() == 'пойдем копать картошку':
        update.message.reply_text('а погнали!')
        logging.info('пошли копать картошку')
        return

    try:
        podcast = Podcast(url)
        podcast.download()
        logging.info(f'make podcast with id {podcast.video_id}')
    except Exception as e:
        update.message.reply_text(
            'Something go wrong. Maybe your link is incorrect.'
        )
        logging.error(f'can`t make podcast: {e}')
        return

    audio_file_path = podcast.audio_file_path
    author_name = podcast.author
    title = podcast.title
    duration = podcast.length

    try:
        with open(audio_file_path, 'rb') as audio_file:
            update.message.reply_audio(
                audio_file, performer=author_name,
                title=title, duration=duration
            )

        logging.info(f'send podcast with id {podcast.video_id}')
    except Exception as e:
        update.message.reply_text(
            "For some reason, I can't send you audio, sorry."
        )
        logging.error(f'can`t make podcast {e}')
        return

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
