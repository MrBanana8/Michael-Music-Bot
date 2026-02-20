import os
import discord
from discord import app_commands
from dotenv import load_dotenv
from music import Song, get_player, get_or_create_player, remove_player

load_dotenv()

intents = discord.Intents.default()
intents.voice_states = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


@client.event
async def on_ready():
    await tree.sync()
    print(f'Logged in as {client.user}')
    print('Slash commands synced!')


@tree.command(name='play', description='Play a song from YouTube')
@app_commands.describe(query='Song name or YouTube URL')
async def play(interaction: discord.Interaction, query: str):
    if not interaction.user.voice:
        await interaction.response.send_message('You need to be in a voice channel!', ephemeral=True)
        return

    await interaction.response.defer()

    player = get_or_create_player(interaction.guild_id)
    player.text_channel = interaction.channel

    if not player.voice_client:
        player.voice_client = await interaction.user.voice.channel.connect()

    try:
        song = await Song.from_query(query, client.loop)
        await player.add_song(song)

        if player.current == song:
            await interaction.followup.send(f'🎵 Now playing: **{song.title}**')
        else:
            await interaction.followup.send(f'✅ Added to queue: **{song.title}**')
    except Exception as e:
        print(f'Play error: {e}')
        await interaction.followup.send('Error playing the song. Please try again.')


@tree.command(name='pause', description='Pause the current song')
async def pause(interaction: discord.Interaction):
    player = get_player(interaction.guild_id)
    if not player or not player.current:
        await interaction.response.send_message('Nothing is playing!', ephemeral=True)
        return

    player.pause()
    await interaction.response.send_message('⏸️ Paused')


@tree.command(name='resume', description='Resume the paused song')
async def resume(interaction: discord.Interaction):
    player = get_player(interaction.guild_id)
    if not player:
        await interaction.response.send_message('Nothing is playing!', ephemeral=True)
        return

    player.resume()
    await interaction.response.send_message('▶️ Resumed')


@tree.command(name='skip', description='Skip to the next song')
async def skip(interaction: discord.Interaction):
    player = get_player(interaction.guild_id)
    if not player or not player.current:
        await interaction.response.send_message('Nothing to skip!', ephemeral=True)
        return

    player.skip()
    await interaction.response.send_message('⏭️ Skipped')


@tree.command(name='stop', description='Stop playing and clear the queue')
async def stop(interaction: discord.Interaction):
    player = get_player(interaction.guild_id)
    if not player:
        await interaction.response.send_message('Nothing is playing!', ephemeral=True)
        return

    await player.stop()
    remove_player(interaction.guild_id)
    await interaction.response.send_message('⏹️ Stopped and cleared queue')


@tree.command(name='queue', description='Show the current song queue')
async def queue(interaction: discord.Interaction):
    player = get_player(interaction.guild_id)
    if not player or (not player.current and not player.queue):
        await interaction.response.send_message('The queue is empty!', ephemeral=True)
        return

    embed = discord.Embed(title='Music Queue', color=0x5865F2)

    songs = []
    if player.current:
        songs.append(f'🎵 Now Playing: **{player.current.title}**')

    for i, song in enumerate(player.queue[:9], 1):
        songs.append(f'{i}. **{song.title}**')

    embed.description = '\n'.join(songs)

    if len(player.queue) > 9:
        embed.set_footer(text=f'And {len(player.queue) - 9} more...')

    await interaction.response.send_message(embed=embed)


client.run(os.getenv('DISCORD_TOKEN'))
