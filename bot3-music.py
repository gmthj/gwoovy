import discord
from discord.ext import commands, tasks
from discord.ext.commands import Greedy
from discord.utils import get
from discord import app_commands

from typing import Literal, Optional
import os
from random import shuffle, choice as rchoice, random as randfloat, randint
import subprocess
import asyncio
import yt_dlp
from datetime import datetime
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import requests
from bs4 import BeautifulSoup
import json
import psycopg2
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from typing import Optional
import googleapiclient.discovery
from dotenv import load_dotenv

import bot_config3 as bot_config

load_dotenv()

bot_version = bot_config.bot_version_number
try:  # Server side config
    dummy = os.environ['DUMMY']
    conndb = os.environ['DATABASE_URL']
    command_prefix = '-'
except:  # Local config
    conndb = bot_config.db_creds
    bot_version += 'beta'
    command_prefix = '_'
bot_version += bot_config.bot_version_message


YOUTUBE_DEVELOPER_KEY = os.environ['YOUTUBE_DEV_API_KEY']

AUTO_LEAVE_TIME = 5 #minutes

# Leech free zone, Cock and Balls inc, Express, Banger, 3rfq2f
control_room_ids = {890253956616433665:797770451971342417, 905354625518034956:894876712784003072, 905354087820853280:770817814780051477, 924350814196215808:823981249344962611, 904777855882367057:875026341563629568} # control-room-channel : target server

queues = {} # dict of string guildids : list of dicts of string queue items ; {'213453454543424' : [{'filesavename':'song1.mp3', 'time_seconds':230, 'link':'https://youtube.com/IvY7vswVy/', 'title':'song3'}, {'filesavename':'song3.mp3', 'time_seconds':20, 'link':'https://youtube.com/IvY7vswVy/', 'title':'song3'}], '654321234543212345': [{'filesavename':'song1.mp3', 'time_seconds':230, 'link':'https://youtube.com/IvY7vswVy/', 'title':'song3'}, {'filesavename':'song1.mp3', 'time_seconds':230, 'link':'https://youtube.com/IvY7vswVy/', 'title':'song3'}]}
currently_playing = {} # dict of string guildids : dict of current song ; {'234543212345432' : {'filesavename':'song1.mp3', 'time_seconds':230, 'start_time':datetime obj, 'pause_time':datetime obj, 'pause_seconds':0, 'link':'https://youtube.com/IvY7vswVy/', 'title':'song3'}, '54323454322345432' : {'filesavename':'song1.mp3', 'time_seconds':230, 'start_time':datetime obj, 'pause_time':None, 'pause_seconds':35, 'link':'https://youtube.com/IvY7vswVy/', 'title':'song3'}}
loops = {} # dict of string guildids : boolean ; {'234543212345432' : True, '54323454322345432' : False}
autoplays = {} # dict of string guildids : boolean ; {'234543212345432' : True, '54323454322345432' : False}
history = {} # dict of string guildids : list of string song names ; {'213453454543424' : ['song1.mp3', 'youtube.com/wefwe']}

intents = discord.Intents.all()
intents.members = True
intents.presences = True
client = commands.Bot(command_prefix=commands.when_mentioned_or(command_prefix), intents=intents, case_insensitive=True)


auth_manager = SpotifyClientCredentials(client_id = os.environ['SPOTIFY_CLIENT_ID'], client_secret = os.environ['SPOTIFY_CLIENT_SECRET'])
sp = spotipy.Spotify(auth_manager=auth_manager)
print('[1/4]', 'spotify ready')


gauth = GoogleAuth()
# gauth.LocalWebserverAuth() # client_secrets.json need to be in the same directory as the script
# gauth.SaveCredentialsFile("gdrive_creds.txt")
gauth.LoadCredentialsFile("gdrive_creds.txt")
drive = GoogleDrive(gauth)
print('[2/4]', 'Google drive auth ready')


statuses = ['-help', '/help']


emojiforward = '▶️'
emojiback = '◀️'
emojigreensquare = '🟩'
emojiredsquare = '🟥'
emoji1 = '1️⃣'
emoji2 = '2️⃣'
emoji3 = '3️⃣'
emoji1finger = '☝️'
emoji2finger = '✌️'
emoji3finger = '👌'
emojirefresh = '🔄'


# filetypes
# mp3 - audio/mpeg
# wav - audio/x-wav
# mp4 - video/mp4
# mov - video/quicktime
# mkv - video/x-matroska
# webm - video/webm
# png - image/png
# jpg/jpeg - image/jpeg
# gif - image/gif
filetypes = ['audio/mpeg', 'video/mp4', 'video/quicktime', 'video/x-matroska', 'video/webm', 'audio/x-wav']
validfiletypes = '**mp3, mp4, mov, mkv, webm, wav**'


embed_help = discord.Embed(title=f'Gwoovy commands',colour=discord.Colour.purple(), description=f'prefix: `{command_prefix}`\n\
★ old Groovy\'s premium features')
embed_help.add_field(name='Music 🎵', value=bot_config.commands_music, inline=False)
embed_help.add_field(name='Queue control 🎮', value=bot_config.commands_queue, inline=False)
embed_help.add_field(name='Save queue 💾', value=bot_config.commands_save_queue, inline=False)
embed_help.add_field(name='Bot control 🤖', value=bot_config.commands_control, inline=False)
embed_help.add_field(name='Others 🙃', value=bot_config.commands_others, inline=False)
embed_help.add_field(name='Others you can\'t use 🛡️', value=bot_config.commands_others2, inline=False)
embed_help.set_footer(text=f'Version: {bot_version}')



def seconds_to_strHMS(totalsecs):
    hours = totalsecs // 3600
    totalsecs %= 3600
    mins = totalsecs // 60
    totalsecs %= 60
    seconds = totalsecs

    hours, mins, seconds = str(hours), str(mins), str(seconds)
    hours = '0'+hours if len(hours) == 1 else hours
    mins = '0'+mins if len(mins) == 1 else mins
    seconds = '0'+seconds if len(seconds) == 1 else seconds
    str_time = f'{hours}:{mins}:{seconds}'
    return str_time

def get_length(filename):
    result = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                             "format=duration", "-of",
                             "default=noprint_wrappers=1:nokey=1", filename],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT)
    return int(float(result.stdout)) #return duration in seconds

def timeline(current, total):
    length = 20
    if total > 0:
        if total >= current:
            percentage = current/total
            first_half_length = int(percentage*length)
        else:
            print('timeline error: current time more than total time')
            first_half_length = length
        second_half_length = length-first_half_length
        # line = '|' + first_half_length*'-' + '○' + second_half_length*'-' + '|'
        line = first_half_length*'▬' + '●' + second_half_length*'▬'
    else:
        line = 'LIVE: ' + length*'▬' + '●'
    return line


def initialise_db():
    db = psycopg2.connect(conndb)
    cursor = db.cursor()
    # cursor.execute('DROP TABLE IF EXISTS queues')
    cursor.execute('''CREATE TABLE IF NOT EXISTS queues(
    guildid BIGINT,
    id BIGINT,
    name TEXT,
    queue_name TEXT,
    queue TEXT
    )''')
    db.commit()
    cursor.close()
    db.close()


# https://open.spotify.com/playlist/5DVr2ew1gnYOcmcEeT3PjR?si=f22c383b5fa747c2
# https://open.spotify.com/track/1ZeVIrCWzEmsJexkrgvjFv?si=24816581f83c4398
# https://open.spotify.com/album/1zsfTBbGALW0bzwjKiDFvb?si=vG3GbPzASrmRzcxqZ_zXuA
# https://www.youtube.com/watch?v=owrhKIN3Y90&list=PLu5_j_8_fpMgJEFl5xcLX0suUSrVz1yRq&index=12
# https://youtube.com/playlist?list=PL2nBn3wnvOO_FGeqeUYZf8jrUTME62Dun
async def youtube_download(link, msg, ctx):
    try:
        videos_info_output = []
        playlist = False
        spotify_playlist = False
        embed = msg.embeds[0]
        ydl = yt_dlp.YoutubeDL({'format': 'bestaudio/best', "cookiefile": "cookies.txt"})
        with ydl:
            if ' ' not in link and 'youtube.com' in link or 'youtu.be' in link:
                if '/playlist' in link:
                    result = ydl.extract_info(f'{link}', download=False)
                    playlist = True
                else:
                    link = youtube_link_cleaner(link)
                    result = ydl.extract_info(f'{link}', download=False)
            elif ' ' not in link and 'soundcloud.com' in link:
                result = ydl.extract_info(f'{link}', download=False)
                if '/sets' in link:
                    playlist = True
            elif ' ' not in link and 'coub.com' in link:
                result = ydl.extract_info(f'{link}', download=False)
            elif ' ' not in link and 'spotify.com/track/' in link:
                link = link[:-1] if link[-1] == '/' else link
                track_id = link.split('/')[-1]
                track_info = sp.track(track_id)
                name = track_info['name']
                album = track_info['album']['name']
                artist = track_info['album']['artists'][0]['name']
                new_search = f'{name} {artist} {album}'
                embed = embed.set_footer(text=f'spotify track: getting 1/1')
                await msg.edit(embed=embed)
                result = ydl.extract_info(f'ytsearch:{new_search}', download=False)
            elif ' ' not in link and ('spotify.com/playlist/' in link or 'spotify.com/album/' in link):
                global queues
                guild = ctx.guild
                text_channel = ctx.channel
                guildid = str(ctx.guild.id)
                spotify_playlist_album = ''
                if 'spotify.com/playlist/' in link:
                    spotify_playlist_album = 'playlist'
                    link = link[:-1] if link[-1] == '/' else link
                    playlist_id = link.split('/')[-1]
                    playlist_info = sp.playlist_tracks(playlist_id)
                    tracks = playlist_info['tracks']['items']
                elif 'spotify.com/album/' in link:
                    spotify_playlist_album = 'album'
                    album_info = sp.album(link)
                    tracks = album_info['tracks']['items']
                total_tracks = len(tracks)
                videos = []
                start_dt = datetime.now().replace(microsecond=0)
                spotify_playlist = True
                spotify_playlist_count = 0
                for track_info in tracks:
                    try:
                        if spotify_playlist_album == 'playlist':
                            name = track_info['track']['name']
                            album = track_info['track']['album']['name']
                            artist = track_info['track']['album']['artists'][0]['name']
                            # release_date = track_info['track']['album']['release_date']
                            # year = release_date.split('-')[0]
                            # new_search = f'{name} {artist} {album} {year} fficial'
                        elif spotify_playlist_album == 'album':
                            name = track_info['name']
                            album = album_info['name']
                            artist = album_info['artists'][0]['name']
                        new_search = f'{name} {artist} {album}'
                        result = ydl.extract_info(f'ytsearch:{new_search}', download=False)
                        if 'entries' in result:
                            video = result['entries'][0]
                        else:
                            video = result
                        filename = url_from_ytvideo_formats(video['formats'])
                        title = video['title']
                        duration = int(video['duration']) or 1
                        url = video['webpage_url']
                        queue_item = {'filesavename':filename, 'time_seconds':duration, 'link':url, 'title':title}
                        if guildid not in queues:
                            queues[guildid] = []
                        queues[guildid].append(queue_item)
                        videos.append(video)

                        spotify_playlist_count += 1
                        current_dt = datetime.now().replace(microsecond=0)
                        embed = embed.set_footer(text=f'spotify {spotify_playlist_album}: queued {spotify_playlist_count}/{total_tracks} time elapsed: {seconds_to_strHMS((current_dt-start_dt).seconds)}')
                        await msg.edit(embed=embed)
                        if spotify_playlist_count == 1:
                            voice_client = guild.voice_client
                            if not voice_client:
                                await join(ctx)
                                await play2(guild, text_channel)
                            elif not voice_client.is_playing() and not voice_client.is_paused():
                                await play2(guild, text_channel)
                    except Exception as e:
                        print('spotify playlist/album track failed: ', e)
            else:
                if link.startswith('http'):
                    result = ydl.extract_info(f'{link}', download=False)
                else:
                    result = ydl.extract_info(f'ytsearch:{link}', download=False)

        if spotify_playlist == True:
            videos = videos
        elif 'entries' in result:
            if playlist == True:
                videos = result['entries']
            else:
                videos = [result['entries'][0]]
        else:
            videos = [result]

        for video in videos:
            filename = url_from_ytvideo_formats(video['formats'])
            title = video['title']
            duration = int(video['duration']) or 1
            url = video['webpage_url']
            videos_info_output.append([filename, duration, url, title])

        return videos_info_output, spotify_playlist
    except Exception as e:
        print('ytdl err ', e)
        try:
            await ctx.send(str('something went wrong: '+str(e)))
            await report(ctx, text=e)
        except Exception as e:
            print('ytdl ex err ', e)
        videos_info_output = [[None, 0, None, None]]
        return videos_info_output, False

async def youtube_download_interaction(link, embed, interaction):
    try:
        videos_info_output = []
        playlist = False
        spotify_playlist = False
        ydl = yt_dlp.YoutubeDL({'format': 'bestaudio/best', "cookiefile": "cookies.txt"})
        with ydl:
            if ' ' not in link and 'youtube.com' in link or 'youtu.be' in link:
                if '/playlist' in link:
                    result = ydl.extract_info(f'{link}', download=False)
                    playlist = True
                else:
                    link = youtube_link_cleaner(link)
                    result = ydl.extract_info(f'{link}', download=False)
            elif ' ' not in link and 'soundcloud.com' in link:
                result = ydl.extract_info(f'{link}', download=False)
                if '/sets' in link:
                    playlist = True
            elif ' ' not in link and 'coub.com' in link:
                result = ydl.extract_info(f'{link}', download=False)
            elif ' ' not in link and 'spotify.com/track/' in link:
                link = link[:-1] if link[-1] == '/' else link
                track_id = link.split('/')[-1]
                track_info = sp.track(track_id)
                name = track_info['name']
                album = track_info['album']['name']
                artist = track_info['album']['artists'][0]['name']
                new_search = f'{name} {artist} {album}'
                embed = embed.set_footer(text=f'spotify track: getting 1/1')
                await interaction.edit_original_response(embed=embed)
                result = ydl.extract_info(f'ytsearch:{new_search}', download=False)
            elif ' ' not in link and ('spotify.com/playlist/' in link or 'spotify.com/album/' in link):
                global queues
                guild = interaction.guild
                text_channel = interaction.channel
                guildid = str(interaction.guild.id)
                spotify_playlist_album = ''
                if 'spotify.com/playlist/' in link:
                    spotify_playlist_album = 'playlist'
                    link = link[:-1] if link[-1] == '/' else link
                    playlist_id = link.split('/')[-1]
                    playlist_info = sp.playlist_tracks(playlist_id)
                    tracks = playlist_info['tracks']['items']
                elif 'spotify.com/album/' in link:
                    spotify_playlist_album = 'album'
                    album_info = sp.album(link)
                    tracks = album_info['tracks']['items']
                total_tracks = len(tracks)
                videos = []
                start_dt = datetime.now().replace(microsecond=0)
                spotify_playlist = True
                spotify_playlist_count = 0
                for track_info in tracks:
                    try:
                        if spotify_playlist_album == 'playlist':
                            name = track_info['track']['name']
                            album = track_info['track']['album']['name']
                            artist = track_info['track']['album']['artists'][0]['name']
                            # release_date = track_info['track']['album']['release_date']
                            # year = release_date.split('-')[0]
                            # new_search = f'{name} {artist} {album} {year} fficial'
                        elif spotify_playlist_album == 'album':
                            name = track_info['name']
                            album = album_info['name']
                            artist = album_info['artists'][0]['name']
                        new_search = f'{name} {artist} {album}'
                        result = ydl.extract_info(f'ytsearch:{new_search}', download=False)
                        if 'entries' in result:
                            video = result['entries'][0]
                        else:
                            video = result
                        filename = url_from_ytvideo_formats(video['formats'])
                        title = video['title']
                        duration = int(video['duration']) or 1
                        url = video['webpage_url']
                        queue_item = {'filesavename':filename, 'time_seconds':duration, 'link':url, 'title':title}
                        if guildid not in queues:
                            queues[guildid] = []
                        queues[guildid].append(queue_item)
                        videos.append(video)

                        spotify_playlist_count += 1
                        current_dt = datetime.now().replace(microsecond=0)
                        embed = embed.set_footer(text=f'spotify {spotify_playlist_album}: queued {spotify_playlist_count}/{total_tracks} time elapsed: {seconds_to_strHMS((current_dt-start_dt).seconds)}')
                        await interaction.edit_original_response(embed=embed)
                        if spotify_playlist_count == 1:
                            voice_client = guild.voice_client
                            if not voice_client:
                                await join_2(interaction)
                                await play2(guild, text_channel)
                            elif not voice_client.is_playing() and not voice_client.is_paused():
                                await play2(guild, text_channel)
                    except Exception as e:
                        print('spotify playlist/album track failed: ', e)
            else:
                if link.startswith('http'):
                    result = ydl.extract_info(f'{link}', download=False)
                else:
                    result = ydl.extract_info(f'ytsearch:{link}', download=False)

        if spotify_playlist == True:
            videos = videos
        elif 'entries' in result:
            if playlist == True:
                videos = result['entries']
            else:
                videos = [result['entries'][0]]
        else:
            videos = [result]

        for video in videos:
            filename = url_from_ytvideo_formats(video['formats'])
            title = video['title']
            duration = int(video['duration']) or 1
            url = video['webpage_url']
            videos_info_output.append([filename, duration, url, title])

        return videos_info_output, spotify_playlist
    except Exception as e:
        print('ytdl err ', e)
        try:
            await interaction.edit_original_response(str('something went wrong: '+str(e)))
            await report(interaction, text=e)
        except Exception as e:
            print('ytdl ex err ', e)
        videos_info_output = [[None, 0, None, None]]
        return videos_info_output, False

def url_from_ytvideo_formats(formats_list):
    for format in formats_list:
        if 'googlevideo.com/' in format['url']:
            return format['url']
    return formats_list[0]['url']

def youtube_link_cleaner(link):
    if '?' in link and '&' in link:
        end_index = 0
        v_index = link.index('v=')
        and_indexs = [i for i, c in enumerate(link) if c == '&']
        and_indexs.append(len(link))
        for i in and_indexs[::-1]:
            if i > v_index:
                end_index = i
        if end_index == 0:
            return link
        else:
            link = 'https://www.youtube.com/watch?' + link[v_index:end_index]
    return link
    # https://www.youtube.com/watch?v=owrhKIN3Y90&list=PLu5_j_8_fpMgJEFl5xcLX0suUSrVz1yRq&index=12


def init_queues():
    for guild in client.guilds:
        guildid = str(guild.id)
        if not guildid in currently_playing:
            currently_playing[guildid] = {'filesavename':'', 'time_seconds':0, 'start_time':None, 'pause_time':None, 'pause_seconds':0, 'link':'', 'title':''}
        if not guildid in loops:
            loops[guildid] = False
        if not guildid in autoplays:
            autoplays[guildid] = False
        if not guildid in queues:
            queues[guildid] = []
        if not guildid in history:
            history[guildid] = []

@client.event
async def on_ready():
    print('[3/4]', 'running ', client.user)
    initialise_db()
    print('[4/4]', 'database ready')
    init_queues()
    rolling_status_loop.start(statuses)

    logs_channel = await client.fetch_channel(bot_config.logs_channel)
    await logs_channel.send('ready '+bot_version)
    # await client.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name='-help'))

@client.event
async def on_guild_join(guild):
    msg = '**Gwoovy bot**\ntype **-help** or **/help** for a list of commands'
    sys_channel = guild.system_channel #getting system channel
    if sys_channel.permissions_for(guild.me).send_messages: #making sure you have permissions
        await sys_channel.send(msg)
    else:
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                await channel.send(msg)
                break
    logs_channel = await client.fetch_channel(bot_config.logs_channel)
    init_queues()
    embed = discord.Embed(title=f'Joined new server: {guild.name}',colour=discord.Colour.purple(), description='reinitialised queues')
    await logs_channel.send(embed=embed)

@client.event
async def on_raw_reaction_add(payload):
    try:
        channel = await client.fetch_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        user = await client.fetch_user(payload.user_id)
        reaction = get(message.reactions, emoji=payload.emoji.name)
        if user == client.user:
            return
        elif payload.emoji.name == "🔄" and message.reactions[0].me: #check if emoji and bot has also reacted
            await message.edit(embed=embed_help)
            await reaction.remove(user)
        # else:
        #     print('emoji not recog and messgae not roll')
    except Exception as e:
        print('react error')
        user = await client.fetch_user(payload.user_id)
        print(e, user)

@client.command()
async def ping(ctx):
    await ctx.channel.send(f'pong!\n\
**Latency**: {client.latency*1000:.0f} ms\n\
**Version**: {bot_version}')

@client.tree.command(name='ping')
async def ping_(interaction: discord.Interaction):
    """pong"""
    await interaction.response.send_message(f'pong!\n\
**Latency**: {client.latency*1000:.0f} ms\n\
**Version**: {bot_version}')

client.remove_command('help')
@client.command()
async def help(ctx):
    msg = await ctx.send(embed=embed_help)
    await msg.add_reaction(emojirefresh)

@client.tree.command(name='help')
async def help_(interaction: discord.Interaction):
    """Help message with list of commands"""
    # await interaction.response.defer()
    await interaction.response.send_message(embed=embed_help)
    # await msg.add_reaction(emojirefresh)

@client.command()
async def report(ctx, *, text=None):
    logs_channel = await client.fetch_channel(bot_config.logs_channel)
    await logs_channel.send(ctx.message.author)
    await logs_channel.send(ctx.message.content)
    if text:
        await logs_channel.send(text)
    await logs_channel.send(ctx.message.jump_url)
    await ctx.send('report made')

@client.command()
@commands.is_owner()
async def listdir(ctx,*,dir=None):
    startdir = os.getcwd()
    if dir:
        dir = '/' + dir.replace(' ','/')
        os.chdir(os.getcwd()+dir)
    files = ''
    folders = ''
    dir_files = os.listdir()
    dir_files.sort(key=lambda f: os.path.splitext(f)[::-1])
    for file in dir_files:
        if '.' in file:
            files += '|--' + file  + '\n'
        elif '.' not in file:
            folders += file + '\n'
    os.chdir(startdir)
    try:
        await ctx.channel.send(folders+files)
    except Exception:
        with open('listdir.txt', 'w') as f:
            f.write(f'{folders+files}')
        f2 = open('listdir.txt','rb')
        text = discord.File(f2)
        f2.close()
        await ctx.channel.send('too many characters', file=text)



@client.command(aliases=['j','jion'])
async def join(ctx):
    if ctx.channel.id in control_room_ids:
        ctx.guild = client.get_guild(control_room_ids[ctx.channel.id])
        voice_client = ctx.guild.voice_client
        try:
            channel = None
            for vc in ctx.guild.voice_channels:
                print(vc.members)
                if vc.members != []:
                    channel = vc
                    break
            if channel:
                if not voice_client:
                    await channel.connect()
                    await ctx.send(f'joined {channel}')
                elif voice_client and voice_client.channel != channel:
                    await voice_client.move_to(channel)
                    await ctx.send(f'joined (moved to) {channel}')
                # else:
                #     await ctx.send("already in the same voice channel as you")
            else:
                await ctx.send('no one detected in any vc')
        except Exception as e:
            await ctx.send("joining error")
            await ctx.send(e)
            print(e)
    elif not ctx.message.author.voice:
        message = f'{ctx.message.author} join a voice channel to use this command'
        embed_join = discord.Embed(colour=discord.Colour.purple(), description=message)
        await ctx.send(embed=embed_join)
    else:
        channel = ctx.message.author.voice.channel
        voice_client = ctx.guild.voice_client
        try:
            guildid = str(ctx.guild.id)
            # loops[guildid] = False
            # if not channel.is_connected()
            if not voice_client:
                await channel.connect()
            elif voice_client and voice_client.channel != channel:
                await voice_client.move_to(channel)
            # else:
            #     await ctx.send("already in the same voice channel as you")
        except Exception as e:
            await ctx.send("joining error")
            await ctx.send(e)
            print(e)

@client.tree.command(name='join')
async def join_(interaction: discord.Interaction):
    """Bot joins your voice channel"""
    print('joinse')
    if interaction.channel.id in control_room_ids:
        interaction.guild = client.get_guild(control_room_ids[interaction.channel.id])
        voice_client = interaction.guild.voice_client
        try:
            channel = None
            for vc in interaction.guild.voice_channels:
                print(vc.members)
                if vc.members != []:
                    channel = vc
                    break
            if channel:
                if not voice_client:
                    await channel.connect()
                    await interaction.response.send_message(f'joined {channel}')
                elif voice_client and voice_client.channel != channel:
                    await voice_client.move_to(channel)
                    await interaction.response.send_message(f'joined (moved to) {channel}')
                # else:
                #     await ctx.send("already in the same voice channel as you")
            else:
                await interaction.response.send_message('no one detected in any vc')
        except Exception as e:
            await interaction.response.send_message(f"/joining error {e}")
            print(e)
    elif not interaction.user.voice:
        message = f'{interaction.user} join a voice channel to use this command'
        embed_join = discord.Embed(colour=discord.Colour.purple(), description=message)
        await interaction.response.send_message(embed=embed_join)
    else:
        channel = interaction.user.voice.channel
        voice_client = interaction.guild.voice_client
        try:
            # guildid = str(interaction.guild.id)
            # loops[guildid] = False
            # if not channel.is_connected()
            if not voice_client:
                await channel.connect()
                await interaction.response.send_message(f'joined {channel}')
            elif voice_client and voice_client.channel != channel:
                await voice_client.move_to(channel)
                await interaction.response.send_message(f'joined (moved to) {channel}')
            # else:
            #     await interaction.response.send_message("already in the same voice channel as you")
        except Exception as e:
            await interaction.response.send_message(f"/joining error {e}")
            print(e)

async def join_2(interaction: discord.Interaction):
    if interaction.channel.id in control_room_ids:
        interaction.guild = client.get_guild(control_room_ids[interaction.channel.id])
        voice_client = interaction.guild.voice_client
        try:
            channel = None
            for vc in interaction.guild.voice_channels:
                print(vc.members)
                if vc.members != []:
                    channel = vc
                    break
            if channel:
                if not voice_client:
                    await channel.connect()
                    await interaction.channel.send(f'joined {channel}')
                elif voice_client and voice_client.channel != channel:
                    await voice_client.move_to(channel)
                    await interaction.channel.send(f'joined (moved to) {channel}')
                # else:
                #     await ctx.send("already in the same voice channel as you")
            else:
                await interaction.channel.send('no one detected in any vc')
        except Exception as e:
            await interaction.channel.send(f"/joining error {e}")
            print(e)
    elif not interaction.user.voice:
        message = f'{interaction.user} join a voice channel to use this command'
        embed_join = discord.Embed(colour=discord.Colour.purple(), description=message)
        await interaction.channel.send(embed=embed_join)
    else:
        channel = interaction.user.voice.channel
        voice_client = interaction.guild.voice_client
        try:
            # guildid = str(interaction.guild.id)
            # loops[guildid] = False
            # if not channel.is_connected()
            if not voice_client:
                await channel.connect()
                # await interaction.channel.send(f'joined {channel}')
            elif voice_client and voice_client.channel != channel:
                await voice_client.move_to(channel)
                # await interaction.channel.send(f'joined (moved to) {channel}')
            # else:
            #     await interaction.channel.send("already in the same voice channel as you")
        except Exception as e:
            await interaction.channel.send(f"/joining error {e}")
            print(e)

@client.command(aliases=['lv','dc','disconnect','fuckoff'])
async def leave(ctx):
    global queues
    if ctx.channel.id in control_room_ids:
        ctx.guild = client.get_guild(control_room_ids[ctx.channel.id])
    guildid = str(ctx.guild.id)
    voice_client = ctx.guild.voice_client
    if voice_client and voice_client.is_connected():
        if queues[guildid] != []:
            await clear2(ctx)
        await voice_client.disconnect()
        embed_leave = discord.Embed(colour=discord.Colour.purple(), description='Bye👋')
        await ctx.send(embed=embed_leave)
    else:
        await ctx.send("I am not in any voice channel")

@client.tree.command(name='leave')
async def leave_(interaction: discord.Interaction):
    """Bot leaves your voice channel and queue is cleared"""
    global queues
    if interaction.channel.id in control_room_ids:
        interaction.guild = client.get_guild(control_room_ids[interaction.channel.id])
    guildid = str(interaction.guild.id)
    voice_client = interaction.guild.voice_client
    if voice_client and voice_client.is_connected():
        if queues[guildid] != []:
            await clear2(interaction) #ctx
        await voice_client.disconnect()
        embed_leave = discord.Embed(colour=discord.Colour.purple(), description='Bye👋')
        await interaction.response.send_message(embed=embed_leave)
    else:
        await interaction.response.send_message("I am not in any voice channel")

@client.command(aliases=['p'])
async def play(ctx, *, text=None):
    global queues
    try:
        if ctx.channel.id in control_room_ids:
            ctx.guild = client.get_guild(control_room_ids[ctx.channel.id])
        elif not ctx.message.author.voice:
            message = f'{ctx.message.author} join a voice channel to use this command'
            embed_playjoin = discord.Embed(colour=discord.Colour.purple(), description=message)
            await ctx.send(embed=embed_playjoin)
            return
        guild = ctx.guild
        text_channel = ctx.channel
        guildid = str(ctx.guild.id)

        attachment = ctx.message.attachments
        spotify_playlist = False
        filesavename = None
        time_seconds = 0
        link = None
        title = None
        msg = None
        if attachment:
            if attachment[0].content_type not in filetypes:
                message = f'invalid file type: "{attachment[0].content_type}"; use {validfiletypes}'
                embed_attachment = discord.Embed(colour=discord.Colour.purple(), description=message)
                await ctx.send(embed=embed_attachment)
            else:
                filesavename = attachment[0].filename
                await attachment[0].save(filesavename)
                time_seconds = get_length(filesavename)
                link = ctx.message.jump_url # attachment[0].url -actual file download
                title = filesavename
                videos_info_output = [[filesavename, time_seconds, link, title]]
        elif text:
            # print(text)
            if 'fmstream.org' in text:
                filesavename = text
                time_seconds = 0
                link = text
                title = text
                videos_info_output = [[filesavename, time_seconds, link, title]]
            else:
                message = f'getting track'
                embed_ytplay = discord.Embed(colour=discord.Colour.purple(), description=message)
                msg = await ctx.send(embed=embed_ytplay)

                videos_info_output, spotify_playlist = await youtube_download(text, msg, ctx)
                number_of_videos = len(videos_info_output)
                if number_of_videos <= 0:
                    message = f'error getting {text}: nothing found'
                elif number_of_videos == 1:
                    if videos_info_output[0][0] is None:
                        message = f'error getting {text}'
                    else:
                        message = f'successfully got track'
                else:
                    message = f'successfully got {number_of_videos} tracks'
                embed_ytplay = discord.Embed(colour=discord.Colour.purple(), description=message)
                await msg.edit(embed=embed_ytplay)
        else:
            message = f'No attachment found and no input given'
            embed_noplay = discord.Embed(colour=discord.Colour.purple(), description=message)
            await ctx.send(embed=embed_noplay)
            return


        if spotify_playlist:
            queue_count = len(videos_info_output)
            message = f'Queued {queue_count} items'
        else:
            queue_count = 0
            for video in videos_info_output:
                filesavename, time_seconds, link, title = video
                if filesavename and time_seconds >= 0 and link and title:
                    queue_item = {'filesavename':filesavename, 'time_seconds':time_seconds, 'link':link, 'title':title}
                    if guildid not in queues:
                        queues[guildid] = [queue_item]
                        message=f'Queued {title}'
                        queue_count += 1
                    elif queues[guildid] != [] and queues[guildid][-1]['link'] == link and queues[guildid][-1]['title'] == title:
                        message = f'{title} is already the most recently queued item. Nothing added to the queue. You can use {command_prefix}loop to loop the current track.'
                    else:
                        queues[guildid].append(queue_item)
                        message=f'Queued {title}'
                        queue_count += 1

            if queue_count > 1:
                message = f'Queued {queue_count} items'

        embed_play = discord.Embed(colour=discord.Colour.purple(), description=message)
        # embed_play.set_footer(text='if QUEUED and nothing happens, type -fp')
        if msg:
            await msg.edit(embed=embed_play, delete_after=5*60)
        else:
            msg = await ctx.send(embed=embed_play, delete_after=5*60)
        if queue_count > 0:
            voice_client = guild.voice_client
            if not voice_client:
                # # all i want for christmas plug
                # #all i want for xmas, last xmas, its begining to look a lot like xmas
                # xmas_songs = ['https://www.youtube.com/watch?v=yXQViqx6GMY', 'https://www.youtube.com/watch?v=E8gmARGvPlI', 'https://www.youtube.com/watch?v=QJ5DOWPGxwg']
                # all_i_want_for_christmas, spotify_playlist = await youtube_download(rchoice(xmas_songs), msg, ctx)
                # filesavename, time_seconds, link, title = all_i_want_for_christmas[0]
                # xmas_queue_item = {'filesavename':filesavename, 'time_seconds':time_seconds, 'link':link, 'title':title}
                # # print(xmas_queue_item)
                # # if queue_count > 0 and 'Mariah Carey - All I Want For Christmas Is You (Official Video)' not in [queue_item['title'] for queue_item in queues[guildid]] and randfloat()>0.6:
                # if queue_count > 0 and xmas_queue_item['title'] not in [queue_item['title'] for queue_item in queues[guildid]] and randfloat()>0.1:
                #     queues[guildid].append(xmas_queue_item)
                #     message = rchoice(['Christmas time 🎅', 'Christmas time 🎄'])
                #     embed_xmas = discord.Embed(colour=rchoice([discord.Colour.red(), discord.Colour.green()]), description=message)
                #     await ctx.send(embed=embed_xmas)
                #     print('play command', queues)
                # # all i want for christmas plug
                await join(ctx)
                await play2(guild, text_channel)
            elif not voice_client.is_playing() and not voice_client.is_paused():
                await play2(guild, text_channel)
    except Exception as e:
        print('err play command', e)
        if queues[guildid] != []:
            print('trying to forceplay')
            await forceplay(ctx)

@client.tree.command(name='play')
@app_commands.rename(text = 'input')
@app_commands.describe(text = 'A link or search term', file = 'An audio file - enter anything into \'input\'')
async def play_(interaction: discord.Interaction, text: str, file: Optional[discord.Attachment] = None):
    """Play a song with a link, search term or audio file"""
    global queues
    try:
        if interaction.channel.id in control_room_ids:
            interaction.guild = client.get_guild(control_room_ids[interaction.channel.id])
        elif not interaction.user.voice:
            message = f'{interaction.user} join a voice channel to use this command'
            embed_playjoin = discord.Embed(colour=discord.Colour.purple(), description=message)
            await interaction.response.send_message(embed=embed_playjoin)
            return
        guild = interaction.guild
        text_channel = interaction.channel
        guildid = str(interaction.guild.id)

        attachment = file
        spotify_playlist = False
        filesavename = None
        time_seconds = 0
        link = None
        title = None
        msg = None
        if attachment:
            if attachment.content_type not in filetypes:
                message = f'invalid file type: "{attachment.content_type}"; use {validfiletypes}'
                embed_attachment = discord.Embed(colour=discord.Colour.purple(), description=message)
                await interaction.response.send_message(embed=embed_attachment)
            else:
                filesavename = attachment.filename
                await attachment.save(filesavename)
                time_seconds = get_length(filesavename)
                link = interaction.channel.jump_url # attachment.url -actual file download
                title = filesavename
                videos_info_output = [[filesavename, time_seconds, link, title]]
        elif text:
            # print(text)
            if 'fmstream.org' in text:
                filesavename = text
                time_seconds = 0
                link = text
                title = text
                videos_info_output = [[filesavename, time_seconds, link, title]]
            else:
                message = f'getting track'
                embed_ytplay = discord.Embed(colour=discord.Colour.purple(), description=message)
                await interaction.response.send_message(embed=embed_ytplay)
                msg = 1
                print('ytp1')
                videos_info_output, spotify_playlist = await youtube_download_interaction(text, embed_ytplay, interaction)
                print('ytp2')
                number_of_videos = len(videos_info_output)
                if number_of_videos <= 0:
                    message = f'error getting {text}: nothing found'
                elif number_of_videos == 1:
                    if videos_info_output[0][0] is None:
                        message = f'error getting {text}'
                    else:
                        message = f'successfully got track'
                else:
                    message = f'successfully got {number_of_videos} tracks'
                embed_ytplay = discord.Embed(colour=discord.Colour.purple(), description=message)
                await interaction.edit_original_response(embed=embed_ytplay)
        else:
            message = f'No attachment found and no input given'
            embed_noplay = discord.Embed(colour=discord.Colour.purple(), description=message)
            await interaction.response.send_message(embed=embed_noplay)
            return


        if spotify_playlist:
            queue_count = len(videos_info_output)
            message = f'Queued {queue_count} items'
        else:
            queue_count = 0
            for video in videos_info_output:
                filesavename, time_seconds, link, title = video
                if filesavename and time_seconds >= 0 and link and title:
                    queue_item = {'filesavename':filesavename, 'time_seconds':time_seconds, 'link':link, 'title':title}
                    if guildid not in queues:
                        queues[guildid] = [queue_item]
                        message=f'Queued {title}'
                        queue_count += 1
                    elif queues[guildid] != [] and queues[guildid][-1]['link'] == link and queues[guildid][-1]['title'] == title:
                        message = f'{title} is already the most recently queued item. Nothing added to the queue. You can use {command_prefix}loop to loop the current track.'
                    else:
                        queues[guildid].append(queue_item)
                        message=f'Queued {title}'
                        queue_count += 1

            if queue_count > 1:
                message = f'Queued {queue_count} items'

        embed_play = discord.Embed(colour=discord.Colour.purple(), description=message)
        # embed_play.set_footer(text='if QUEUED and nothing happens, type -fp')
        print('ok1')
        if msg:
            await interaction.edit_original_response(embed=embed_play)#, delete_after=5*60)
        else:
            await interaction.response.send_message(embed=embed_play)#, delete_after=5*60)
        print('ok2')
        if queue_count > 0:
            print('ok3')
            voice_client = guild.voice_client
            print('ok4')
            if not voice_client:
                print('ok5')
                # # all i want for christmas plug
                # #all i want for xmas, last xmas, its begining to look a lot like xmas
                # xmas_songs = ['https://www.youtube.com/watch?v=yXQViqx6GMY', 'https://www.youtube.com/watch?v=E8gmARGvPlI', 'https://www.youtube.com/watch?v=QJ5DOWPGxwg']
                # all_i_want_for_christmas, spotify_playlist = await youtube_download(rchoice(xmas_songs), msg, ctx)
                # filesavename, time_seconds, link, title = all_i_want_for_christmas[0]
                # xmas_queue_item = {'filesavename':filesavename, 'time_seconds':time_seconds, 'link':link, 'title':title}
                # # print(xmas_queue_item)
                # # if queue_count > 0 and 'Mariah Carey - All I Want For Christmas Is You (Official Video)' not in [queue_item['title'] for queue_item in queues[guildid]] and randfloat()>0.6:
                # if queue_count > 0 and xmas_queue_item['title'] not in [queue_item['title'] for queue_item in queues[guildid]] and randfloat()>0.1:
                #     queues[guildid].append(xmas_queue_item)
                #     message = rchoice(['Christmas time 🎅', 'Christmas time 🎄'])
                #     embed_xmas = discord.Embed(colour=rchoice([discord.Colour.red(), discord.Colour.green()]), description=message)
                #     await ctx.send(embed=embed_xmas)
                #     print('play command', queues)
                # # all i want for christmas plug
                await join_2(interaction)
                print('ok6')
                await play2(guild, text_channel)
            elif not voice_client.is_playing() and not voice_client.is_paused():
                await play2(guild, text_channel)
    except Exception as e:
        print('/err play command', e)
        if queues[guildid] != []:
            print('/trying to forceplay')
            # await forceplay(ctx)

@client.command(aliases=['ra'])
async def radio(ctx, *, text=None):
    global queues
    try:
        if ctx.channel.id in control_room_ids:
            ctx.guild = client.get_guild(control_room_ids[ctx.channel.id])
        elif not ctx.message.author.voice:
            message = f'{ctx.message.author} join a voice channel to use this command'
            embed_playjoin = discord.Embed(colour=discord.Colour.purple(), description=message)
            await ctx.send(embed=embed_playjoin)
            return
        guild = ctx.guild
        text_channel = ctx.channel
        guildid = str(ctx.guild.id)

        filesavename = None
        time_seconds = 0
        link = None
        title = None
        msg = None
        if text:
            message = f'trying to get {text}'
            embed_ytplay = discord.Embed(colour=discord.Colour.purple(), description=message)
            msg = await ctx.send(embed=embed_ytplay)

            lowered_text = text.lower()
            # `class 95` `kiss 92` `987 fm` `gold 905`
            station_name = None
            # class 95
            if lowered_text in ['95', 'class95', 'class 95', 'class']:
                text = 'http://208.80.54.32:3690/CLASS95_PREM_SC'
                station_name = 'Class 95'
            # kiss 92
            elif lowered_text in ['92', 'kiss92', 'kiss 92', 'kiss']:
                text = 'https://22283.live.streamtheworld.com/KISS_92AAC.aac'
                station_name = 'Kiss 92'
            # 987 fm
            elif lowered_text in ['987', '987fm', '987 fm']:
                text = 'https://19183.live.streamtheworld.com/987FM_PREM.aac'
                station_name = '987 FM'
            # gold 905
            elif lowered_text in ['905', 'gold905', 'gold 905', 'gold']:
                text = 'https://22393.live.streamtheworld.com/GOLD905AAC.aac'
                station_name = 'GOLD 905'
            # SYMPHONY 924
            elif lowered_text in ['924', 'symphony924', 'symphony 924', 'symphony', 'sym', 'symp', 'symph', 'syn']:
                text = 'http://208.80.54.32:3690/SYMPHONY924_PREM_SC'
                station_name = 'Symphony 924'

            filesavename = text
            time_seconds = 0
            link = text
            title = station_name or text
            videos_info_output = [[filesavename, time_seconds, link, title]]
        else:
            message = f'No radio station/link given; available staions: `class 95` `kiss 92` `987 fm` `gold 905` `symphony924`'
            embed_noplay = discord.Embed(colour=discord.Colour.purple(), description=message)
            await ctx.send(embed=embed_noplay)



        queue_count = 0
        for video in videos_info_output:
            filesavename, time_seconds, link, title = video
            if filesavename and time_seconds >= 0 and link and title:
                queue_item = {'filesavename':filesavename, 'time_seconds':time_seconds, 'link':link, 'title':title}
                if guildid not in queues:
                    queues[guildid] = [queue_item]
                    message=f'Queued {title}'
                    queue_count += 1
                elif queues[guildid] != [] and queues[guildid][-1]['link'] == link and queues[guildid][-1]['title'] == title:
                    message = f'{title} is already the most recently queued item. Nothing added to the queue'
                else:
                    queues[guildid].append(queue_item)
                    message=f'Queued {title}'
                    queue_count += 1


        if queue_count > 1:
            message = f'Queued {queue_count} items'

        embed_play = discord.Embed(colour=discord.Colour.purple(), description=message)
        # embed_play.set_footer(text='if QUEUED and nothing happens, type -fp')
        if msg:
            await msg.edit(embed=embed_play, delete_after=5*60)
        else:
            msg = await ctx.send(embed=embed_play, delete_after=5*60)
        if queue_count > 0:
            voice_client = guild.voice_client
            if not voice_client:
                # all i want for christmas plug
                # all_i_want_for_christmas, spotify_playlist = await youtube_download('https://www.youtube.com/watch?v=yXQViqx6GMY', msg, ctx)
                # filesavename, time_seconds, link, title = all_i_want_for_christmas[0]
                # xmas_queue_item = {'filesavename':filesavename, 'time_seconds':time_seconds, 'link':link, 'title':title}
                # if queue_count > 0 and 'Mariah Carey - All I Want For Christmas Is You (Official Video)' not in [queue_item['title'] for queue_item in queues[guildid]] and randfloat()>0.6:
                #     queues[guildid].append(xmas_queue_item)
                #     message = rchoice(['Christmas time 🎅', 'Christmas time 🎄'])
                #     embed_xmas = discord.Embed(colour=rchoice([discord.Colour.red(), discord.Colour.green()]), description=message)
                #     await ctx.send(embed=embed_xmas)
                #     print('play command', queues)
                # all i want for christmas plug
                await join(ctx)
                await play2(guild, text_channel)
            elif not voice_client.is_playing() and not voice_client.is_paused():
                await play2(guild, text_channel)
    except Exception as e:
        print('err radio command', e)
        if queues[guildid] != []:
            print('trying to forceplay')
            await forceplay(ctx)


async def play_for_auto(guild, text_channel, text=None):
    global queues
    guildid = str(guild.id)
    try:
        filesavename = None
        time_seconds = 0
        link = None
        title = None
        msg = None
        if text:
            message = f'Autoplay: getting track'
            embed_ytplay = discord.Embed(colour=discord.Colour.purple(), description=message)
            msg = await text_channel.send(embed=embed_ytplay)

            videos_info_output, spotify_playlist = await youtube_download(text, msg, None)
            number_of_videos = len(videos_info_output)
            if number_of_videos <= 0:
                message = f'Autoplay: error getting {text} from youtube: nothing found'
            elif number_of_videos == 1:
                if videos_info_output[0][0] is None:
                    message = f'Autoplay: error getting {text} from youtube'
                else:
                    message = f'Autoplay: successfully got youtube video'
            else:
                message = f'Autoplay: successfully got youtube video: {number_of_videos} videos'
            embed_ytplay = discord.Embed(colour=discord.Colour.purple(), description=message)
            await msg.edit(embed=embed_ytplay)
        else:
            message = f'Autoplay: could not generate new track'
            embed_noplay = discord.Embed(colour=discord.Colour.purple(), description=message)
            await text_channel.send(embed=embed_noplay)

        queue_count = 0
        for video in videos_info_output:
            filesavename, time_seconds, link, title = video
            if filesavename and time_seconds >= 0 and link and title:
                queue_item = {'filesavename':filesavename, 'time_seconds':time_seconds, 'link':link, 'title':title}
                if guildid not in queues:
                    queues[guildid] = [queue_item]
                    message=f'Queued {title}'
                    queue_count += 1
                elif queues[guildid] != [] and queues[guildid][-1]['link'] == link and queues[guildid][-1]['title'] == title:
                    message = f'Autoplay: {title} is already the most recently queued item. Nothing added to the queue'
                else:
                    queues[guildid].append(queue_item)
                    message=f'Autoplay: Queued {title}'
                    queue_count += 1


        if queue_count > 1:
            message = f'Autoplay: Queued {queue_count} items'

        embed_play = discord.Embed(colour=discord.Colour.purple(), description=message)
        # embed_play.set_footer(text='if QUEUED and nothing happens, type -fp')
        if msg:
            await msg.edit(embed=embed_play, delete_after=5*60)
        else:
            msg = await text_channel.send(embed=embed_play, delete_after=5*60)
        if queue_count > 0:
            voice_client = guild.voice_client
            if not voice_client:
                # await join(ctx)
                await play2(guild, text_channel)
            elif not voice_client.is_playing() and not voice_client.is_paused():
                await play2(guild, text_channel)
    except Exception as e:
        print('err play for auto', e)


@client.command(aliases=['fp'])
async def forceplay(ctx, *, text=None):
    try:
        if ctx.channel.id in control_room_ids:
            ctx.guild = client.get_guild(control_room_ids[ctx.channel.id])
        guild = ctx.guild
        text_channel = ctx.channel
        guildid = str(ctx.guild.id)

        if text:
            await play(ctx, text=text)
        # print('forceplay command', queues)
        embed_forceplay = discord.Embed(colour=discord.Colour.purple(), description=f'trying to force play')
        await ctx.send(embed=embed_forceplay)
        await join(ctx)
        await play2(guild, text_channel)
    except Exception as e:
        print('err forceplay command', e)

FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
# {'filesavename':'song1.mp3', 'time_seconds':230, 'link':'https://youtube.com/IvY7vswVy/', 'title':'song3'}
# {'filesavename':'song1.mp3', 'time_seconds':230, 'start_time':datetime obj, 'pause_time':datetime obj, 'pause_seconds':0, 'link':'https://youtube.com/IvY7vswVy/', 'title':'song3'}
async def play2(guild, text_channel):
    global queues
    global currently_playing
    global autoplays
    global history
    try:
        guildid = str(guild.id)
        voice_client = guild.voice_client
        # voice_client: discord.VoiceClient = discord.utils.get(client.voice_clients, guild=guild)
        # print('play func', queues)
        if queues[guildid] != [] and not voice_client.is_playing() and not voice_client.is_paused() and not loops[guildid] and queues[guildid][0]['filesavename'] == currently_playing[guildid]['filesavename']:
            queues[guildid].pop(0)
            if queues[guildid] == []:
                if autoplays[guildid]:
                    print('doing autoplay while end')
                    current_link = currently_playing[guildid]["link"]
                    new_link = autoplay_get_new_link(current_link, guild)
                    await play_for_auto(guild, text_channel, new_link)
                    print('doing autoplay while end done')
                else:
                    currently_playing[guildid] = {'filesavename':'', 'time_seconds':0, 'start_time':None, 'pause_time':None, 'pause_seconds':0, 'link':'', 'title':''}
                    auto_leave_loop.cancel()
                    await asyncio.sleep(2)
                    print(auto_leave_loop.is_running(), '2')
                    if auto_leave_loop.is_running():
                        await asyncio.sleep(10)
                    auto_leave_loop.start(guild, text_channel)
        if queues[guildid] != [] and not voice_client.is_playing() and not voice_client.is_paused():
            current_song = queues[guildid][0]
            try:
                if current_song['filesavename'][-3:] in validfiletypes:
                    audio_source = discord.FFmpegPCMAudio(current_song['filesavename'])
                else:
                    audio_source = discord.FFmpegPCMAudio(current_song['filesavename'], **FFMPEG_OPTIONS)
            except Exception as e:
                print('PCM err', e)
            print('trying to play')
            try:
                voice_client.play(audio_source, after = lambda e: asyncio.run_coroutine_threadsafe(play2(guild, text_channel), client.loop))
            except Exception as e:
                print('coro err', e)
            current_dt = datetime.now().replace(microsecond=0)
            currently_playing[guildid] = {'filesavename':current_song['filesavename'], 'time_seconds':current_song['time_seconds'], 'start_time':current_dt, 'pause_time':None, 'pause_seconds':0, 'link':current_song['link'], 'title':current_song['title']}
            message = f'Playing: {current_song["title"]} `{seconds_to_strHMS(current_song["time_seconds"])}` [source]({current_song["link"]})'
            embed_playing = discord.Embed(colour=discord.Colour.purple(), description=message)
            await text_channel.send(embed=embed_playing)#, delete_after=5*60)
            print('playing')
            history[guildid].append(currently_playing[guildid]['title'])
            if len(history[guildid]) > 20:
                history[guildid].pop(0)

            if autoplays[guildid] and len(queues[guildid]) == 1:
                print('doing autoplay while queue')
                current_link = queues[guildid][-1]["link"]
                new_link = autoplay_get_new_link(current_link, guild)
                await play_for_auto(guild, text_channel, new_link)
                print('doing autoplay while queue done')

    except Exception as e:
        print('err play func', e)


def get_radio_title(url):
    headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'}
    try:
        response = requests.get(url, headers = headers)
        soup = BeautifulSoup(response.text, features="lxml")
        body = soup.body
        tds_list = body.find_all('td')
        artist_title = tds_list[1].text
        artist_title = artist_title.replace('\n','')
        return artist_title
    except:
        return 'Could not find title'

# {'filesavename':'song1.mp3', 'time_seconds':230, 'start_time':datetime obj, 'pause_time':datetime obj, 'pause_seconds':0, 'link':'https://youtube.com/IvY7vswVy/', 'title':'song3'}
@client.command(aliases=['np'])
async def nowplaying(ctx, output=False):
    if ctx.channel.id in control_room_ids:
        ctx.guild = client.get_guild(control_room_ids[ctx.channel.id])
    guildid = str(ctx.guild.id)
    current_song = currently_playing[guildid]

    if current_song['filesavename'] == '':
        message = f'Now playing: Nothing is currently playing'
        play_time = 0
    else:
        current_dt = datetime.now().replace(microsecond=0)
        time_diff = current_dt-current_song['start_time']
        play_time = time_diff.seconds - current_song['pause_seconds']

        if current_song['pause_time']:
            pause_time = current_song['pause_time']
            pause_time_diff = current_dt-pause_time
            paused_duration_time = pause_time_diff.seconds
            play_time -= paused_duration_time

        playing_time = seconds_to_strHMS(play_time)
        song_time = seconds_to_strHMS(current_song['time_seconds'])

        message = ''
        if current_song["pause_time"] is not None:
            message = 'Now paused: '
        else:
            message = 'Now playing: '

        if current_song["title"] == 'Class 95':
            current_song["title"] = current_song["title"] + ': ' + get_radio_title('https://onlineradiobox.com/sg/class95/playlist/')
        elif current_song["title"] == 'Kiss 92':
            current_song["title"] = current_song["title"] + ': ' + get_radio_title('https://onlineradiobox.com/sg/kiss92/playlist/')
        elif current_song["title"] == '987 FM':
            current_song["title"] = current_song["title"] + ': ' + get_radio_title('https://onlineradiobox.com/sg/987fm/playlist/')
        elif current_song["title"] == 'GOLD 905':
            current_song["title"] = current_song["title"] + ': ' + get_radio_title('https://onlineradiobox.com/sg/gold905/playlist/')
        elif current_song["title"] == 'Symphony 924':
            current_song["title"] = current_song["title"] + ': ' + get_radio_title('https://onlineradiobox.com/sg/symphony/playlist/')

        message += f'{current_song["title"]} [source]({current_song["link"]})\n\
`{playing_time}`{timeline(play_time, current_song["time_seconds"])}`{song_time}`'

    if output == True:
        remaining_time = current_song['time_seconds'] - play_time
        return message, remaining_time
    embed_nowplaying = discord.Embed(colour=discord.Colour.purple(), description=message)
    if loops[guildid]:
        embed_nowplaying.set_footer(text='looping on')
    await ctx.send(embed=embed_nowplaying)

@client.command(aliases=['stop', '='])
async def pause(ctx):
    global currently_playing
    if ctx.channel.id in control_room_ids:
        ctx.guild = client.get_guild(control_room_ids[ctx.channel.id])
    guildid = str(ctx.guild.id)
    voice_client = ctx.guild.voice_client
    if voice_client and voice_client.is_playing():
        current_dt = datetime.now().replace(microsecond=0)
        currently_playing[guildid]['pause_time'] = current_dt
        await voice_client.pause()
    else:
        embed_pause = discord.Embed(colour=discord.Colour.purple(), description='Nothing is currently playing')
        await ctx.send(embed=embed_pause)
# {'filesavename':'song1.mp3', 'time_seconds':230, 'start_time':datetime obj, 'pause_time':datetime obj, 'pause_seconds':0, 'link':'https://youtube.com/IvY7vswVy/', 'title':'song3'}
@client.command(aliases=['go', 'unpause', '>'])
async def resume(ctx):
    global currently_playing
    if ctx.channel.id in control_room_ids:
        ctx.guild = client.get_guild(control_room_ids[ctx.channel.id])
    guildid = str(ctx.guild.id)
    voice_client = ctx.guild.voice_client
    if voice_client and voice_client.is_paused():
        current_dt = datetime.now().replace(microsecond=0)
        pause_time = currently_playing[guildid]['pause_time']
        time_diff = current_dt-pause_time
        paused_duration_time = time_diff.seconds
        currently_playing[guildid]['pause_seconds'] += paused_duration_time
        currently_playing[guildid]['pause_time'] = None
        await voice_client.resume()
    else:
        embed_resume = discord.Embed(colour=discord.Colour.purple(), description='Nothing is currently paused')
        await ctx.send(embed=embed_resume)

@client.command(aliases=['s','next','n'])
async def skip(ctx):
    global queues
    global currently_playing
    if ctx.channel.id in control_room_ids:
        ctx.guild = client.get_guild(control_room_ids[ctx.channel.id])
    voice_client = ctx.guild.voice_client
    guildid = str(ctx.guild.id)
    if voice_client and voice_client.is_playing():
        if loops[guildid]:
            queues[guildid].pop(0)
            if queues[guildid] == []:
                currently_playing[guildid] = {'filesavename':'', 'time_seconds':0, 'start_time':None, 'pause_time':None, 'pause_seconds':0, 'link':'', 'title':''}
                auto_leave_loop.cancel()
                await asyncio.sleep(2)
                print(auto_leave_loop.is_running(), '2')
                if auto_leave_loop.is_running():
                    await asyncio.sleep(10)
                auto_leave_loop.start(ctx.guild, ctx.channel)
        await voice_client.stop()
    else:
        embed_skip = discord.Embed(colour=discord.Colour.purple(), description='Nothing is currently playing')
        await ctx.send(embed=embed_skip)

@client.command(aliases=['l'])
async def loop(ctx):
    global loops
    if ctx.channel.id in control_room_ids:
        ctx.guild = client.get_guild(control_room_ids[ctx.channel.id])
    guildid = str(ctx.guild.id)
    if loops[guildid]:
        loops[guildid] = False
        message = f'{emojiredsquare} looping off'
    else:
        loops[guildid] = True
        message = f'{emojigreensquare} looping on'
    embed_loop = discord.Embed(colour=discord.Colour.purple(), description=message)
    await ctx.send(embed=embed_loop)


# {'filesavename':'song1.mp3', 'time_seconds':230, 'link':'https://youtube.com/IvY7Vy/'}
@client.command(aliases=['q'])
async def queue(ctx):
    global queues
    if ctx.channel.id in control_room_ids:
        ctx.guild = client.get_guild(control_room_ids[ctx.channel.id])
    guildid = str(ctx.guild.id)
    message = ''
    embed_queue = discord.Embed(colour=discord.Colour.purple())
    count = 0
    total_count = 0
    total_time = 0
    page_count = 1
    np_track_percentage_remaining = '000'
    if queues[guildid] == []:
        message += f'Nothing currently in queue'
    elif len(queues[guildid]) == 1:
        description, remaining_time = await nowplaying(ctx, True)
        embed_queue = discord.Embed(colour=discord.Colour.purple(), description=description)
        total_time += remaining_time
        current_track_time = queues[guildid][0]['time_seconds'] or 1
        np_track_percentage_remaining = str(remaining_time/current_track_time).split('.')[1] + '000'
    else:
        description, remaining_time = await nowplaying(ctx, True)
        embed_queue = discord.Embed(colour=discord.Colour.purple(), description=description)
        total_time += remaining_time
        current_track_time = queues[guildid][0]['time_seconds'] or 1
        np_track_percentage_remaining = str(remaining_time/current_track_time).split('.')[1] + '000'
        for item in queues[guildid][1:]:
            count += 1
            total_count += 1
            item_time = seconds_to_strHMS(item['time_seconds'])
            total_time += item['time_seconds']
            message += f'{total_count}) {item["title"]} `{item_time}` [source]({item["link"]})' + '\n'
            if count >= 5:
                embed_queue.add_field(name=f'queue-{page_count}', value=message, inline=False)
                message = ''
                count = 0
                page_count += 1
            if total_count >= 25:
                embed_queue.set_footer(text=f'and {len(queues[guildid])-total_count-1} more tracks (i would show more but there\'s a character limit)')
                for remaining_item in queues[guildid][total_count+1:]:
                    total_time += remaining_item['time_seconds']
                break

    if message != '':
        embed_queue.add_field(name=f'queue-{page_count}', value=message, inline=False)
    total = f'{len(queues[guildid])-1}.{np_track_percentage_remaining[:2]}' if len(queues[guildid]) > 0 else '0'
    embed_queue.add_field(name=f'total', value=f'{total} tracks `{seconds_to_strHMS(total_time)}` left', inline=False)
    await ctx.send(embed=embed_queue)

@client.command(aliases=['c'])
async def clear(ctx):
    global queues
    global currently_playing
    if ctx.channel.id in control_room_ids:
        ctx.guild = client.get_guild(control_room_ids[ctx.channel.id])
    guildid = str(ctx.guild.id)
    queues[guildid] = [queues[guildid][0]] if queues[guildid] != [] else []
    embed_clearqueue = discord.Embed(colour=discord.Colour.purple(), description='queue cleared')
    await ctx.send(embed=embed_clearqueue)

async def clear2(ctx):
    global queues
    global currently_playing
    if ctx.channel.id in control_room_ids:
        ctx.guild = client.get_guild(control_room_ids[ctx.channel.id])
    guildid = str(ctx.guild.id)
    queues[guildid] = []
    currently_playing[guildid] = {'filesavename':'', 'time_seconds':0, 'start_time':None, 'pause_time':None, 'pause_seconds':0, 'link':'', 'title':''}

@client.command(aliases=['rm'])
async def remove(ctx, remove_index=None):
    global queues
    if ctx.channel.id in control_room_ids:
        ctx.guild = client.get_guild(control_room_ids[ctx.channel.id])
    guildid = str(ctx.guild.id)
    if queues[guildid] == [] or len(queues[guildid]) == 1:
        message = f'queue currently empty; nothing removed'
    elif remove_index is None:
        remove_index = len(queues[guildid])-1
        remove_track = queues[guildid][remove_index]
        queues[guildid].pop(remove_index)
        track_time = seconds_to_strHMS(remove_track['time_seconds'])
        message = f'successfully removed {remove_index}) {remove_track["title"]} `{track_time}` [source]({remove_track["link"]})'
    elif remove_index.isdigit() and 0 < int(remove_index) < len(queues[guildid]):
        remove_index = int(remove_index)
        remove_track = queues[guildid][remove_index]
        queues[guildid].pop(remove_index)
        track_time = seconds_to_strHMS(remove_track['time_seconds'])
        message = f'successfully removed {remove_index}) {remove_track["title"]} `{track_time}` [source]({remove_track["link"]})'
    else:
        message = f'invalid queue number `{remove_index}`; nothing removed, current queue numbers: `1-{len(queues[guildid])-1}`'
    embed_queueremove = discord.Embed(colour=discord.Colour.purple(), description=message)
    await ctx.send(embed=embed_queueremove)

# queues[guildid].insert(to, queues[guildid].pop(from))
@client.command(aliases=['m'])
async def move(ctx, from_index=None, to_index=None):
    global queues
    if ctx.channel.id in control_room_ids:
        ctx.guild = client.get_guild(control_room_ids[ctx.channel.id])
    guildid = str(ctx.guild.id)
    if queues[guildid] == [] or len(queues[guildid]) == 1:
        message = f'queue currently empty; nothing to move'
    elif len(queues[guildid]) == 2:
        message = f'only 1 track in queue; nothing to move'
    #last to first
    elif from_index is None and to_index is None:
        item = queues[guildid][-1]
        item_string = f'{item["title"]} `{seconds_to_strHMS(item["time_seconds"])}` [source]({item["link"]})'
        queues[guildid].insert(1, queues[guildid].pop(-1))
        message = f'moved {len(queues[guildid])-1}➔1) {item_string}'
    #from_index to first
    elif from_index is not None and to_index is None and from_index.isdigit() and 0 < int(from_index) < len(queues[guildid]):
        if from_index == '1':
            message = f'cant move track 1 to 1; nothing moved'
        else:
            from_index = int(from_index)
            item = queues[guildid][from_index]
            item_string = f'{item["title"]} `{seconds_to_strHMS(item["time_seconds"])}` [source]({item["link"]})'
            queues[guildid].insert(1, queues[guildid].pop(from_index))
            message = f'moved {from_index}➔1) {item_string}'
    #move
    elif from_index is not None and to_index is not None and from_index.isdigit() and 0 < int(from_index) < len(queues[guildid]) and to_index.isdigit() and 0 < int(to_index) < len(queues[guildid]):
        if from_index == to_index:
            message = f'cant move track {from_index} to {to_index}; nothing moved'
        else:
            from_index = int(from_index)
            to_index = int(to_index)
            item = queues[guildid][from_index]
            item_string = f'{item["title"]} `{seconds_to_strHMS(item["time_seconds"])}` [source]({item["link"]})'
            queues[guildid].insert(to_index, queues[guildid].pop(from_index))
            message = f'moved {from_index}➔{to_index}) {item_string}'
    #invalid
    else:
        message = ''
        if from_index is not None and (from_index.isdigit() and 0 < int(from_index) < len(queues[guildid])) == False:
            message += f'invalid `old` queue number: `{from_index}`; available queue numbers: `1-{len(queues[guildid])-1}`'
        if to_index is not None and (to_index.isdigit() and 0 < int(to_index) < len(queues[guildid])) == False:
            if message != '':
                message += '\n'
            message += f'invalid `new` queue number: `{to_index}`; available queue numbers: `1-{len(queues[guildid])-1}`'
    embed_queuemove = discord.Embed(colour=discord.Colour.purple(), description=message)
    await ctx.send(embed=embed_queuemove)

@client.command(aliases=['jm'])
async def jump(ctx, jump_index=None):
    global queues
    if ctx.channel.id in control_room_ids:
        ctx.guild = client.get_guild(control_room_ids[ctx.channel.id])
    guildid = str(ctx.guild.id)
    if queues[guildid] == [] or len(queues[guildid]) == 1:
        message = f'queue currently empty; nothing to jump to'
    elif jump_index is None:
        message = f'no queue number given; nothing to jump to, current queue numbers: `1-{len(queues[guildid])-1}`'
    elif jump_index.isdigit() and 0 < int(jump_index) < len(queues[guildid]):
        jump_track = queues[guildid][int(jump_index)]
        queue_item = f'{jump_index}) {jump_track["title"]} `{seconds_to_strHMS(jump_track["time_seconds"])}` [source]({jump_track["link"]})'
        if jump_index != '1':
            for i in range(int(jump_index)):
                queues[guildid].pop(0)
        message = f'jumped to {queue_item}'
        voice_client = ctx.guild.voice_client
        if voice_client and voice_client.is_playing():
            await voice_client.stop()
    else:
        message = f'invalid queue number `{jump_index}`; nothing to jump to, current queue numbers: `1-{len(queues[guildid])-1}`'
    embed_queuejump = discord.Embed(colour=discord.Colour.purple(), description=message)
    await ctx.send(embed=embed_queuejump)

@client.command(aliases=['shuffle', 'sh'])
async def _shuffle(ctx):
    global queues
    if ctx.channel.id in control_room_ids:
        ctx.guild = client.get_guild(control_room_ids[ctx.channel.id])
    guildid = str(ctx.guild.id)
    if queues[guildid] == [] or len(queues[guildid]) == 1:
        message = f'queue currently empty; nothing to shuffle'
    elif len(queues[guildid]) == 2:
        message = f'only 1 track in queue; nothing to shuffle'
    else:
        copy = queues[guildid][1:]
        shuffle(copy)
        queues[guildid][1:] = copy
        message = f'Shuffled {len(queues[guildid])-1} tracks in queue'
    embed_queueshuffle = discord.Embed(colour=discord.Colour.purple(), description=message)
    await ctx.send(embed=embed_queueshuffle)

# https://api.lyrics.ovh/v1/artist/title
# https://some-random-api.ml/lyrics?title=adventure of a Lifetime
# {'filesavename':'', 'time_seconds':0, 'start_time':None, 'pause_time':None, 'pause_seconds':0, 'link':'', 'title':''}
@client.command(aliases=['lyric', 'ly'])
async def lyrics(ctx, *, query=None):
    global currently_playing
    if ctx.channel.id in control_room_ids:
        ctx.guild = client.get_guild(control_room_ids[ctx.channel.id])
    guildid = str(ctx.guild.id)
    if query is None and currently_playing[guildid]['title'] == '':
        message = 'Uh oh: Nothing is currently playing and no query was given'
        embed_lyrics = discord.Embed(colour=discord.Colour.purple(), description=message)
        await ctx.send(embed=embed_lyrics)
    else:
        if query is None:
            query = currently_playing[guildid]['title']
            if '(' in query:
                bracket1_index = query.rindex('(')
                query = query[:bracket1_index]
            if '[' in query:
                bracket2_index = query.rindex('[')
                query = query[:bracket2_index]
            query = query.replace('HD','').replace('Audio','').replace('Official','').replace('-','')
        data_raw = requests.get(f"https://some-random-api.ml/lyrics?title={query}")
        data_dict = json.loads(data_raw.text)

        if 'error' in data_dict:
            if data_raw.status_code == 404:
                message = f'Uh oh: {data_dict["error"]}: {query}'
            else:
                message = f'Uh oh: {data_dict["error"]}'
            embed_lyrics = discord.Embed(colour=discord.Colour.purple(), description=message)
            await ctx.send(embed=embed_lyrics)
        else:
            title = data_dict['title']
            author = data_dict['author']
            lyrics = [data_dict['lyrics']]

            while len(lyrics[-1]) > 1000:
                split_index = lyrics[-1][:1000].rindex('\n')
                last_page = lyrics[-1]
                lyrics[-1] = last_page[:split_index]
                lyrics.append(last_page[split_index:])

            embed_lyrics = discord.Embed(title=f'Lyrics: {title}', colour=discord.Colour.purple(), description=lyrics[0])
            if len(lyrics) > 1:
                for page in lyrics[1:]:
                    embed_lyrics.add_field(name='\u200b', value=page, inline=False)
            await ctx.send(embed=embed_lyrics)


def autoplay_get_new_link(current_link, guild):
    if 'youtube.com' not in current_link and 'youtu.be' not in current_link:
        print('autoplay_get_new_link not youtube link')
        return None
    try:
        guildid = str(guild.id)

        if 'watch?v=' in current_link:
            index = current_link.index('watch?v=')
            current_link = current_link[index+8:]
        if '/' in current_link:
            index = current_link.index('/')
            current_link = current_link[:index]
        video_id = current_link
        # print(video_id)

        api_service_name = 'youtube'
        api_version = 'v3'
        youtube = googleapiclient.discovery.build(
            api_service_name, api_version, developerKey = YOUTUBE_DEVELOPER_KEY)

        request = youtube.search().list(
            part = 'snippet',
            relatedToVideoId = video_id,
            type = 'video'
        )
        response = request.execute()
        # print(response)
        # new_id = response['items'][0]['id']['videoId']
        # new_link = 'https://www.youtube.com/watch?v=' + new_id
        for item in response['items']:
            if 'snippet' in item:
                new_link = item['snippet']['title']
                if new_link not in history[guildid]:
                    return new_link
        return None
    except Exception as e:
        print('auto get link err', e)
        return None

@client.command(aliases=['auto', 'ap'])
async def autoplay(ctx):
    if ctx.channel.id in control_room_ids:
        ctx.guild = client.get_guild(control_room_ids[ctx.channel.id])
    guildid = str(ctx.guild.id)
    guild = ctx.guild
    text_channel = ctx.channel
    # voice_client = guild.voice_client

    global autoplays
    global queues
    if autoplays[guildid]:
        autoplays[guildid] = False
        message = f'{emojiredsquare} autoplay off'
        embed_autoplay = discord.Embed(colour=discord.Colour.purple(), description=message)
        await ctx.send(embed=embed_autoplay)
    else:
        autoplays[guildid] = True
        message = f'{emojigreensquare} autoplay on'
        embed_autoplay = discord.Embed(colour=discord.Colour.purple(), description=message)
        await ctx.send(embed=embed_autoplay)

        if len(queues[guildid]) == 1:
            print('doing autoplay from command')
            current_link = queues[guildid][-1]["link"]
            new_link = autoplay_get_new_link(current_link, guild)
            await play_for_auto(guild, text_channel, new_link)
            print('doing autoplay from command done')



def short_queue(queue):
    message = ''
    total_count = 0
    total_time = 0
    if queue == []:
        message += f'Nothing currently in queue'
    else:
        for item in queue:
            total_count += 1
            item_time = seconds_to_strHMS(item['time_seconds'])
            total_time += item['time_seconds']
            message += f'{total_count}) {item["title"]} `{item_time}` [source]({item["link"]})' + '\n'
            if total_count >= 5:
                message += f'and {len(queue)-total_count} more tracks\n'
                for remaining_item in queue[total_count+1:]:
                    total_time += remaining_item['time_seconds']
                break
        total = len(queue)
        message += f'{total} tracks `{seconds_to_strHMS(total_time)}`'
    return message

def gdrive_upload_save_queue_media(filename):
    # View all folders and file in your Google Drive - 'root' in parents and =>base dir
    folder = drive.ListFile({'q': "'root' in parents and title='gwoovy' and trashed=false"}).GetList()[0]
    for dirfilename in os.listdir():
        if filename in dirfilename:
            filename = dirfilename
            break
    file = drive.CreateFile({"parents": [{"id": folder['id']}] })
    file.SetContentFile(filename)
    file.Upload()
    title = file['title']
    print(f'uploaded file {title}')

def gdrive_download_save_queue_media(filename):
    for dirfilename in os.listdir():
        if filename in dirfilename:
            print(f'{filename} already downloaded')
            break
    else:
        folder = drive.ListFile({'q': "'root' in parents and title='gwoovy' and trashed=false"}).GetList()[0]
        file_list = drive.ListFile({'q': "'{}' in parents and trashed=false".format(folder['id']) }).GetList()
        for file1 in file_list:
            if filename in file1['title']:
                file1.GetContentFile(file1['title'])
                title = file1['title']
                print(f'downloaded file {title}')

@client.command(aliases=[])
async def save(ctx,*,queue_name=None):
    if ctx.channel.id in control_room_ids:
        ctx.guild = client.get_guild(control_room_ids[ctx.channel.id])
    guildid = str(ctx.guild.id)
    userid = str(ctx.author.id)
    media_upload = False
    try:
        db = psycopg2.connect(conndb)
        cursor = db.cursor()
        cursor.execute('SELECT queue_name FROM queues WHERE id = %s',(userid,))
        data = cursor.fetchall()
        current_user_queue_names = [name for saved_queue in data for name in saved_queue]

        if queues[guildid] == []:
            message = 'Nothing currently in queue. Cannot save queue'
        elif len(queues[guildid]) == 1:
            message = 'There is only 1 item in the queue. Queue not saved'
        elif queue_name is None:
            message = 'No queue name given'
        elif '"' in queue_name or '\'' in queue_name or '{' in queue_name or '}' in queue_name or '\\' in queue_name:
            message = 'Invalid queue name; queue names cannot contain `"`, `\'`, `{`, `}`, `\\`'
        elif queue_name in current_user_queue_names:
            message = f'You already have another queue saved as `{queue_name}`. Please use a different name'
        else:
            queue = queues[guildid]
            short_save_queue = short_queue(queue)
            message = 'Saving queue'
            embed_savequeue = discord.Embed(colour=discord.Colour.purple(), description=message)
            msg = await ctx.send(embed=embed_savequeue)
            cursor.execute('INSERT INTO queues VALUES(%s,%s,%s,%s,%s)', (str(guildid), str(userid), str(ctx.author), str(queue_name), str(queue)))
            for queue_item in queue:
                if queue_item['filesavename'][-3:] in validfiletypes:
                    media_upload = True
                    message = f'Saving queue: Uploading {queue_item["filesavename"]}\nWARNING this queue contains media files, loading this queue may take some time'
                    embed_savequeue = discord.Embed(colour=discord.Colour.purple(), description=message)
                    await msg.edit(embed=embed_savequeue)
                    gdrive_upload_save_queue_media(queue_item['filesavename'])
            message = short_save_queue
        db.commit()
        cursor.close()
        db.close()

        if msg:
            embed_savequeue = discord.Embed(title=f'Saved queue `{queue_name}`', colour=discord.Colour.purple(), description=message)
            if media_upload:
                embed_savequeue.set_footer(text='WARNING: this queue contains media files, loading this queue may take time')
            await msg.edit(embed=embed_savequeue)
        else:
            embed_savequeue = discord.Embed(colour=discord.Colour.purple(), description=message)
            await ctx.send(embed=embed_savequeue)
    except Exception as e:
        print(e)

@client.command(aliases=['ld'])
async def load(ctx,*,queue_name=None):
    await ctx.send('no')
    return
    global queues
    if ctx.channel.id in control_room_ids:
        ctx.guild = client.get_guild(control_room_ids[ctx.channel.id])
    guildid = str(ctx.guild.id)
    # userid = str(ctx.author.id)
    guild = ctx.guild
    text_channel = ctx.channel
    try:
        db = psycopg2.connect(conndb)
        cursor = db.cursor()
        # cursor.execute('SELECT queue_name FROM queues WHERE id = %s',(userid,))
        cursor.execute('SELECT queue_name, id FROM queues')
        data = cursor.fetchall()
        # current_queue_names = [name for saved_queue in data for name in saved_queue]
        current_queue_names = [str(list(saved_queue)[0]) for saved_queue in data]
        current_queue_user_ids = [str(list(saved_queue)[1]) for saved_queue in data]
        db.commit()
        cursor.close()
        db.close()
        if queue_name and queue_name in current_queue_names:
            if current_queue_names.count(queue_name) > 1:
                indices = [i for i, x in enumerate(current_queue_names) if x == queue_name]
                # TODO: select which queue, person 1 person 2
            else:
                userid = current_queue_user_ids[current_queue_names.index(queue_name)]
            await join(ctx)
            voice_client = ctx.guild.voice_client
            if voice_client:
                db = psycopg2.connect(conndb)
                cursor = db.cursor()
                cursor.execute('SELECT queue FROM queues WHERE id = %s AND queue_name = %s',(userid,queue_name))
                data = cursor.fetchall()[0][0]
                db.commit()
                cursor.close()
                db.close()

                loaded_queue = eval(str(data))
                first_reload = True

                message = f'Loading `{queue_name}` from `{ctx.author}`'
                embed_savequeue = discord.Embed(colour=discord.Colour.purple(), description=message)
                msg = await ctx.send(embed=embed_savequeue)

                loading_total = len(loaded_queue)
                loading_count = 0
                for queue_item in loaded_queue:
                    try:
                        loading_count += 1
                        if queue_item['filesavename'][-3:] in validfiletypes:
                            message = f'Loading `{queue_name}` from `{ctx.author}`: downloading media {queue_item["filesavename"]} [{loading_count}/{loading_total}]'
                            embed_savequeuedownloading = discord.Embed(colour=discord.Colour.purple(), description=message)
                            await msg.edit(embed=embed_savequeuedownloading)
                            gdrive_download_save_queue_media(queue_item['filesavename'])
                            queues[guildid].append(queue_item)
                        else:
                            message = f'Loading `{queue_name}` from `{ctx.author}`: getting media {queue_item["title"]} [{loading_count}/{loading_total}]'
                            embed_savequeuedownloading = discord.Embed(colour=discord.Colour.purple(), description=message)
                            await msg.edit(embed=embed_savequeuedownloading)
                            videos_info_output, spotify_playlist = await youtube_download(queue_item["link"], msg, ctx)
                            if len(videos_info_output)>0 and videos_info_output[0][0] is not None:
                                filesavename, time_seconds, link, title = videos_info_output[0]
                                if filesavename and time_seconds >= 0 and link and title:
                                    queue_item = {'filesavename':filesavename, 'time_seconds':time_seconds, 'link':link, 'title':title}
                                    queues[guildid].append(queue_item)
                        if first_reload:
                            first_reload = False
                            if not voice_client.is_playing() and not voice_client.is_paused():
                                await play2(guild, text_channel)
                    except Exception as e:
                        print('error loading', e)

                message = f'Loaded `{queue_name}` from `{ctx.author}`'
                embed_savequeue = discord.Embed(colour=discord.Colour.purple(), description=message)
                await msg.edit(embed=embed_savequeue)

                if not voice_client.is_playing() and not voice_client.is_paused():
                    await play2(guild, text_channel)
        elif queue_name and not queue_name in current_queue_names:
            message = f'You do not have any queue saved as `{queue_name}`'
            embed_savequeue = discord.Embed(colour=discord.Colour.purple(), description=message)
            await ctx.send(embed=embed_savequeue)
        else:
            #show saved
            message = f'no queue name given'
            embed_savequeue = discord.Embed(colour=discord.Colour.purple(), description=message)
            await ctx.send(embed=embed_savequeue)
    except Exception as e:
        print(e)

@client.command(aliases=['lf'])
async def loadfrom(ctx, target: Optional[discord.Member], *, queue_name=None):
    global queues
    if ctx.channel.id in control_room_ids:
        ctx.guild = client.get_guild(control_room_ids[ctx.channel.id])
    guildid = str(ctx.guild.id)
    userid = str(ctx.author.id)
    guild = ctx.guild
    text_channel = ctx.channel
    if target is None and queue_name is None:
        message = f'No user and queue name give; -loadfrom @user queuename'
        embed_invalidloadfrom = discord.Embed(colour=discord.Colour.purple(), description=message)
        await ctx.send(embed=embed_invalidloadfrom)
    elif target is None and queue_name is not None:
        user_detected = (queue_name.split(' '))[0]
        message = f'Could not find the user `{user_detected}`'
        embed_invalidloadfrom = discord.Embed(colour=discord.Colour.purple(), description=message)
        await ctx.send(embed=embed_invalidloadfrom)
    elif target is not None and queue_name is None:
        message = f'No queue name entered for `{target}`; -loadfrom @{target} **queuename**\nto see queues saved by {target}, use -show @{target}'
        embed_invalidloadfrom = discord.Embed(colour=discord.Colour.purple(), description=message)
        await ctx.send(embed=embed_invalidloadfrom)
    else:
        userid = str(target.id)
        try:
            db = psycopg2.connect(conndb)
            cursor = db.cursor()
            cursor.execute('SELECT queue_name FROM queues WHERE id = %s',(userid,))
            data = cursor.fetchall()
            current_user_queue_names = [name for saved_queue in data for name in saved_queue]
            db.commit()
            cursor.close()
            db.close()
            if queue_name and queue_name in current_user_queue_names:
                await join(ctx)
                voice_client = ctx.guild.voice_client
                if voice_client:
                    db = psycopg2.connect(conndb)
                    cursor = db.cursor()
                    cursor.execute('SELECT queue FROM queues WHERE id = %s AND queue_name = %s',(userid,queue_name))
                    data = cursor.fetchall()[0][0]
                    db.commit()
                    cursor.close()
                    db.close()

                    loaded_queue = eval(str(data))
                    reloaded_queue = []
                    first_reload = True

                    message = f'Loading `{queue_name}` from `{target}` by `{ctx.author}`'
                    embed_savequeue = discord.Embed(colour=discord.Colour.purple(), description=message)
                    msg = await ctx.send(embed=embed_savequeue)

                    loading_total = len(loaded_queue)
                    loading_count = 0
                    for queue_item in loaded_queue:
                        loading_count += 1
                        if queue_item['filesavename'][-3:] in validfiletypes:
                            message = f'Loading `{queue_name}` from `{target}` by `{ctx.author}`: downloading media {queue_item["filesavename"]} [{loading_count}/{loading_total}]'
                            embed_savequeuedownloading = discord.Embed(colour=discord.Colour.purple(), description=message)
                            await msg.edit(embed=embed_savequeuedownloading)
                            gdrive_download_save_queue_media(queue_item['filesavename'])
                            if first_reload:
                                first_reload = False
                                queues[guildid].append(queue_item)
                                if not voice_client.is_playing() and not voice_client.is_paused():
                                    await play2(guild, text_channel)
                            else:
                                reloaded_queue.append(queue_item)
                        else:
                            message = f'Loading `{queue_name}` from `{target}` by `{ctx.author}`: getting media {queue_item["title"]} [{loading_count}/{loading_total}]'
                            embed_savequeuedownloading = discord.Embed(colour=discord.Colour.purple(), description=message)
                            await msg.edit(embed=embed_savequeuedownloading)
                            videos_info_output, spotify_playlist = await youtube_download(queue_item["link"], msg, ctx)
                            if len(videos_info_output)>0 and videos_info_output[0][0] is not None:
                                filesavename, time_seconds, link, title = videos_info_output[0]
                                if filesavename and time_seconds >= 0 and link and title:
                                    queue_item = {'filesavename':filesavename, 'time_seconds':time_seconds, 'link':link, 'title':title}
                                    if first_reload:
                                        first_reload = False
                                        queues[guildid].append(queue_item)
                                        if not voice_client.is_playing() and not voice_client.is_paused():
                                            await play2(guild, text_channel)
                                    else:
                                        reloaded_queue.append(queue_item)

                    queues[guildid].extend(reloaded_queue)

                    message = f'Loaded `{queue_name}` from `{target}`'
                    embed_savequeue = discord.Embed(colour=discord.Colour.purple(), description=message)
                    await msg.edit(embed=embed_savequeue)

                    if not voice_client.is_playing() and not voice_client.is_paused():
                        await play2(guild, text_channel)
            elif queue_name and not queue_name in current_user_queue_names:
                message = f'{target} does not have any queue saved as `{queue_name}`'
                embed_savequeue = discord.Embed(colour=discord.Colour.purple(), description=message)
                await ctx.send(embed=embed_savequeue)
            else:
                #show saved
                message = f'no queue name given'
                embed_savequeue = discord.Embed(colour=discord.Colour.purple(), description=message)
                await ctx.send(embed=embed_savequeue)
        except Exception as e:
            print(e)

@client.command(aliases=['showsaved', 'sw'])
async def show(ctx, target: Optional[discord.Member]):
    if ctx.channel.id in control_room_ids:
        ctx.guild = client.get_guild(control_room_ids[ctx.channel.id])
    guildid = str(ctx.guild.id)
    target = target or ctx.author
    userid = str(target.id)
    try:
        db = psycopg2.connect(conndb)
        cursor = db.cursor()
        cursor.execute('SELECT queue_name FROM queues WHERE id = %s',(userid,))
        data = cursor.fetchall()
        print(data)
        current_user_queue_names = [name for saved_queue in data for name in saved_queue]
        print(current_user_queue_names)
        if current_user_queue_names == []:
            message = f'{target} does not have any queues saved'
            embed_showsaved = discord.Embed(colour=discord.Colour.purple(), description=message)
            await ctx.send(embed=embed_showsaved)
        else:
            embed_showsaved = discord.Embed(title=f'{target} Saved queues', colour=discord.Colour.purple())
            count = 0
            for queue_name in current_user_queue_names:
                cursor.execute('SELECT queue FROM queues WHERE id = %s AND queue_name = %s',(userid,queue_name))
                data = cursor.fetchall()[0][0]
                loaded_queue = eval(str(data))
                embed_showsaved.add_field(name=queue_name, value=short_queue(loaded_queue), inline=False)
                count += 1
                if count >= 20:
                    await ctx.send(embed=embed_showsaved)
                    embed_showsaved = discord.Embed(title=f'{target} Saved queues', colour=discord.Colour.purple())
                    count = 0
            if count != 0:
                await ctx.send(embed=embed_showsaved)

        db.commit()
        cursor.close()
        db.close()
    except Exception as e:
        print(e)

@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        # com = str(error).split('"')[1]
        # author_mention = ctx.message.author.mention
        # message = author_mention + ' -' + com + ' isnt a command; use -help for a list of commands'
        # await ctx.send(message)
        pass
    elif isinstance(error, commands.NotOwner):
        # await ctx.send(f'{error} no')
        pass
    elif str(error) == 'Command raised an exception: TypeError: object NoneType can\'t be used in \'await\' expression':
        pass
    else:
        gmthj = await client.fetch_user(416620513608335361) #gmthj
        await ctx.send(f'well it seems like something went wrong {gmthj.mention} : {error}')
        print('command eroorr ', str(error))




# @client.event
# async def on_message(message):
#     embeds = message.embeds
#     for embed in embeds:
#         print(embed.to_dict())
#     if message.author == client.user:
#         return
#     await client.process_commands(message)

@client.command(aliases=['audit'])
@commands.is_owner()
async def aaaa(ctx, search=10, guildid=797770451971342417):
    # embed_person = discord.Embed(title='a',colour=discord.Colour.blue())
    # embed_person.set_image(url=search)
    # await ctx.send(embed=embed_person)
    guild = await client.fetch_guild(guildid)
    txt = ''
    async for entry in guild.audit_logs(limit=int(search)):
        txt += '{0.user} did {0.action} to {0.target}, extra {0.extra}, changes {0.changes}\n'.format(entry)
    with open('auditlog.txt', 'w') as f:
        f.write(f'{txt}')
    f2 = open('auditlog.txt','rb')
    text = discord.File(f2)
    f2.close()
    await ctx.send(file=text)



@client.command()
@commands.is_owner()
async def run(ctx,*,a=None):
    try:
        exec(str(a))
    except Exception as e:
        print(e)



@tasks.loop(minutes = AUTO_LEAVE_TIME, count = 2)
async def auto_leave_loop(guild, text_channel):
    current_iter = auto_leave_loop.current_loop
    if current_iter == 0:
        embed_preautoleave = discord.Embed(colour=discord.Colour.purple(), description=f'Nothing in queue: I will leave in {AUTO_LEAVE_TIME} mins if nothing is queued')
        await text_channel.send(embed=embed_preautoleave, delete_after=10*60)
    else:
        voice_client = guild.voice_client
        guildid = str(guild.id)
        if voice_client and voice_client.is_connected() and not voice_client.is_playing() and not voice_client.is_paused() and queues[guildid] == []:
            await voice_client.disconnect()
            embed_autoleave = discord.Embed(colour=discord.Colour.purple(), description='Nothing in queue: Bye👋')
            await text_channel.send(embed=embed_autoleave)

status_index = 0
@tasks.loop(seconds = 8)
async def rolling_status_loop(statuses):
    global status_index
    status_index += 1
    if status_index >= len(statuses):
        status_index = 0
    name = statuses[status_index]
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name=name))


@client.command()
@commands.guild_only()
@commands.is_owner()
async def sync(ctx, guilds: Greedy[discord.Object], spec: Optional[Literal["~", "*", "^"]] = None) -> None:
    if not guilds:
        if spec == "~":
            synced = await ctx.bot.tree.sync(guild=ctx.guild)
        elif spec == "*":
            ctx.bot.tree.copy_global_to(guild=ctx.guild)
            synced = await ctx.bot.tree.sync(guild=ctx.guild)
        elif spec == "^":
            ctx.bot.tree.clear_commands(guild=ctx.guild)
            await ctx.bot.tree.sync(guild=ctx.guild)
            synced = []
        else:
            synced = await ctx.bot.tree.sync()

        await ctx.send(f"Synced {len(synced)} commands {'globally' if spec is None else 'to the current guild.'}")
        return

    ret = 0
    for guild in guilds:
        try:
            await ctx.bot.tree.sync(guild=guild)
        except discord.HTTPException:
            pass
        else:
            ret += 1

    await ctx.send(f"Synced the tree to {ret}/{len(guilds)}.")


client.run(os.environ['DISCORD_TOKEN'])
