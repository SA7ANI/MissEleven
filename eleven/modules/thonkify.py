# thonkify initially made by @devrism for discord
# Ported to telegram bot api (and) improved by @rupansh

import base64
from io import BytesIO
from PIL import Image
from telegram import Message, Update, Bot, User
from telegram.ext import run_async, CommandHandler
from eleven import dispatcher, spamcheck
from eleven.modules.languages import tl
from eleven.modules.helper_funcs.chat_status import is_user_admin, user_admin


@spamcheck
@user_admin
@run_async
def thonkify(update, context):
    args = context.args

    from eleven.modules.thonkify_dict import thonkifydict

    chat = update.effective_chat
    message = update.effective_message
    if not message.reply_to_message:
        msg = message.text.split(None, 1)[1]
    else:
        msg = message.reply_to_message.text

    # the processed photo becomes too long and unreadable +
    # the telegram doesnt support any longer dimensions +
    # you have the lulz
    if (len(msg)) > 39:
        message.reply_text(tl(chat.id, "Thonk yourself!"))
        return

    tracking = Image.open(BytesIO(base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAYAAAOACAYAAAAZzQIQAAAALElEQVR4nO3BAQ0AAADCoPdPbQ8HFAAAAAAAAAAAAAAAAAAAAAAAAAAAAPwZV4AAAfA8WFIAAAAASUVORK5CYII='))) # base64 encoded empty image(but longer)

    # remove characters thonkify can't parse
    for character in msg:
        if character not in thonkifydict:
            msg = msg.replace(character, "")

    # idk PIL. this part was untouched and ask @devrism for better explanation. According to my understanding, Image.new creates a new image and paste "pastes" the character one by one comparing it with "value" variable
    x = 0
    y = 896
    image = Image.new('RGBA', [x, y], (0, 0, 0))
    for character in msg:
        value = thonkifydict.get(character)
        addedimg = Image.new('RGBA', [x + value.size[0] + tracking.size[0], y], (0, 0, 0))
        addedimg.paste(image, [0, 0])
        addedimg.paste(tracking, [x, 0])
        addedimg.paste(value, [x + tracking.size[0], 0])
        image = addedimg
        x = x + value.size[0] + tracking.size[0]

    maxsize = 1024, 896
    if image.size[0] > maxsize[0]:
        image.thumbnail(maxsize, Image.ANTIALIAS)

    # put processed image in a buffer and then upload cause async
    with BytesIO() as buffer:
        buffer.name = 'cache/image.png'
        image.save(buffer, 'PNG')
        buffer.seek(0)
        context.bot.send_sticker(chat_id=message.chat_id, sticker=buffer)


THONKIFY_HANDLER = CommandHandler("thonkify", thonkify)

dispatcher.add_handler(THONKIFY_HANDLER)
