import subprocess
from threading import Thread
from pyrogram import Client, filters
from pykeyboard import InlineKeyboard
from pyrogram.types import InlineKeyboardButton
import time
import asyncio
import re
from os import mkdir, system

AppId = 6969  #Replace With Your Own
AppHash = "deafbeef2fb23af2bab23f23aaff2a3"  #Replace With Your Own
BotToken = "13265466:AaSaddDaHGwaBdadsaDHfafw4daw"  #Replace With Your Own
app = Client("FFMpvdvdvdvegot", api_id=AppId, api_hash=AppHash, bot_token=BotToken)


class Convert:
    def __init__(self, quality, file, outfile):
        if quality == "Compressed":
            self._cmd = 'ffpb -i "{}" -c:v libx265 -crf 28  -preset ultrafast -movflags +faststart "{}" -y'.format(file, outfile)
        else:
            self._cmd = 'ffpb -i "{}" -vf scale="trunc(oh*a/2)*2:{}" -c:v libx265 -crf 28  -preset ultrafast -movflags +faststart "{}" -y'.format(
                file, quality, outfile)
        self._done = False
        self.progress = None
        self._fname = file.split("/")[-1]
        self._fpath = file

    def startasdaemon(self):
        process = subprocess.Popen(self._cmd, shell=True, errors="replace", stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT)
        while not self._done:
            realtime_output = process.stdout.readline()
            if realtime_output == '' and process.poll() is not None:
                self._done = True
                self.progress = "Completed Encoding"

                break
            if realtime_output:
                try:
                    prog = re.findall(r"(\d*%\|[\w\W]*\d*/\d+)", realtime_output.strip())[0].split(" ")
                except:
                    prog = []
                if prog:
                    self.progress = "Encoding File {} \n{}\nFrames: {}".format(self._fname, "".join(prog[:-1]),
                                                                               prog[-1])

    def start(self):
        t = Thread(target=self.startasdaemon)
        t.start()


async def format_bytes(size):
    power = 2 ** 10
    n = 0
    power_labels = {0: '', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while size > power:
        size /= power
        n += 1
    return str(round(size, 2)) + power_labels[n] + 'B'


async def progressbar(current, total, query, startedon, dlorup):
    diff = time.time() - startedon
    current_percent = str(round((current / total) * 100, 2))
    speed = current / diff
    current_formatted = await format_bytes(current)
    total_formatted = await format_bytes(total)
    speed_formatted = await format_bytes(speed)
    if int(diff)%5==0:
        await query.edit_message_text(
        "{} The File\nProgress: {}/{}  {}\nPercentage: {}".format(
            dlorup, current_formatted, total_formatted, speed_formatted + "/s", current_percent+"%")
    )


async def upload2tg(query, fpath):
    start = time.time()
    fname = fpath.split("/")[-1]
    await query.message.edit("Starting the upload of file ``" + fname + "``")
    await query.message.reply_video(fpath,
                                    progress=progressbar,
                                    progress_args=(query, start, "Uploading")

                                    )

    dirname = '/'.join(fpath.split("/")[:-1])
    system("rm -rf "+dirname)


@app.on_callback_query()
async def callbacks(client, query):
    data = query.data.split("#")
    dirname = str(time.time())+"/"
    mkdir(dirname)
    message_id = data[0]
    chat_id = data[2]
    message = await app.get_messages(chat_id=chat_id, message_ids=int(message_id))
    await query.edit_message_text("Starting Your Download...")

    path = await message.download(dirname, progress=progressbar,
                                  progress_args=(query, time.time(), "Downloading"))
    await query.edit_message_text("Download Completed Starting Encoding...")
    newfname = "/".join(path.split("/")[:-1]) + "/" + "[" + data[1] + "] " + path.split("/")[-1]

    converter = Convert(data[1], path, newfname)
    converter.start()

    oldtxt = ""
    while True:
        newtxt = converter.progress
        if oldtxt != newtxt:
            await asyncio.sleep(5)
            if newtxt is not None:
                await query.edit_message_text(newtxt)
            oldtxt = newtxt
        if newtxt == "Completed Encoding":
            break
    if converter._done:
        await query.edit_message_text("Starting to Upload The file Now")
        await upload2tg(query, newfname)


@app.on_message(filters.command(["convert"]))
async def ffmpeg(client, message):
    try:
        message = message.reply_to_message
        chat_id = str(message.chat.id)
        message_id = str(message.message_id)
        keyboard = InlineKeyboard()
        keyboard.row(
            InlineKeyboardButton('240p', message_id + "#240#" + str(chat_id)),
            InlineKeyboardButton('360p', message_id + "#360#" + str(chat_id))
        )
        keyboard.row(
            InlineKeyboardButton('720p', message_id + "#720#" + str(chat_id)),
            InlineKeyboardButton('1080p', message_id + "#1080#" + str(chat_id))
        )
        keyboard.row(
            InlineKeyboardButton('Compress', message_id + "#Compressed#" + str(chat_id))
        )
        await message.reply("Select The Option You Want", reply_markup=keyboard)
    except Exception as e:
        print("Error : "+str(e))
        await message.reply("Please Reply To A Valid Media File")

app.run()
