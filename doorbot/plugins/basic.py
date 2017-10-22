from doorbot import initialcwd, get_data, save_data, has_perm, require_perm, grant_perm, revoke_perm, get_user_perms, has_perm_msg
from slackbot.bot import respond_to, listen_to, default_reply
import subprocess
import datetime
import random
import pytz
import sys
import os
import re

def key_normalize(val):
    return re.sub('[^-: a-z0-9_]+', '', val.lower())

def unhighlight(val):
    if re.match("([a-zA-Z0-9_-]+)", val):
        return val[:1] + "\u200D" + val[1:]
    return val

@respond_to('^version$')
def version(message):
    """`version`: Get the bot's current version"""
    with subprocess.Popen(['/usr/bin/git', 'describe', '--always'], stdout=subprocess.PIPE) as proc:
        version = proc.stdout.read()

    message.send("_doorbot {}_".format(version.decode('utf-8').strip()))

@respond_to('^die$')
@respond_to('^restart$')
@require_perm('admin.restart')
def die(message):
    """`restart`: Update and restart the bot"""
    message.send(":frowning:")

    os.chdir(initialcwd)
    with subprocess.Popen(['/usr/bin/git', 'pull'], stdout=subprocess.PIPE) as proc:
            print(proc.stdout.read())

    os.execv(sys.executable, [sys.executable, '-m', 'doorbot'])

def url_or_code(val):
    if val.startswith('<'):
        return val[1:-1]
    else:
        return '`{}`'.format(val)

@respond_to('^help')
def help(message):
    """`help [command]`: Shows this help, or the help for command."""

    help_str = ""

    for key in HELP_THINGS:
        func =  eval(key)
        if callable(func) and hasattr(func, "__doc__"):
            if has_perm_msg(message, *getattr(func, "permisions", [])):
                if func.__doc__:
                    help_str += "\n" + func.__doc__.split('\n')[0].strip()

    message.reply('*doorbot*:\n' + help_str)

@respond_to('^grant ([a-z_.]+) (?:to )<@(U\w+)>', re.IGNORECASE)
@require_perm('grant.grant')
def grant_permission(message, permission, user):
    """`grant <permission> to <@person>`: Grants a permission"""
    grant_perm(user, permission)
    message.reply('OK, granting permission `{}`.'.format(permission))

@respond_to('^revoke ([a-z_.]+) (?:from )?<@(U\w+)>', re.IGNORECASE)
@require_perm('grant.revoke')
def revoke_permission(message, permission, user):
    """`revoke <permission> from <@person>`: Revokes a permission"""
    if revoke_perm(user, permission):
        message.reply('OK, {} revoked'.format(permission))
    else:
        message.reply("Permission `{}` not granted.".format(permission))

@respond_to('^perm(?:ission)?s? (?:for )?<@(U\w+)>', re.IGNORECASE)
@require_perm('grant.list')
def list_permissions(message, user):
    """`permissions for <@person>`: List someone's permissions"""
    user_perms = get_user_perms(user)

    if user_perms:
        message.reply('Permissions granted: `{}`'.format(', '.join(user_perms)))
    else:
        message.reply('No permissions granted.')

@respond_to('^my perm(?:issions)?s?$')
def my_permissions(message):
    """`my permissions`: List your own permissions"""
    user_perms = get_user_perms(message._get_user_id())

    if user_perms:
        message.reply('Your permissions: `{}`'.format(', '.join(user_perms)))
    else:
        message.reply('You have no permissions.')

@default_reply
def default(message):
    print(message.body)
    message.reply(':question_mark:')

HELP_THINGS = dir()
