import bot_token as d_token
import discord
from discord.ext import commands
from discord import voice_client
import sys
import requests
import json
import re


def generate_audio(text):
    #オーディオファイル生成メソッド
    result = savefile(audio_file, text, SPEAKER)
    if result != 200:
        return 'Error'
    return

TOKEN = d_token.discord_token
client = commands.Bot(command_prefix='//')
audio_file = r'./audio/result.wav'
ffmpeg_exe = r'./ffmpeg/bin/ffmpeg.exe'
SPEAKER = 1
is_read_long_sentence = False
url_pattern = 'https?://[\w/:%#\$&\?\(\)~\.=\+\-]+'
replace_letters = {
    '#' : 'シャープ',
    '$' : 'ドル',
    '%' : 'パーセント',
    '.' : '',
    '/' : '',
    '?' : '',
    '\\' : '',
    ':' : '',
    '\"' : '',
    '\'' : '',
    '!' : ''
    }

text_channel = None
voice_client = None
is_joined = False
looping = False


@client.event
async def on_ready():
    print('Launch successful')

@client.command()
async def connect(ctx):
    print('Connected voice channel')
    if not ctx.message.guild:
        return

    if ctx.author.voice is None:
        await ctx.send('あんたボイスチャンネルに接続してへんで')
    elif ctx.guild.voice_client:
        if ctx.author.voice.channel == ctx.guild.voice_client.channel:
            await ctx.send('もうおるで')
        else:
            voice_channel = ctx.author.voice.channel
            await ctx.voice_client.move_to(voice_channel)
    else:
        global text_channel
        global voice_client
        global is_joined
        text_channel = ctx.channel
        voice_channel = ctx.author.voice.channel
        is_joined = True
        await voice_channel.connect()
        voice_client = ctx.guild.voice_client

@client.command()
async def join(ctx):
    await connect(ctx)

@client.command()
async def disconnect(ctx):
    print('Disconnected voice channel')
    if not ctx.message.guild:
        return

    if ctx.voice_client is None:
        await ctx.send('ワイまだボイスチャンネルにおらんで')
    else:
        global text_channel
        global is_joined
        text_channel = None
        is_joined = False
        await ctx.voice_client.disconnect()


@client.command()
async def leave(ctx):
    await disconnect(ctx)

@client.command()
async def shutdown(ctx):
    if is_joined:
        await leave(ctx)
    await client.logout()
    print('Process exit by shutdown command')
    await sys.exit(0)

@client.command()
async def switch_read_long(ctx):
    global is_read_long_sentence
    is_read_long_sentence = not is_read_long_sentence
    if is_read_long_sentence:
        await ctx.send('長文の読み上げを有効にしました')
    else:
        await ctx.send('長文の読み上げを無効にしました')

@client.command()
async def srl(ctx):
    await switch_read_long(ctx)

@client.event
async def on_message(message):
    print('Message caught')
    print('  ' + str(message.author.name) + ' : ' + message.content)
    await client.process_commands(message)
    if not is_joined or message.author.bot:
        return

    if message.channel is text_channel and voice_client:

        received_text = message.content
        if received_text.startswith('//') or received_text.startswith('!'):
            return

        if re.match(url_pattern, received_text):
            if not voice_client.is_playing():
                voice_client.play(discord.FFmpegPCMAudio(executable=ffmpeg_exe,source=audio_file, options = "-loglevel panic"))
            return

        for l in replace_letters:
            received_text = received_text.replace(l, replace_letters[l])


        if received_text.startswith('-l'):
            received_text = received_text.replace('-l', '')
        elif not is_read_long_sentence and len(received_text) > 40:
            received_text = received_text[0:40] + '以下略'
        print('Generating audio file...')
        result = generate_audio(received_text)
        print('Playing audio file...')
        if result is None:
            voice_client.play(discord.FFmpegPCMAudio(executable=ffmpeg_exe,source=audio_file, options = "-loglevel panic"))
      

def savefile(file_path, read_text, speaker):
    print(read_text)
    url = 'http://localhost:50021/audio_query?text=' + read_text + '&speaker=' + str(speaker)

    res = requests.post(url)
    if res.status_code == 200:
        response_json =  json.loads(res.text)
        url = 'http://localhost:50021/synthesis?speaker=' + str(speaker)
        res = requests.post(url, json.dumps(response_json), headers={'Content-Type':'application/json'})
        if res.status_code == 200:
            with open(file_path,mode='wb') as f:
                f.write(res.content)
        else:
            print('WAV getting filed by status ' + str(res.status_code))
            print(res.text)
    else:
        print('JSON getting filed by status ' + str(res.status_code))
        print(res.text)
    return res.status_code



client.run(TOKEN)
