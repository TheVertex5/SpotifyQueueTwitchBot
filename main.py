import spotipy
from spotipy.oauth2 import SpotifyOAuth
from twitchAPI import Twitch
from twitchAPI.oauth import UserAuthenticator
from twitchAPI.types import AuthScope, ChatEvent
from twitchAPI.chat import Chat, EventData, ChatCommand
from decouple import config
import asyncio

USER_SCOPE = [AuthScope.CHAT_READ, AuthScope.CHAT_EDIT]

scope = ("user-modify-playback-state", "user-read-playback-state")
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=config('SPOTIPY_CLIENT_ID'), client_secret=config('SPOTIPY_CLIENT_SECRET'), redirect_uri=config('SPOTIPY_REDIRECT_URI'), scope=scope), requests_session=True)


def is_track_URI(uri):
    return uri.startswith('spotify:track:')


def is_track_URL(url):
    return url.startswith('http://open.spotify.com/track/') | url.startswith('https://open.spotify.com/track/')


async def on_ready(ready_event: EventData):
    print('Bot is ready for work, joining channels')
    await ready_event.chat.join_room(config('TARGET_CHANNEL'))


async def queue_command(cmd: ChatCommand):
    if len(cmd.parameter) == 0:
        await cmd.reply('You did not tell me what song to add!')
    else:
        try:
            qStatus = sp.queue()
            if (qStatus['currently_playing'] is not None) & (len(qStatus['queue']) > 0):
                if is_track_URL(cmd.parameter) | is_track_URI(cmd.parameter):
                    sp.add_to_queue(cmd.parameter)
                else:
                    await cmd.reply('Provided was not a Spotify URL or URI!')
            else:
                await cmd.reply('Queue is empty and inactive!')
        finally:
            results = sp.queue()
            print('\n')
            print('PLAYING:', results['currently_playing']['name'])
            for idx, item in enumerate(results['queue']):
                track = item['name']
                print(idx, track)


async def run():
    twitch = await Twitch(config('APP_ID'), config('APP_SECRET'))
    auth = UserAuthenticator(twitch, USER_SCOPE, force_verify=False)
    token, refresh_token = await auth.authenticate()
    await twitch.set_user_authentication(token, USER_SCOPE, refresh_token)

    chat = await Chat(twitch)
    chat.set_prefix('$')
    chat.register_event(ChatEvent.READY, on_ready)
    chat.register_command('flxQueue', queue_command)
    chat.start()

    try:
        input('press ENTER to stop\n')
    finally:
        await chat.send_message(config('TARGET_CHANNEL'), 'Bot is shutting down, may be maintenance or error.\nCheck with Felix')
        chat.stop()
        await twitch.close()
        return

asyncio.run(run())
