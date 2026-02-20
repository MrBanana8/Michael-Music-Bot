# Mike - Discord Music Bot

A Discord bot that plays music from YouTube in voice channels using slash commands.

## Prerequisites

- Python 3.10+
- [FFmpeg](https://ffmpeg.org/) installed and available in PATH
- A [Discord bot token](https://discord.com/developers/applications)

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Setup

Create a `.env` file in the project root:

```
DISCORD_TOKEN=your_bot_token_here
```

## Run

```bash
source .venv/bin/activate
python bot.py
```

## Commands

| Command | Description |
|---------|-------------|
| `/play <query>` | Play a song by name or YouTube URL |
| `/pause` | Pause the current song |
| `/resume` | Resume playback |
| `/skip` | Skip to the next song |
| `/stop` | Stop playing and clear the queue |
| `/queue` | Show the current song queue |
