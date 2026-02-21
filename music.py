import asyncio
import re
import discord
import yt_dlp

YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'ytsearch',
    'source_address': '0.0.0.0',
}

YDL_PLAYLIST_OPTIONS = {
    'extract_flat': 'in_playlist',
    'quiet': True,
    'no_warnings': True,
    'source_address': '0.0.0.0',
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}

PLAYLIST_PATTERN = re.compile(r'[?&]list=')


def is_playlist_url(query: str) -> bool:
    return query.startswith('http') and bool(PLAYLIST_PATTERN.search(query))


class Song:
    def __init__(self, title: str, url: str, stream_url: str | None = None):
        self.title = title
        self.url = url
        self.stream_url = stream_url

    async def ensure_stream_url(self, loop: asyncio.AbstractEventLoop):
        if self.stream_url:
            return
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            data = await loop.run_in_executor(None, lambda: ydl.extract_info(self.url, download=False))
            if 'entries' in data:
                data = data['entries'][0]
            self.stream_url = data.get('url')

    @classmethod
    async def from_query(cls, query: str, loop: asyncio.AbstractEventLoop):
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            if not query.startswith('http'):
                query = f'ytsearch:{query}'

            data = await loop.run_in_executor(None, lambda: ydl.extract_info(query, download=False))

            if 'entries' in data:
                data = data['entries'][0]

            return cls(
                title=data.get('title', 'Unknown'),
                url=data.get('webpage_url', query),
                stream_url=data.get('url')
            )

    @classmethod
    async def from_playlist(cls, url: str, loop: asyncio.AbstractEventLoop) -> list['Song']:
        with yt_dlp.YoutubeDL(YDL_PLAYLIST_OPTIONS) as ydl:
            data = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=False))

        songs = []
        for entry in data.get('entries', []):
            if entry:
                songs.append(cls(
                    title=entry.get('title', 'Unknown'),
                    url=entry.get('url') or entry.get('webpage_url', ''),
                ))
        return songs


class MusicPlayer:
    def __init__(self, guild_id: int):
        self.guild_id = guild_id
        self.queue: list[Song] = []
        self.voice_client: discord.VoiceClient | None = None
        self.current: Song | None = None
        self.text_channel: discord.TextChannel | None = None

    async def play_next(self):
        if not self.queue or not self.voice_client:
            self.current = None
            return

        self.current = self.queue.pop(0)

        await self.current.ensure_stream_url(self.voice_client.loop)
        source = discord.FFmpegPCMAudio(self.current.stream_url, **FFMPEG_OPTIONS)

        def after_playing(error):
            if error:
                print(f'Player error: {error}')
            asyncio.run_coroutine_threadsafe(self.play_next(), self.voice_client.loop)

        self.voice_client.play(source, after=after_playing)

        if self.text_channel:
            await self.text_channel.send(f'🎵 Now playing: **{self.current.title}**')

    async def add_song(self, song: Song):
        self.queue.append(song)
        if not self.voice_client.is_playing() and not self.voice_client.is_paused():
            await self.play_next()

    async def add_songs(self, songs: list[Song]):
        self.queue.extend(songs)
        if not self.voice_client.is_playing() and not self.voice_client.is_paused():
            await self.play_next()

    def skip(self):
        if self.voice_client and self.voice_client.is_playing():
            self.voice_client.stop()

    def pause(self):
        if self.voice_client and self.voice_client.is_playing():
            self.voice_client.pause()

    def resume(self):
        if self.voice_client and self.voice_client.is_paused():
            self.voice_client.resume()

    async def stop(self):
        self.queue.clear()
        self.current = None
        if self.voice_client:
            self.voice_client.stop()
            await self.voice_client.disconnect()
            self.voice_client = None


players: dict[int, MusicPlayer] = {}


def get_player(guild_id: int) -> MusicPlayer | None:
    return players.get(guild_id)


def get_or_create_player(guild_id: int) -> MusicPlayer:
    if guild_id not in players:
        players[guild_id] = MusicPlayer(guild_id)
    return players[guild_id]


def remove_player(guild_id: int):
    if guild_id in players:
        del players[guild_id]
