from discord.errors import ClientException, DiscordException
from discord.ext.commands.errors import CommandError


class NotInVoiceChannel(CommandError):
    """Exception raised when a user is not in a channel"""


class InvalidUUID(CommandError):
    """Exception raised when a parsing a UUID
    """

    def __init__(self, param):
        self.param = param


class AlreadyMonitored(CommandError):
    """Exception raised when another user is already monitoring an account
    """

    def __init__(self, param):
        self.param = param


class AccountAlreadyMonitoring(CommandError):
    """Exception raised when a user is monitoring a different account already
    """

    def __init__(self, param):
        self.param = param


class NotMonitoring(CommandError):
    """Exception raised when an account is Not Monitoring any Accounts.
    """


class TooManyAccounts(CommandError):
    """Exception raised when more accounts are trying to be added than can be handleded.
    """


class InvalidTime(CommandError):
    """Exception raised when more accounts are trying to be added than can be handleded.
    """

    def __init__(self, param):
        self.param = param