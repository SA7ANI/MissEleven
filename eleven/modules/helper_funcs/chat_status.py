import sys
import traceback

from functools import wraps
from typing import Optional

from telegram import User, Chat, ChatMember, Update, Bot
from telegram import error

from eleven import DEL_CMDS, SUDO_USERS, WHITELIST_USERS

from eleven.modules import languages


def can_delete(chat: Chat, bot_id: int) -> bool:
	return chat.get_member(bot_id).can_delete_messages

def user_can_delete(chat: Chat, user: User, bot_id: int) -> bool:
	return chat.get_member(bot_id).can_delete_messages and chat.get_member(user.id).can_delete_messages

def bot_can_restrict(chat: Chat, bot_id: int) -> bool:
	return chat.get_member(bot_id).can_restrict_members


def is_user_ban_protected(chat: Chat, user_id: int, member: ChatMember = None) -> bool:
	if chat.type == 'private' \
			or user_id in SUDO_USERS \
			or user_id in WHITELIST_USERS \
			or chat.all_members_are_administrators or user_id == 777000:
		return True

	if not member:
		member = chat.get_member(user_id)
	return member.status in ('administrator', 'creator')


def is_user_admin(chat: Chat, user_id: int, member: ChatMember = None) -> bool:
	if chat.type == 'private' \
			or user_id in SUDO_USERS \
			or chat.all_members_are_administrators or user_id == 777000:
		return True

	try:
		if not member:
			member = chat.get_member(user_id)
		return member.status in ('administrator', 'creator')
	except:
		return False


def is_bot_admin(chat: Chat, bot_id: int, bot_member: ChatMember = None) -> bool:
	if chat.type == 'private' \
			or chat.all_members_are_administrators:
		return True

	if not bot_member:
		bot_member = chat.get_member(bot_id)
	return bot_member.status in ('administrator', 'creator')


def is_user_in_chat(chat: Chat, user_id: int) -> bool:
	member = chat.get_member(user_id)
	return member.status not in ('left', 'kicked')


def bot_can_delete(func):
	@wraps(func)
	def delete_rights(update, context, *args, **kwargs):
		if can_delete(update.effective_chat, context.bot.id):
			return func(update, context, *args, **kwargs)
		else:
			update.effective_message.reply_text(languages.tl(update.effective_message, "I can't delete messages here! Make sure I'm admin and can delete other user's messages."))

	return delete_rights


def can_pin(func):
	@wraps(func)
	def pin_rights(update, context, *args, **kwargs):
		if update.effective_chat.get_member(context.bot.id).can_pin_messages:
			return func(update, context, *args, **kwargs)
		else:
			update.effective_message.reply_text(languages.tl(update.effective_message, "I can't pin messages here! Make sure I'm admin and can pin messages."))

	return pin_rights


def can_promote(func):
	@wraps(func)
	def promote_rights(update, context, *args, **kwargs):
		if update.effective_chat.get_member(context.bot.id).can_promote_members:
			return func(update, context, *args, **kwargs)
		else:
			update.effective_message.reply_text(languages.tl(update.effective_message, "I can't promote/demote people here! Make sure I'm admin and can appoint new admins."))

	return promote_rights


def can_restrict(func):
	@wraps(func)
	def promote_rights(update, context, *args, **kwargs):
		if update.effective_chat.get_member(context.bot.id).can_restrict_members:
			return func(update, context, *args, **kwargs)
		else:
			update.effective_message.reply_text(languages.tl(update.effective_message, "I can't restrict people here! Make sure I'm admin and can appoint new admins."))

	return promote_rights


def bot_admin(func):
	@wraps(func)
	def is_admin(update, context, *args, **kwargs):
		if is_bot_admin(update.effective_chat, context.bot.id):
			return func(update, context, *args, **kwargs)
		else:
			update.effective_message.reply_text(languages.tl(update.effective_message, "I can't restrict people here! Make sure I'm admin and can appoint new admins."))

	return is_admin


def user_admin(func):
	@wraps(func)
	def is_admin(update, context, *args, **kwargs):
		if update.effective_chat.type == "private":
			return func(update, context, *args, **kwargs)
		user = update.effective_user  # type: Optional[User]
		if user and is_user_admin(update.effective_chat, user.id):
			return func(update, context, *args, **kwargs)

		elif not user:
			pass

		elif DEL_CMDS and " " not in update.effective_message.text:
			update.effective_message.delete()

		else:
			update.effective_message.reply_text(languages.tl(update.effective_message, "Who dis non-admin telling me what to do?"))

	return is_admin


def user_admin_no_reply(func):
	@wraps(func)
	def is_admin(update, context, *args, **kwargs):
		user = update.effective_user  # type: Optional[User]
		if user and is_user_admin(update.effective_chat, user.id):
			return func(update, context, *args, **kwargs)

		elif not user:
			pass

		elif DEL_CMDS and " " not in update.effective_message.text:
			update.effective_message.delete()

		else:
			context.bot.answer_callback_query(update.callback_query.id, languages.tl(update.effective_message, "You are not an admin in this group!"))

	return is_admin


def user_not_admin(func):
	@wraps(func)
	def is_not_admin(update, context, *args, **kwargs):
		user = update.effective_user  # type: Optional[User]
		if user and not is_user_admin(update.effective_chat, user.id):
			return func(update, context, *args, **kwargs)

	return is_not_admin

# This is unused code
def no_reply_handler(func):
	@wraps(func)
	def error_catcher(update, context, *args, **kwargs):
		try:
			func(update, context, *args,**kwargs)
		except error.BadRequest as err:
			if str(err) == "Reply message not found":
				print('Error')
				print(err)
				exc_type, exc_obj, exc_tb = sys.exc_info()
				log_errors = traceback.format_exception(etype=exc_type, value=exc_obj, tb=exc_tb)
				tl = languages.tl
				for x in log_errors:
					if " update.effective_message" in x:
						do_func = x.split("update.effective_message", 1)[1].split(")", 1)
						do_func = "".join(do_func)
						exec("update.effective_message" + do_func + ", quote=False)")
					elif "message.reply_text(" in x:
						do_func = x.split("message.reply_text", 1)[1].split(")", 1)
						do_func = "".join(do_func)
						exec("update.effective_message.reply_text" + do_func + ", quote=False)")
	return error_catcher
