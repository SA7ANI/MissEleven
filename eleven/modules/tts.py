from telegram import ChatAction
from gtts import gTTS
import html
import urllib.request
import re
import json
from datetime import datetime
from typing import Optional, List
import time
import requests
from telegram import Message, Chat, Update, Bot, MessageEntity
from telegram import ParseMode
from telegram.ext import CommandHandler, run_async, Filters
from telegram.utils.helpers import escape_markdown, mention_html
from eleven import dispatcher
from eleven.__main__ import STATS
from eleven.modules.disable import DisableAbleCommandHandler
from eleven.modules.helper_funcs.extraction import extract_user
from eleven.modules.helper_funcs.chat_status import user_admin

@user_admin
@run_async
def tts(update, context):
	args = context.args
	current_time = datetime.strftime(datetime.now(), "%d.%m.%Y %H:%M:%S")
	filename = datetime.now().strftime("%d%m%y-%H%M%S%f")
	reply = " ".join(args)
	update.message.chat.send_action(ChatAction.RECORD_AUDIO)
	lang="ml"
	tts = gTTS(reply, lang)
	tts.save("k.mp3")
	with open("k.mp3", "rb") as f:
		linelist = list(f)
		linecount = len(linelist)
	if linecount == 1:
		update.message.chat.send_action(ChatAction.RECORD_AUDIO)
		lang = "en"
		tts = gTTS(reply, lang)
		tts.save("k.mp3")
	with open("k.mp3", "rb") as speech:
		update.message.reply_voice(speech, quote=False)


TTS_HANDLER = DisableAbleCommandHandler("tts", tts, pass_args=True, admin_ok=True)

dispatcher.add_handler(TTS_HANDLER)
