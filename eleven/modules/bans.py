import html
from typing import Optional, List

from telegram import Message, Chat, Update, Bot, User
from telegram.error import BadRequest
from telegram.ext import run_async, CommandHandler, Filters
from telegram.utils.helpers import mention_html

from eleven import dispatcher, BAN_STICKER, LOGGER, spamcheck
from eleven.modules.disable import DisableAbleCommandHandler
from eleven.modules.helper_funcs.chat_status import bot_admin, user_admin, is_user_ban_protected, can_restrict, \
    is_user_admin, is_user_in_chat
from eleven.modules.helper_funcs.extraction import extract_user_and_text
from eleven.modules.helper_funcs.string_handling import extract_time
from eleven.modules.log_channel import loggable
from eleven.modules.connection import connected

from eleven.modules.languages import tl
from eleven.modules.helper_funcs.alternate import send_message


@run_async
@spamcheck
@user_admin
@loggable
def ban(update, context):
    currentchat = update.effective_chat  # type: Optional[Chat]
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]
    args = context.args

    user_id, reason = extract_user_and_text(message, args)
    if user_id == "error":
        send_message(update.effective_message, tl(update.effective_message, reason))
        return ""

    conn = connected(context.bot, update, chat, user.id, need_admin=True)
    if conn:
        chat = dispatcher.bot.getChat(conn)
        chat_id = conn
        chat_name = dispatcher.bot.getChat(conn).title
    else:
        if update.effective_message.chat.type == "private":
            send_message(update.effective_message, tl(update.effective_message, "You can do this command in groups, not PM"))
            return ""
        chat = update.effective_chat
        chat_id = update.effective_chat.id
        chat_name = update.effective_message.chat.title

    check = context.bot.getChatMember(chat_id, context.bot.id)
    if check.status == 'member' or check['can_restrict_members'] == False:
        if conn:
            text = tl(update.effective_message, "I can't restrict people in {}! Make sure I'm admin and can appoint new admins.").format(chat_name)
        else:
            text = tl(update.effective_message, "I can't restrict people here! Make sure I'm admin and can appoint new admins.")
        send_message(update.effective_message, text, parse_mode="markdown")
        return ""

    if not user_id:
        send_message(update.effective_message, tl(update.effective_message, "You don't seem to be referring to a user."))
        return ""

    try:
        if conn:
            member = context.bot.getChatMember(chat_id, user_id)
        else:
            member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            if conn:
                text = tl(update.effective_message, "I can't find this user on *{}* 😣").format(chat_name)
            else:
                text = tl(update.effective_message, "I can't find this user 😣")
            send_message(update.effective_message, text, parse_mode="markdown")
            return ""
        else:
            raise

    if user_id == context.bot.id:
        send_message(update.effective_message, tl(update.effective_message, "I'm not gonna BAN myself, are you crazy? 😠"))
        return ""

    if is_user_ban_protected(chat, user_id, member):
        send_message(update.effective_message, tl(update.effective_message, "I really wish I could ban admins 😒"))
        return ""

    if member['can_restrict_members'] == False:
        if conn:
            text = tl(update.effective_message, "You have no right to restrict someone in *{}*.").format(chat_name)
        else:
            text = tl(update.effective_message, "You have no right to restrict someone.")
        send_message(update.effective_message, text, parse_mode="markdown")
        return ""

    log = "<b>{}:</b>" \
          "\n#BANNED" \
          "\n<b>Admin:</b> {}" \
          "\n<b>User:</b> {} (<code>{}</code>)".format(html.escape(chat.title),
                                                       mention_html(user.id, user.first_name),
                                                       mention_html(member.user.id, member.user.first_name),
                                                       member.user.id)
    if reason:
        log += "\n<b>Reason:</b> {}".format(reason)

    try:
        if conn:
            context.bot.kickChatMember(chat_id, user_id)
            context.bot.send_sticker(currentchat.id, BAN_STICKER)  # banhammer marie sticker
            send_message(update.effective_message, tl(update.effective_message, "Banned at *{}*! 😝").format(chat_name), parse_mode="markdown")
        else:
            chat.kick_member(user_id)
            if message.text.split(None, 1)[0][1:] == "sban":
                update.effective_message.delete()
            else:
                context.bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie sticker
                send_message(update.effective_message, tl(update.effective_message, "Banned! 😝"))
        return log

    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            send_message(update.effective_message, tl(update.effective_message, "Banned! 😝"), quote=False)
            return log
        elif excp.message == "Message can't be deleted":
            pass
        else:
            LOGGER.warning(update)
            LOGGER.exception("ERROR banned the user%s in the chat%s(%s) caused by%s", user_id, chat.title, chat.id,
                             excp.message)
            send_message(update.effective_message, tl(update.effective_message, "Well damn, I can't ban that user 😒"))

    return ""


@run_async
@spamcheck
@user_admin
@loggable
def temp_ban(update, context):
    currentchat = update.effective_chat  # type: Optional[Chat]
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]
    args = context.args

    user_id, reason = extract_user_and_text(message, args)
    if user_id == "error":
        send_message(update.effective_message, tl(update.effective_message, reason))
        return ""

    conn = connected(context.bot, update, chat, user.id, need_admin=True)
    if conn:
        chat = dispatcher.bot.getChat(conn)
        chat_id = conn
        chat_name = dispatcher.bot.getChat(conn).title
    else:
        if update.effective_message.chat.type == "private":
            send_message(update.effective_message, tl(update.effective_message, "You can do this command in groups, not PM"))
            return ""
        chat = update.effective_chat
        chat_id = update.effective_chat.id
        chat_name = update.effective_message.chat.title

    check = context.bot.getChatMember(chat_id, context.bot.id)
    if check.status == 'member':
        if conn:
            text = tl(update.effective_message, "I can't restrict people *{}*! Make sure I'm admin and can appoint new admins.").format(chat_name)
        else:
            text = tl(update.effective_message, "I can't restrict people here! Make sure I'm admin and can appoint new admins.")
        send_message(update.effective_message, text, parse_mode="markdown")
        return ""
    else:
        if check['can_restrict_members'] == False:
            if conn:
                text = tl(update.effective_message, "I can't restrict people *{}*! Make sure I'm admin and can appoint new admins.").format(chat_name)
            else:
                text = tl(update.effective_message, "I can't restrict people here! Make sure I'm admin and can appoint new admins.")
            send_message(update.effective_message, text, parse_mode="markdown")
            return ""

    if not user_id:
        send_message(update.effective_message, tl(update.effective_message, "You don't seem to be referring to a user."))
        return ""

    try:
        if conn:
            member = context.bot.getChatMember(chat_id, user_id)
        else:
            member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            send_message(update.effective_message, tl(update.effective_message, "I can't find this user 😣"))
            return ""
        else:
            raise

    if user_id == context.bot.id:
        send_message(update.effective_message, tl(update.effective_message, "I'm not gonna BAN myself, are you crazy? 😠"))
        return ""

    if is_user_ban_protected(chat, user_id, member):
        send_message(update.effective_message, tl(update.effective_message, "I really wish I could ban admins 😒"))
        return ""

    if member['can_restrict_members'] == False:
        send_message(update.effective_message, tl(update.effective_message, "You have no right to restrict someone."))
        return ""

    if not reason:
        send_message(update.effective_message, tl(update.effective_message, "You haven't specified a time to ban this user for!"))
        return ""
    
    split_reason = reason.split(None, 1)

    time_val = split_reason[0].lower()
    if len(split_reason) > 1:
        reason = split_reason[1]
    else:
        reason = ""
        
        bantime = extract_time(message, time_val)
        
        if not bantime:
            return ""

    log = "<b>{}:</b>" \
          "\n#TEMPBAN" \
          "\n<b>Admin:</b> {}" \
          "\n<b>User:</b> {} (<code>{}</code>)" \
          "\n<b>Time:</b> {}".format(html.escape(chat.title),
                                     mention_html(user.id, user.first_name),
                                     mention_html(member.user.id, member.user.first_name),
                                     member.user.id,
                                     time_val)
    if reason:
        log += "\n<b>Reason:</b> {}".format(reason)

    try:
        if conn:
            context.bot.kickChatMember(chat_id, user_id, until_date=bantime)
            context.bot.send_sticker(currentchat.id, BAN_STICKER)  # banhammer marie sticker
            send_message(update.effective_message, tl(update.effective_message, "Banned! User banned for *{}* at *{}*.").format(time_val, chat_name), parse_mode="markdown")
        else:
            chat.kick_member(user_id, until_date=bantime)
            context.bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie sticker
            send_message(update.effective_message, tl(update.effective_message, "Banned! User banned for {}.").format(time_val))
        return log

    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            send_message(update.effective_message, tl(update.effective_message, "Banned! User banned for {}.").format(time_val), quote=False)
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception("ERROR banning user %s in chat %s (%s) due to %s", user_id, chat.title, chat.id,
                             excp.message)
            send_message(update.effective_message, tl(update.effective_message, "Well damn, I can't kick that user 😒"))

    return ""


@run_async
@spamcheck
@user_admin
@loggable
def kick(update, context):
    currentchat = update.effective_chat  # type: Optional[Chat]
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]
    args = context.args

    user_id, reason = extract_user_and_text(message, args)
    if user_id == "error":
        send_message(update.effective_message, tl(update.effective_message, reason))
        return ""

    if not user_id:
        send_message(update.effective_message, tl(update.effective_message, "You don't seem to be referring to a user."))
        return ""

    conn = connected(context.bot, update, chat, user.id, need_admin=True)
    if conn:
        chat = dispatcher.bot.getChat(conn)
        chat_id = conn
        chat_name = dispatcher.bot.getChat(conn).title
    else:
        if update.effective_message.chat.type == "private":
            send_message(update.effective_message, tl(update.effective_message, "You can do this command in groups, not PM"))
            return ""
        chat = update.effective_chat
        chat_id = update.effective_chat.id
        chat_name = update.effective_message.chat.title

    check = context.bot.getChatMember(chat_id, context.bot.id)
    if check.status == 'member':
        if conn:
            text = tl(update.effective_message, "I can't restrict people in {}! Make sure I'm admin and can appoint new admins.").format(chat_name)
        else:
            text = tl(update.effective_message, "I can't restrict people here! Make sure I'm admin and can appoint new admins.")
        send_message(update.effective_message, text, parse_mode="markdown")
        return ""
    else:
        if check['can_restrict_members'] == False:
            if conn:
                text = tl(update.effective_message, "I can't restrict people *{}*! Make sure I'm admin and can appoint new admins.").format(chat_name)
            else:
                text = tl(update.effective_message, "I can't restrict people here! Make sure I'm admin and can appoint new admins.")
            send_message(update.effective_message, text, parse_mode="markdown")
            return ""

    if not user_id:
        return ""

    try:
        if conn:
            member = context.bot.getChatMember(chat_id, user_id)
        else:
            member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            send_message(update.effective_message, tl(update.effective_message, "I can't find this user 😣"))
            return ""
        else:
            raise

    if user_id == context.bot.id:
        send_message(update.effective_message, tl(update.effective_message, "I won't kick myself, are you crazy? 😠"))
        return ""

    if is_user_ban_protected(chat, user_id):
        send_message(update.effective_message, tl(update.effective_message, "I can't kick this person because he is an admin 😒"))
        return ""

    if user_id == context.bot.id:
        send_message(update.effective_message, tl(update.effective_message, "Yeahhh I'm not gonna do that 😝"))
        return ""

    check = context.bot.getChatMember(chat.id, user.id)
    if check['can_restrict_members'] == False:
        send_message(update.effective_message, tl(update.effective_message, "You have no right to restrict someone."))
        return ""

    if conn:
        res = context.bot.unbanChatMember(chat_id, user_id)  # unban on current user = kick
    else:
        res = chat.unban_member(user_id)  # unban on current user = kick
    if res:
        if conn:
            context.bot.send_sticker(currentchat.id, BAN_STICKER)  # banhammer marie sticker
            text = tl(update.effective_message, "Kicked at *{}*! 😝").format(chat_name)
            send_message(update.effective_message, text, parse_mode="markdown")
        else:
            if message.text.split(None, 1)[0][1:] == "skick":
                update.effective_message.delete()
            else:
                context.bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie sticker
                text = tl(update.effective_message, "Kicked! 😝")
                send_message(update.effective_message, text, parse_mode="markdown")
        log = "<b>{}:</b>" \
              "\n#KICKED" \
              "\n<b>Admin:</b> {}" \
              "\n<b>User:</b> {} (<code>{}</code>)".format(html.escape(chat.title),
                                                           mention_html(user.id, user.first_name),
                                                           mention_html(member.user.id, member.user.first_name),
                                                           member.user.id)
        log += "\n<b>Reason:</b> {}".format(reason)

        return log

    else:
        send_message(update.effective_message, tl(update.effective_message, "Well damn, I can't kick that user 😒"))

    return ""


@run_async
@spamcheck
@bot_admin
@can_restrict
def kickme(update, context):
    user_id = update.effective_message.from_user.id
    if is_user_admin(update.effective_chat, user_id):
        send_message(update.effective_message, tl(update.effective_message, "I wish I could... but you're an admin."))
        return

    res = update.effective_chat.unban_member(user_id)  # unban on current user = kick
    if res:
        send_message(update.effective_message, tl(update.effective_message, "No problem 😊"))
    else:
        send_message(update.effective_message, tl(update.effective_message, "Huh? I can't 🙄"))


@run_async
@spamcheck
@user_admin
@loggable
def unban(update, context):
    message = update.effective_message  # type: Optional[Message]
    user = update.effective_user  # type: Optional[User]
    chat = update.effective_chat  # type: Optional[Chat]
    args = context.args

    user_id, reason = extract_user_and_text(message, args)
    if user_id == "error":
        send_message(update.effective_message, tl(update.effective_message, reason))
        return ""

    conn = connected(context.bot, update, chat, user.id, need_admin=True)
    if conn:
        chat = dispatcher.bot.getChat(conn)
        chat_id = conn
        chat_name = dispatcher.bot.getChat(conn).title
    else:
        if update.effective_message.chat.type == "private":
            send_message(update.effective_message, tl(update.effective_message, "You can do this command in groups, not PM"))
            return ""
        chat = update.effective_chat
        chat_id = update.effective_chat.id
        chat_name = update.effective_message.chat.title

    if not user_id:
        return ""

    check = context.bot.getChatMember(chat_id, context.bot.id)
    if check.status == 'member':
        if conn:
            text = tl(update.effective_message, "I can't restrict people in {}! Make sure I'm admin and can appoint new admins.").format(chat_name)
        else:
            text = tl(update.effective_message, "I can't restrict people here! Make sure I'm admin and can appoint new admins.")
        send_message(update.effective_message, text, parse_mode="markdown")
        return ""
    else:
        if check['can_restrict_members'] == False:
            if conn:
                text = tl(update.effective_message, "I can't restrict people in {}! Make sure I'm admin and can appoint new admins.").format(chat_name)
            else:
                text = tl(update.effective_message, "I can't restrict people here! Make sure I'm admin and can appoint new admins.")
            send_message(update.effective_message, text, parse_mode="markdown")
            return ""

    try:
        if conn:
            member = context.bot.getChatMember(chat_id, user_id)
        else:
            member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            send_message(update.effective_message, tl(update.effective_message, "I can't find this user 😣"))
            return ""
        else:
            raise

    if user_id == context.bot.id:
        send_message(update.effective_message, tl(update.effective_message, "How would I unban myself if I wasn't here...? 🤔"))
        return ""

    if is_user_in_chat(chat, user_id):
        send_message(update.effective_message, tl(update.effective_message, "Why are you trying to unban someone that's already in the chat? 😑"))
        return ""

    check = context.bot.getChatMember(chat.id, user.id)
    if check['can_restrict_members'] == False:
        send_message(update.effective_message, tl(update.effective_message, "You have no right to restrict someone."))
        return ""

    if conn:
        context.bot.unbanChatMember(chat_id, user_id)
        send_message(update.effective_message, tl(update.effective_message, "Yep, this user can join in {}! 😁").format(chat_name))
    else:
        chat.unban_member(user_id)
        send_message(update.effective_message, tl(update.effective_message, "Yep, this user can join! 😁"))

    log = "<b>{}:</b>" \
          "\n#UNBANNED" \
          "\n<b>Admin:</b> {}" \
          "\n<b>User:</b> {} (<code>{}</code>)".format(html.escape(chat.title),
                                                       mention_html(user.id, user.first_name),
                                                       mention_html(member.user.id, member.user.first_name),
                                                       member.user.id)
    if reason:
        log += "\n<b>Reason:</b> {}".format(reason)

    return log


__help__ = "bans_help"

__mod_name__ = "Bans"

BAN_HANDLER = CommandHandler(["ban", "sban"], ban, pass_args=True)#, filters=Filters.group)
TEMPBAN_HANDLER = CommandHandler(["tban", "tempban"], temp_ban, pass_args=True)#, filters=Filters.group)
KICK_HANDLER = CommandHandler(["kick", "skick"], kick, pass_args=True)#, filters=Filters.group)
UNBAN_HANDLER = CommandHandler("unban", unban, pass_args=True)#, filters=Filters.group)
KICKME_HANDLER = DisableAbleCommandHandler("kickme", kickme, filters=Filters.group)

dispatcher.add_handler(BAN_HANDLER)
dispatcher.add_handler(TEMPBAN_HANDLER)
dispatcher.add_handler(KICK_HANDLER)
dispatcher.add_handler(UNBAN_HANDLER)
dispatcher.add_handler(KICKME_HANDLER)
