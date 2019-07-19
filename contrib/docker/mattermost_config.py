import logging
BACKEND = 'Mattermost'
BOT_ROOT_DIR = "/opt/errbot"
BOT_DATA_DIR = f"{BOT_ROOT_DIR}/data"
BOT_EXTRA_BACKEND_DIR = f"{BOT_ROOT_DIR}/backends/"
BOT_EXTRA_PLUGIN_DIR = f"{BOT_ROOT_DIR}/plugins/"
BOT_LOG_FILE = f"{BOT_ROOT_DIR}/log/err.log"
BOT_LOG_LEVEL = logging.DEBUG
BOT_LOG_SENTRY = False
SENTRY_DSN = ''
SENTRY_LOGLEVEL = 1
BOT_ASYNC = True

# Mattermost
MATTERMOST = {
    # Required
    'team': '<TEAM_NAME>',
    'server': '<MATTERMOST_SERVER_NAME>',
    # For the login, either
    'login': '<BOT_MATTERMOST_LOGIN>',
    'password': '<BOT_MATTERMOST_PASSWORD>',
    # Or, if you have a personal access token
    #'token': '<BOT_TOKEN>',
    # Optional
    'insecure': False, # Default = False. Set to true for self signed certificates
    'scheme': 'http', # Default = https
    'port': 8065, # Default = 8065
    'timeout': 30, # Default = 30. If the webserver disconnects idle connections later/earlier change this value
    'cards_hook': 'incomingWebhookId' # Needed for cards/attachments
}
BOT_IDENTITY=MATTERMOST

BOT_ADMINS = (['<DISCORD_NAME>'])
CHATROOM_PRESENCE = (["<CHAT_ROOM_NAME>"])
CHATROOM_FN = '<BOT_NAME>'
BOT_PREFIX = '!'

DIVERT_TO_PRIVATE = ()
CHATROOM_RELAY = {}
REVERSE_CHATROOM_RELAY = {}

# Err-StackStorm
STACKSTORM = {
    'auth_url': 'https://<STACKSTORM_SERVERNAME>/auth/v1',
    'api_url': 'https://<STACKSTORM_SERVERNAME>/api/v1',
    'stream_url': 'https://<STACKSTORM_SERVERNAME>/stream/v1',

    'verify_cert': False,
    'secrets_store': 'cleartext',
    'api_auth': {
        'user': {
            'name': '<BOT_ST2_USERNAME>',
            'password': "<BOT_ST2_PASSWORD>",
        },
    },
    'rbac_auth': {
        'standalone': {}
    },
    'timer_update': 900, #  Unit: second.  Bot token renewal interval.
}
