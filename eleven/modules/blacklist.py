import html
import re
from typing import Optional, List

from telegram import Message, Chat, Update, Bot, ParseMode
from telegram.error import BadRequest
from telegram.ext import CommandHandler, MessageHandler, Filters, run_async
from telegram.utils.helpers import mention_html, escape_markdown

import eleven.modules.sql.blacklist_sql as sql
from eleven import dispatcher, LOGGER, spamcheck, OWNER_ID
from eleven.modules.disable import DisableAbleCommandHandler
from telegram.utils.helpers import mention_markdown
from eleven.modules.helper_funcs.chat_status import user_admin, user_not_admin
from eleven.modules.helper_funcs.extraction import extract_text
from eleven.modules.helper_funcs.misc import split_message
from eleven.modules.log_channel import loggable
from eleven.modules.warns import warn
from eleven.modules.helper_funcs.string_handling import extract_time
from eleven.modules.connection import connected

from eleven.modules.languages import tl
from eleven.modules.helper_funcs.alternate import send_message

BLACKLIST_GROUP = 11


@run_async
@spamcheck
def blacklist(update, context):
	msg = update.effective_message  # type: Optional[Message]
	chat = update.effective_chat  # type: Optional[Chat]
	user = update.effective_user  # type: Optional[User]
	args = context.args
	
	conn = connected(context.bot, update, chat, user.id, need_admin=False)
	if conn:
		chat_id = conn
		chat_name = dispatcher.bot.getChat(conn).title
	else:
		if chat.type == "private":
			return
		else:
			chat_id = update.effective_chat.id
			chat_name = chat.title
	
	filter_list = tl(update.effective_message, "<b>Current blacklisted words:\n {}:</b>\n").format(chat_name)

	all_blacklisted = sql.get_chat_blacklist(chat_id)

	if len(args) > 0 and args[0].lower() == 'copy':
		for trigger in all_blacklisted:
			filter_list += "<code>{}</code>\n".format(html.escape(trigger))
	else:
		for trigger in all_blacklisted:
			filter_list += " - <code>{}</code>\n".format(html.escape(trigger))

	# for trigger in all_blacklisted:
	#     filter_list += " - <code>{}</code>\n".format(html.escape(trigger))

	split_text = split_message(filter_list)
	for text in split_text:
		if filter_list == tl(update.effective_message, "<b>Current blacklisted words:\n {}:</b>\n").format(chat_name):
			send_message(update.effective_message, tl(update.effective_message, "There are no blacklisted messages in <b>{}</b>!").format(chat_name), parse_mode=ParseMode.HTML)
			return
		send_message(update.effective_message, text, parse_mode=ParseMode.HTML)


@run_async
@spamcheck
@user_admin
def add_blacklist(update, context):
	msg = update.effective_message  # type: Optional[Message]
	chat = update.effective_chat  # type: Optional[Chat]
	user = update.effective_user  # type: Optional[User]
	words = msg.text.split(None, 1)

	conn = connected(context.bot, update, chat, user.id)
	if conn:
		chat_id = conn
		chat_name = dispatcher.bot.getChat(conn).title
	else:
		chat_id = update.effective_chat.id
		if chat.type == "private":
			return
		else:
			chat_name = chat.title

	if len(words) > 1:
		text = words[1]
		to_blacklist = list(set(trigger.strip() for trigger in text.split("\n") if trigger.strip()))
		for trigger in to_blacklist:
			sql.add_to_blacklist(chat_id, trigger.lower())

		if len(to_blacklist) == 1:
			send_message(update.effective_message, tl(update.effective_message, "<code>{}</code> Added to the blacklist in <b>{}</b>!").format(html.escape(to_blacklist[0]), chat_name),
				parse_mode=ParseMode.HTML)

		else:
			send_message(update.effective_message, tl(update.effective_message, "Added <code>{}</code> triggers to the blacklist in <b>{}</b>!").format(len(to_blacklist), chat_name), parse_mode=ParseMode.HTML)

	else:
		send_message(update.effective_message, tl(update.effective_message, "Tell me which words you would like to add to the blacklist."))


@run_async
@spamcheck
@user_admin
def unblacklist(update, context):
	msg = update.effective_message  # type: Optional[Message]
	chat = update.effective_chat  # type: Optional[Chat]
	user = update.effective_user  # type: Optional[User]
	words = msg.text.split(None, 1)

	conn = connected(context.bot, update, chat, user.id)
	if conn:
		chat_id = conn
		chat_name = dispatcher.bot.getChat(conn).title
	else:
		chat_id = update.effective_chat.id
		if chat.type == "private":
			return
		else:
			chat_name = chat.title


	if len(words) > 1:
		text = words[1]
		to_unblacklist = list(set(trigger.strip() for trigger in text.split("\n") if trigger.strip()))
		successful = 0
		for trigger in to_unblacklist:
			success = sql.rm_from_blacklist(chat_id, trigger.lower())
			if success:
				successful += 1

		if len(to_unblacklist) == 1:
			if successful:
				send_message(update.effective_message, tl(update.effective_message, "Removed <code>{}</code> from the blacklist!").format(html.escape(to_unblacklist[0]), chat_name),
							   parse_mode=ParseMode.HTML)
			else:
				send_message(update.effective_message, "This is not a trigger for a blacklist ...!")

		elif successful == len(to_unblacklist):
			send_message(update.effective_message, tl(update.effective_message, "Removed <code>{}</code> triggers from the blacklist.").format(
					successful, chat_name), parse_mode=ParseMode.HTML)

		elif not successful:
			send_message(update.effective_message, tl(update.effective_message, "None of these triggers exist, so they weren't removed.").format(
					successful, len(to_unblacklist) - successful), parse_mode=ParseMode.HTML)

		else:
			send_message(update.effective_message, tl(update.effective_message, "Pemicu <code>{}</code> dihapus dari daftar hitam. {} Tidak ada, "
				"jadi tidak dihapus.").format(successful, len(to_unblacklist) - successful),
				parse_mode=ParseMode.HTML)
	else:
		send_message(update.effective_message, tl(update.effective_message, "Tell me which words you would like to add to the blacklist."))


@run_async
@spamcheck
@loggable
@user_admin
def blacklist_mode(update, context):
	chat = update.effective_chat  # type: Optional[Chat]
	user = update.effective_user  # type: Optional[User]
	msg = update.effective_message  # type: Optional[Message]
	args = context.args

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

	if args:
		if args[0].lower() == 'off' or args[0].lower() == 'nothing' or args[0].lower() == 'no':
			settypeblacklist = tl(update.effective_message, 'do nothing')
			sql.set_blacklist_strength(chat_id, 0, "0")
		elif args[0].lower() == 'del' or args[0].lower() == 'delete':
			settypeblacklist = tl(update.effective_message, 'left, the message will be deleted')
			sql.set_blacklist_strength(chat_id, 1, "0")
		elif args[0].lower() == 'warn':
			settypeblacklist = tl(update.effective_message, 'warn sender')
			sql.set_blacklist_strength(chat_id, 2, "0")
		elif args[0].lower() == 'mute':
			settypeblacklist = tl(update.effective_message, 'mute sender')
			sql.set_blacklist_strength(chat_id, 3, "0")
		elif args[0].lower() == 'kick':
			settypeblacklist = tl(update.effective_message, 'kick sender')
			sql.set_blacklist_strength(chat_id, 4, "0")
		elif args[0].lower() == 'ban':
			settypeblacklist = tl(update.effective_message, 'banned sender')
			sql.set_blacklist_strength(chat_id, 5, "0")
		elif args[0].lower() == 'tban':
			if len(args) == 1:
				teks = tl(update.effective_message, """It looks like you are trying to set a temporary value to blacklist, but has not determined the time; use `/blacklistmode tban <timevalue>`.

Examples of time values: 4m = 4 minute, 3h = 3 hours, 6d = 6 days, 5w = 5 weeks.""")
				send_message(update.effective_message, teks, parse_mode="markdown")
				return ""
			restime = extract_time(msg, args[1])
			if not restime:
				teks = tl(update.effective_message, """Invalid time value!
Examples of time values: 4m = 4 minute, 3h = 3 hours, 6d = 6 days, 5w = 5 weeks.""")
				send_message(update.effective_message, teks, parse_mode="markdown")
				return ""
			settypeblacklist = tl(update.effective_message, 'temporarily ban for {}').format(args[1])
			sql.set_blacklist_strength(chat_id, 6, str(args[1]))
		elif args[0].lower() == 'tmute':
			if len(args) == 1:
				teks = tl(update.effective_message, """It looks like you are trying to set a temporary value to blacklist, but has not determined the time; use `/blacklistmode tmute <timevalue>`.

Examples of time values: 4m = 4 minute, 3h = 3 hours, 6d = 6 days, 5w = 5 weeks.""")
				send_message(update.effective_message, teks, parse_mode="markdown")
				return ""
			restime = extract_time(msg, args[1])
			if not restime:
				teks = tl(update.effective_message, """Nilai waktu tidak valid!
Contoh nilai waktu: 4m = 4 menit, 3h = 3 jam, 6d = 6 hari, 5w = 5 minggu.""")
				send_message(update.effective_message, teks, parse_mode="markdown")
				return ""
			settypeblacklist = tl(update.effective_message, 'temporarily mute for {}').format(args[1])
			sql.set_blacklist_strength(chat_id, 7, str(args[1]))
		else:
			send_message(update.effective_message, tl(update.effective_message, "I only understand off/del/warn/ban/kick/mute/tban/tmute!"))
			return ""
		if conn:
			text = tl(update.effective_message, "Blacklist mode changed, will `{}` at *{}*!").format(settypeblacklist, chat_name)
		else:
			text = tl(update.effective_message, "Blacklist mode changed, will `{}`!").format(settypeblacklist)
		send_message(update.effective_message, text, parse_mode="markdown")
		return "<b>{}:</b>\n" \
				"<b>Admin:</b> {}\n" \
				"Changed the blacklist mode. will {}.".format(html.escape(chat.title),
																			mention_html(user.id, user.first_name), settypeblacklist)
	else:
		getmode, getvalue = sql.get_blacklist_setting(chat.id)
		if getmode == 0:
			settypeblacklist = tl(update.effective_message, "disabled")
		elif getmode == 1:
			settypeblacklist = tl(update.effective_message, "delete")
		elif getmode == 2:
			settypeblacklist = tl(update.effective_message, "warn")
		elif getmode == 3:
			settypeblacklist = tl(update.effective_message, "mute")
		elif getmode == 4:
			settypeblacklist = tl(update.effective_message, "kick")
		elif getmode == 5:
			settypeblacklist = tl(update.effective_message, "ban")
		elif getmode == 6:
			settypeblacklist = tl(update.effective_message, "temp ban for {}").format(getvalue)
		elif getmode == 7:
			settypeblacklist = tl(update.effective_message, "temp mute for").format(getvalue)
		if conn:
			text = tl(update.effective_message, "Current blacklist mode is set to *{}* in *{}*.").format(settypeblacklist, chat_name)
		else:
			text = tl(update.effective_message, "Current blacklist mode is set to *{}*.").format(settypeblacklist)
		send_message(update.effective_message, text, parse_mode=ParseMode.MARKDOWN)
	return ""


def findall(p, s):
	i = s.find(p)
	while i != -1:
		yield i
		i = s.find(p, i+1)

@run_async
@user_not_admin
def del_blacklist(update, context):
	chat = update.effective_chat  # type: Optional[Chat]
	message = update.effective_message  # type: Optional[Message]
	user = update.effective_user
	bot = context.bot
	to_match = extract_text(message)
	if not to_match:
		return

	getmode, value = sql.get_blacklist_setting(chat.id)

	chat_filters = sql.get_chat_blacklist(chat.id)
	for trigger in chat_filters:
		pattern = r"( |^|[^\w])" + re.escape(trigger) + r"( |$|[^\w])"
		if re.search(pattern, to_match, flags=re.IGNORECASE):
			try:
				if getmode == 0:
					return
				elif getmode == 1:
					message.delete()
				elif getmode == 2:
					message.delete()
					warn(update.effective_user, chat, tl(update.effective_message, "Say '{}' which in blacklist words").format(trigger), message, update.effective_user, conn=False)
					return
				elif getmode == 3:
					message.delete()
					bot.restrict_chat_member(chat.id, update.effective_user.id, can_send_messages=False)
					bot.sendMessage(chat.id, tl(update.effective_message, "{} muted because say '{}' which in blacklist words").format(mention_markdown(user.id, user.first_name), trigger), parse_mode="markdown")
					return
				elif getmode == 4:
					message.delete()
					res = chat.unban_member(update.effective_user.id)
					if res:
						bot.sendMessage(chat.id, tl(update.effective_message, "{} kicked because say '{}' which in blacklist words").format(mention_markdown(user.id, user.first_name), trigger), parse_mode="markdown")
					return
				elif getmode == 5:
					message.delete()
					chat.kick_member(user.id)
					bot.sendMessage(chat.id, tl(update.effective_message, "{} banned because say '{}' which in blacklist words").format(mention_markdown(user.id, user.first_name), trigger), parse_mode="markdown")
					return
				elif getmode == 6:
					message.delete()
					bantime = extract_time(message, value)
					chat.kick_member(user.id, until_date=bantime)
					bot.sendMessage(chat.id, tl(update.effective_message, "{} banned for {} because say '{}' which in blacklist words").format(mention_markdown(user.id, user.first_name), value, trigger), parse_mode="markdown")
					return
				elif getmode == 7:
					message.delete()
					mutetime = extract_time(message, value)
					bot.restrict_chat_member(chat.id, user.id, until_date=mutetime, can_send_messages=False)
					bot.sendMessage(chat.id, tl(update.effective_message, "{} muted for {} because say '{}' which in blacklist words").format(mention_markdown(user.id, user.first_name), value, trigger), parse_mode="markdown")
					return
			except BadRequest as excp:
				if excp.message == "Message to delete not found":
					pass
				else:
					LOGGER.exception("Error while deleting blacklist message.")
			break


def __import_data__(chat_id, data):
	# set chat blacklist
	blacklist = data.get('blacklist', {})
	for trigger in blacklist:
		sql.add_to_blacklist(chat_id, trigger)


def __migrate__(old_chat_id, new_chat_id):
	sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
	blacklisted = sql.num_blacklist_chat_filters(chat_id)
	return tl(user_id, "There are `{}` blacklisted words.").format(blacklisted)


def __stats__():
	return tl(OWNER_ID, "{} blacklist triggers, across {} chats.").format(sql.num_blacklist_filters(),
															sql.num_blacklist_filter_chats())


__mod_name__ = "Blacklists"

__help__ = "blacklist_help"

BLACKLIST_HANDLER = DisableAbleCommandHandler("blacklist", blacklist, pass_args=True,
											  admin_ok=True)
ADD_BLACKLIST_HANDLER = CommandHandler("addblacklist", add_blacklist)
UNBLACKLIST_HANDLER = CommandHandler(["unblacklist", "rmblacklist"], unblacklist)
BLACKLISTMODE_HANDLER = CommandHandler("blacklistmode", blacklist_mode, pass_args=True)
BLACKLIST_DEL_HANDLER = MessageHandler((Filters.text | Filters.command | Filters.sticker | Filters.photo) & Filters.group, del_blacklist)

dispatcher.add_handler(BLACKLIST_HANDLER)
dispatcher.add_handler(ADD_BLACKLIST_HANDLER)
dispatcher.add_handler(UNBLACKLIST_HANDLER)
dispatcher.add_handler(BLACKLISTMODE_HANDLER)
dispatcher.add_handler(BLACKLIST_DEL_HANDLER, group=BLACKLIST_GROUP)
