# Power initially took from https://github.com/AnimeKaizoku/SaitamaRobot.

import html
import json
import os
from typing import List, Optional

from telegram import Bot, Update, ParseMode, TelegramError
from telegram.ext import CommandHandler, run_async, Filters
from telegram.utils.helpers import mention_html

from eleven import dispatcher, WHITELIST_USERS, SUPPORT_USERS, SUDO_USERS, OWNER_ID
from eleven.modules.helper_funcs.extraction import extract_user
from eleven.modules.helper_funcs.filters import CustomFilters

ELEVATED_USERS_FILE = os.path.join(os.getcwd(), 'eleven/elevated_users.json')


def check_user_id(user_id: int, bot: Bot) -> Optional[str]:
    if not user_id:
        reply = "That...is a chat! You Moron?"

    elif user_id == bot.id:
        reply = "This does not work that way."

    else:
        reply = None
    return reply

@run_async
def addsudo(update, context) -> str:
    args = context.args
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat

    user_id = extract_user(message, args)
    user_member = context.bot.getChat(user_id)
    rt = ""

    reply = check_user_id(user_id, context.bot)
    if reply:
        message.reply_text(reply)
        return ""

    with open(ELEVATED_USERS_FILE, 'r') as infile:
        data = json.load(infile)

    if user_id in SUDO_USERS:
        message.reply_text("This member is already a Sudo User")
        return ""

    if user_id in SUPPORT_USERS:
        rt += "Requested HA to promote a Support User to Sudo User."
        data['supports'].remove(user_id)
        SUPPORT_USERS.remove(user_id)

    if user_id in WHITELIST_USERS:
        rt += "Requested HA to promote a Whitelist User to Sudo User."
        data['whitelists'].remove(user_id)
        WHITELIST_USERS.remove(user_id)

    data['sudos'].append(user_id)
    SUDO_USERS.append(user_id)

    with open(ELEVATED_USERS_FILE, 'w') as outfile:
        json.dump(data, outfile, indent=4)

    update.effective_message.reply_text(
        rt + "\nSuccessfully set Power level of {} to Sudo User!".format(user_member.first_name))

    log_message = (f"#SUDO\n"
                   f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
                   f"<b>User:</b> {mention_html(user_member.id, user_member.first_name)}")

    if chat.type != 'private':
        log_message = f"<b>{html.escape(chat.title)}:</b>\n" + log_message

    return log_message


@run_async
def addsupport(update, context) -> str:
    args = context.args
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat

    user_id = extract_user(message, args)
    user_member = context.bot.getChat(user_id)
    rt = ""

    reply = check_user_id(user_id, context.bot)
    if reply:
        message.reply_text(reply)
        return ""

    with open(ELEVATED_USERS_FILE, 'r') as infile:
        data = json.load(infile)

    if user_id in SUDO_USERS:
        rt += "Requested HA to deomote this Sudo User to Support User"
        data['sudos'].remove(user_id)
        SUDO_USERS.remove(user_id)

    if user_id in SUPPORT_USERS:
        message.reply_text("This user is already a Support User.")
        return ""

    if user_id in WHITELIST_USERS:
        rt += "Requested HA to promote this Whitelist User to Support User"
        data['whitelists'].remove(user_id)
        WHITELIST_USERS.remove(user_id)

    data['supports'].append(user_id)
    SUPPORT_USERS.append(user_id)

    with open(ELEVATED_USERS_FILE, 'w') as outfile:
        json.dump(data, outfile, indent=4)

    update.effective_message.reply_text(rt + f"\n{user_member.first_name} was added as a Support User!")

    log_message = (f"#SUPPORT\n"
                   f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
                   f"<b>User:</b> {mention_html(user_member.id, user_member.first_name)}")

    if chat.type != 'private':
        log_message = f"<b>{html.escape(chat.title)}:</b>\n" + log_message

    return log_message


@run_async
def addwhitelist(update, context) -> str:
    args = context.args
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat

    user_id = extract_user(message, args)
    user_member = context.bot.getChat(user_id)
    rt = ""

    reply = check_user_id(user_id, context.bot)
    if reply:
        message.reply_text(reply)
        return ""

    with open(ELEVATED_USERS_FILE, 'r') as infile:
        data = json.load(infile)

    if user_id in SUDO_USERS:
        rt += "This member is a Sudo User, Demoting to Whitelist User."
        data['sudos'].remove(user_id)
        SUDO_USERS.remove(user_id)

    if user_id in SUPPORT_USERS:
        rt += "This user is already a Demon Support User, Demoting to Whitelist User."
        data['supports'].remove(user_id)
        SUPPORT_USERS.remove(user_id)

    if user_id in WHITELIST_USERS:
        message.reply_text("This user is already a Whitelist User.")
        return ""

    data['whitelists'].append(user_id)
    WHITELIST_USERS.append(user_id)

    with open(ELEVATED_USERS_FILE, 'w') as outfile:
        json.dump(data, outfile, indent=4)

    update.effective_message.reply_text(
        rt + f"\nSuccessfully promoted {user_member.first_name} to Whitelist User!")

    log_message = (f"#WHITELIST\n"
                   f"<b>Admin:</b> {mention_html(user.id, user.first_name)} \n"
                   f"<b>User:</b> {mention_html(user_member.id, user_member.first_name)}")

    if chat.type != 'private':
        log_message = f"<b>{html.escape(chat.title)}:</b>\n" + log_message

    return log_message


@run_async
def removesudo(update, context) -> str:
    args = context.args
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat

    user_id = extract_user(message, args)
    user_member = context.bot.getChat(user_id)

    reply = check_user_id(user_id, context.bot)
    if reply:
        message.reply_text(reply)
        return ""

    with open(ELEVATED_USERS_FILE, 'r') as infile:
        data = json.load(infile)

    if user_id in SUDO_USERS:
        message.reply_text("Requested HA to demote this user to Civilian")
        SUDO_USERS.remove(user_id)
        data['sudos'].remove(user_id)

        with open(ELEVATED_USERS_FILE, 'w') as outfile:
            json.dump(data, outfile, indent=4)

        log_message = (f"#UNSUDO\n"
                       f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
                       f"<b>User:</b> {mention_html(user_member.id, user_member.first_name)}")

        if chat.type != 'private':
            log_message = "<b>{}:</b>\n".format(html.escape(chat.title)) + log_message

        return log_message

    else:
        message.reply_text("This user is not a Sudo User!")
        return ""


@run_async
def removesupport(update, context) -> str:
    args = context.args
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat

    user_id = extract_user(message, args)
    user_member = context.bot.getChat(user_id)

    reply = check_user_id(user_id, context.bot)
    if reply:
        message.reply_text(reply)
        return ""

    with open(ELEVATED_USERS_FILE, 'r') as infile:
        data = json.load(infile)

    if user_id in SUPPORT_USERS:
        message.reply_text("Requested HA to demote this user to Civilian")
        SUPPORT_USERS.remove(user_id)
        data['supports'].remove(user_id)

        with open(ELEVATED_USERS_FILE, 'w') as outfile:
            json.dump(data, outfile, indent=4)

        log_message = (f"#UNSUPPORT\n"
                       f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
                       f"<b>User:</b> {mention_html(user_member.id, user_member.first_name)}")

        if chat.type != 'private':
            log_message = f"<b>{html.escape(chat.title)}:</b>\n" + log_message

        return log_message

    else:
        message.reply_text("This user is not a Support User!")
        return ""


@run_async
def removewhitelist(update, context) -> str:
    args = context.args
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat

    user_id = extract_user(message, args)
    user_member = context.bot.getChat(user_id)

    reply = check_user_id(user_id, context.bot)
    if reply:
        message.reply_text(reply)
        return ""

    with open(ELEVATED_USERS_FILE, 'r') as infile:
        data = json.load(infile)

    if user_id in WHITELIST_USERS:
        message.reply_text("Demoting to normal user")
        WHITELIST_USERS.remove(user_id)
        data['whitelists'].remove(user_id)

        with open(ELEVATED_USERS_FILE, 'w') as outfile:
            json.dump(data, outfile, indent=4)

        log_message = (f"#UNWHITELIST\n"
                       f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
                       f"<b>User:</b> {mention_html(user_member.id, user_member.first_name)}")

        if chat.type != 'private':
            log_message = f"<b>{html.escape(chat.title)}:</b>\n" + log_message

        return log_message
    else:
        message.reply_text("This user is not a Whitelist User!")
        return ""


@run_async
def sudolist(update, context):
    reply = "<b>Sudo Users:</b>\n"
    for each_user in SUDO_USERS:
        user_id = int(each_user)
        try:
            user = context.bot.get_chat(user_id)
            reply += f"• {mention_html(user_id, user.first_name)}\n"
        except TelegramError:
            pass
    update.effective_message.reply_text(reply, parse_mode=ParseMode.HTML)


@run_async
def supportlist(update, context):
    reply = "<b>Support Users:</b>\n"
    for each_user in SUPPORT_USERS:
        user_id = int(each_user)
        try:
            user = context.bot.get_chat(user_id)
            reply += f"• {mention_html(user_id, user.first_name)}\n"
        except TelegramError:
            pass
    update.effective_message.reply_text(reply, parse_mode=ParseMode.HTML)


@run_async
def whitelistlist(update, context):
    reply = "<b>Whitelist Users:</b>\n"
    for each_user in WHITELIST_USERS:
        user_id = int(each_user)
        try:
            user = context.bot.get_chat(user_id)

            reply += f"• {mention_html(user_id, user.first_name)}\n"
        except TelegramError:
            pass
    update.effective_message.reply_text(reply, parse_mode=ParseMode.HTML)


SUDO_HANDLER = CommandHandler("addsudo", addsudo, filters=Filters.user(OWNER_ID))
SUPPORT_HANDLER = CommandHandler("addsupport", addsupport, filters=Filters.user(OWNER_ID))
WHITELIST_HANDLER = CommandHandler("addwhitelist", addwhitelist, filters=Filters.user(OWNER_ID))

UNSUDO_HANDLER = CommandHandler("removesudo", removesudo, filters=Filters.user(OWNER_ID))
UNSUPPORT_HANDLER = CommandHandler("removesupport", removesupport, filters=Filters.user(OWNER_ID))
UNWHITELIST_HANDLER = CommandHandler("removewhitelist", removewhitelist, filters=Filters.user(OWNER_ID))

WHITELISTLIST_HANDLER = CommandHandler("whitelistlist", whitelistlist)
SUPPORTLIST_HANDLER = CommandHandler("supportlist", supportlist)
SUDOLIST_HANDLER = CommandHandler("sudolist", sudolist)

dispatcher.add_handler(SUDO_HANDLER)
dispatcher.add_handler(SUPPORT_HANDLER)
dispatcher.add_handler(WHITELIST_HANDLER)

dispatcher.add_handler(UNSUDO_HANDLER)
dispatcher.add_handler(UNSUPPORT_HANDLER)
dispatcher.add_handler(UNWHITELIST_HANDLER)

dispatcher.add_handler(WHITELISTLIST_HANDLER)
dispatcher.add_handler(SUPPORTLIST_HANDLER)
dispatcher.add_handler(SUDOLIST_HANDLER)
