import asyncio
import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import youtube_dl
import yt_dlp
import gptapi

load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
intents = discord.Intents().all()
client = discord.Client(intents=intents)
bot = commands.Bot(command_prefix='!', intents=intents)

youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)


class Song:
    def __init__(self, url, title):
        self.url = url
        self.title = title


class Queue:
    def __init__(self):
        self.queue = []

    def is_empty(self):
        return len(self.queue) == 0

    def enqueue(self, song):
        self.queue.append(song)

    def dequeue(self):
        if self.is_empty():
            return None
        return self.queue.pop(0)

    def peek(self):
        if self.is_empty():
            return None
        return self.queue[0]


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = ""

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        if 'entries' in data:
            data = data['entries'][0]
        filename = data['title'] if stream else ytdl.prepare_filename(data)
        return filename


@bot.event
async def on_ready():
    print("Successfully logged in as:", bot.user)


@bot.command(name='ai', help='Chat with the bot')
async def chat_with_bot(ctx, *, user_message):
    # command = ctx.invoked_with
    bot_response = gptapi.chatgpt_response(prompt=user_message)
    await ctx.send(f'Answer: {bot_response}')


@bot.command(name='play', help='To play a song')
async def play(ctx, url):
    server = ctx.message.guild
    voice_channel = server.voice_client
    async with ctx.typing():
        filename = await YTDLSource.from_url(url, loop=bot.loop)
        song = Song(url, filename)
        if voice_channel.is_playing() or voice_channel.is_paused():
            bot.queue.enqueue(song)
            await ctx.send('**Added to queue:** {}'.format(filename))
        else:
            voice_channel.play(discord.FFmpegPCMAudio(executable="C:\\ffmpeg\\ffmpeg.exe",
                                                      source=filename))
            await ctx.send('**Now playing:** {}'.format(filename))


@bot.command(name='skip', help='Skip the current song')
async def skip(ctx):
    voice_channel = ctx.message.guild.voice_client
    if voice_channel.is_playing():
        voice_channel.stop()
        await play_next(ctx)


async def play_next(ctx):
    if bot.queue.is_empty():
        await ctx.send("queue empty bye") #EMPTY QUEUE
        await leave(ctx)
    else:
        song = bot.queue.dequeue()
        filename = song.title
        voice_channel = ctx.message.guild.voice_client
        voice_channel.play(discord.FFmpegPCMAudio(executable="C:\\ffmpeg\\ffmpeg.exe",
                                                  source=filename))
        await ctx.send('**Now playing:** {}'.format(filename))


@bot.command(name='join', help='Tells the bot to join the voice channel')
async def join(ctx):
    if not ctx.message.author.voice:
        await ctx.send("{} is not connected to a voice channel".format(ctx.message.author.name))
        return
    else:
        channel = ctx.message.author.voice.channel
    await channel.connect()


@bot.command(name='pause', help='This command pauses the song')
async def pause(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_playing():
        voice_client.pause()
    else:
        await ctx.send("The bot is not playing anything at the moment.")


@bot.command(name='resume', help='Resumes the song')
async def resume(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_paused():
        voice_client.resume()
    else:
        await ctx.send("The bot was not playing anything before this. Use play command")


@bot.command(name='leave', help='To make the bot leave the voice channel')
async def leave(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_connected():
        await voice_client.disconnect()
        bot.queue = Queue()  # Clear the queue when leaving
    else:
        await ctx.send("The bot is not connected to a voice channel.")


@bot.command(name='stop', help='Stops the song')
async def stop(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_playing() or voice_client.is_paused():
        voice_client.stop()
        bot.queue = Queue()  # Clear the queue when stopping
    else:
        await ctx.send("The bot is not playing anything at the moment.")


@bot.command(name='queue', help='Displays the current song queue')
async def display_queue(ctx):
    if bot.queue.is_empty():
        await ctx.send("The queue is empty.")
    else:
        queue_str = "\n".join(song.title for song in bot.queue.queue)
        await ctx.send("**Current Queue:**\n{}".format(queue_str))


@bot.command(name='add', help='Adds numbers together')
async def addition(a, b):
    pass

if __name__ == "__main__":
    bot.queue = Queue()
    bot.run(DISCORD_TOKEN)
