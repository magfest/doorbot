from doorbot import initialcwd, get_data, save_data, has_perm, require_perm, grant_perm, revoke_perm, get_user_perms, has_perm_msg
from slackbot.bot import respond_to, listen_to, default_reply
import subprocess
import sys
import os
import re

def key_normalize(val):
    return re.sub('[^-: a-z0-9_]+', '', val.lower())

def unhighlight(val):
    if re.match("([a-zA-Z0-9_-]+)", val):
        return val[:1] + "\u200D" + val[1:]
    return val

@respond_to('^version$', re.IGNORECASE)
def version(message):
    """`version`: Get the bot's current version

    Displays the result of `git describe`.
    """
    with subprocess.Popen(['/usr/bin/git', 'describe', '--always'], stdout=subprocess.PIPE) as proc:
        version = proc.stdout.read()

    message.send("_doorbot {}_".format(version.decode('utf-8').strip()))

@respond_to('^die$', re.IGNORECASE)
@respond_to('^restart$', re.IGNORECASE)
@require_perm('admin.restart')
def die(message):
    """`restart`: Update and restart the bot.

    Aliases: `die`
    """
    message.send(":frowning:")

    os.chdir(initialcwd)
    with subprocess.Popen(['/usr/bin/git', 'pull'], stdout=subprocess.PIPE) as proc:
            print(proc.stdout.read())

    os.execv(sys.executable, [sys.executable, '-m', 'doorbot'])

@respond_to('^unlock', re.IGNORECASE)
@respond_to('^open', re.IGNORECASE)
@require_perm('door.open')
def unlock(message):
    """`unlock`: Unlock the warhouse door

    Aliases: `open`
    """
    with subprocess.Popen(['/usr/local/bin/open_door_shim'], stdout=subprocess.PIPE) as proc:
        out = proc.stdout.read()

    message.reply(out.strip())


@respond_to('^arm', re.IGNORECASE)
@respond_to('^lock', re.IGNORECASE)
@respond_to('^alarm', re.IGNORECASE)
@require_perm('door.alarm')
def alarm(message):
    """`arm`: Arm the warehouse alarm

    Aliases: `lock`, `alarm`
    """
    with subprocess.Popen(['/usr/local/bin/arm_alarm_shim'], stdout=subprocess.PIPE) as proc:
        out = proc.stdout.read()

    message.reply(out.strip())

@respond_to('^disarm', re.IGNORECASE)
@require_perm('door.alarm')
def dealarm(message):
    """`disarm`: Dis-arm the warehouse alarm
    """
    with subprocess.Popen(['/usr/local/bin/disarm_alarm_shim'], stdout=subprocess.PIPE) as proc:
        out = proc.stdout.read()

    message.reply(out.strip())

@respond_to('ip', re.IGNORECASE)
@require_perm('ip')
def ip(message):
    """`ip`: Displays the bot server's IP address information"""
    with subprocess.Popen(['ip', 'a'], stdout=subprocess.PIPE) as proc:
        out = proc.stdout.read()

    message.reply('```\n' + out.decode('ascii').strip() + '```')

def url_or_code(val):
    if val.startswith('<'):
        return val[1:-1]
    else:
        return '`{}`'.format(val)

@respond_to('^sudo')
def sudo(message):
    message.reply("Okay.")

@respond_to('^make me a (sandwh?it?ch|sammit?ch)', re.IGNORECASE)
def make_sandwich(message, _):
    message.reply("What? Make it yourself.")

def help_text_matches(command, docstring):
    cleaned = docstring.split('\n')[0].strip()
    if cleaned.startswith('`'):
        relevant = cleaned[1:cleaned.find('`', 1)]
    else:
        relevant = cleaned

    for line in docstring.split('\n'):
        if 'alias' in line.lower() and command.lower() in line.lower():
            return True

    return command.lower() in relevant.lower()

@respond_to('^help ?([a-z_ -]+)?', re.IGNORECASE)
def help(message, command=None):
    """`help [command]`: Shows this help, or the help for command."""

    help_str = ""

    for key in HELP_THINGS:
        func =  eval(key)
        if callable(func) and hasattr(func, "__doc__"):
            if has_perm_msg(message, *getattr(func, "permisions", [])):
                if func.__doc__:
                    if "default reply" in func.__doc__:
                        continue
                    if command and help_text_matches(command, func.__doc__):
                        # Add the whole thing
                        help_str += "\n" + func.__doc__.strip()

                        perms = getattr(func, "permissions", [])
                        if perms:
                            help_str += "\n*Permissions*: `" + ", ".join(perms) + "`"
                    elif not command:
                        help_str += "\n" + func.__doc__.strip().split('\n')[0]

    if command and not help_str:
        message.reply("Help for command `" + command + "` not found.")
    else:
        message.reply('*' + (command or 'doorbot') + '*:' + help_str)

@respond_to('^grant ([a-z_.\*]+) (?:to )<@(U\w+)>', re.IGNORECASE)
@require_perm('grant.grant')
def grant_permission(message, permission, user):
    """`grant <permission> to <@person>`: Grants a permission

    In order to grant a permission, you must also have that permission.
    Wildcard permission matching may be used with `*`.
    """

    if has_perm_msg(message):
        grant_perm(user, permission)
        message.reply('OK, granting permission `{}`.'.format(permission))
    else:
        message.reply('Cannot grant permission you do not have')

@respond_to('^revoke ([a-z_.\*]+) (?:from )?<@(U\w+)>', re.IGNORECASE)
@require_perm('grant.revoke')
def revoke_permission(message, permission, user):
    """`revoke <permission> from <@person>`: Revokes a permission

    In order to revoke a permission, you must also have that permission.
    """
    if has_perm_msg(message):
        if revoke_perm(user, permission):
            message.reply('OK, {} revoked'.format(permission))
        else:
            message.reply("Permission `{}` not granted.".format(permission))
    else:
        message.reply("Cannot revoke permission you do not have")

@respond_to('^perm(?:ission)?s? (?:for )?<@(U\w+)>', re.IGNORECASE)
@require_perm('grant.list')
def list_permissions(message, user):
    """`permissions for <@person>`: List someone's permissions"""
    user_perms = get_user_perms(user)

    if user_perms:
        message.reply('Permissions granted: `{}`'.format(', '.join(user_perms)))
    else:
        message.reply('No permissions granted.')

@respond_to('^my perm(?:issions)?s?$', re.IGNORECASE)
def my_permissions(message):
    """`my permissions`: List your own permissions"""
    user_perms = get_user_perms(message._get_user_id())

    if user_perms:
        message.reply('Your permissions: `{}`'.format(', '.join(user_perms)))
    else:
        message.reply('You have no permissions.')

@respond_to('execute order 66', re.IGNORECASE)
def order_66(message):
    message.reply("Yes, my lord.")

@default_reply
def default(message):
    print(message.body)
    message.reply('Unknown Command')

HELP_THINGS = dir()
