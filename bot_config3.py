db_creds = 'dbname=datagwoovy user=postgres password=postgrespassword'
logs_channel = 856071033525502004


# bot_version_number, bot_version_message = 'Gwoovy: v2.1', ' - slash'
bot_version_number, bot_version_message = 'Gwoovy: v43', ' - fl'
# bot_version_number, bot_version_message = 'Gwoovy: v42', ' - spotify album support - better playlist'
# bot_version_number, bot_version_message = 'Gwoovy: v41', ' - rm toggle'
# bot_version_number, bot_version_message = 'Gwoovy: v40', ' - yt link clean'
# bot_version_number, bot_version_message = 'Gwoovy: v39', ' - aws'
# bot_version_number, bot_version_message = 'Gwoovy: v38', ' - update cookies'
# bot_version_number, bot_version_message = 'Gwoovy: v37', ' - coub.com'
# bot_version_number, bot_version_message = 'Gwoovy: v36', ' - new autoplay algo'
# bot_version_number, bot_version_message = 'Gwoovy: v35', ' - update yt cookies - yt-dlp'
# bot_version_number, bot_version_message = 'Gwoovy: v34', ' - switch to yt-dlp - SoundCloud'
# bot_version_number, bot_version_message = 'Gwoovy: v33', ' - xmas'
# bot_version_number, bot_version_message = 'Gwoovy: v32', ' - try ytdl geo bypass'
# bot_version_number, bot_version_message = 'Gwoovy: v31', ' - radio - get song names'
# bot_version_number, bot_version_message = 'Gwoovy: v30', ' - radio - fix div by 0 error on queue'
# bot_version_number, bot_version_message = 'Gwoovy: v29', ' - radio - name update'
# bot_version_number, bot_version_message = 'Gwoovy: v28', ' - auto play: better next song selection'
# bot_version_number, bot_version_message = 'Gwoovy: v27', ' - auto play: auto queue new song'
# bot_version_number, bot_version_message = 'Gwoovy: v26', ' - fix save load queues - add loading progress counter'
# bot_version_number, bot_version_message = 'Gwoovy: v25', ' - better list loading(better load for spotify playlist)'
# bot_version_number, bot_version_message = 'Gwoovy: v24', ' - refresh help'
# bot_version_number, bot_version_message = 'Gwoovy: v23', ' - update help message/save load queues disabled'
# bot_version_number, bot_version_message = 'v14-music', ' - queue management(jump)'

commands_music = '**play/p** `link/search` or `attachment`: play songs from youtube/spotify/soundcloud/attachment' + '\n\
┗ supported attachment filetypes: mp3, mp4, mov, mkv, webm, wav' + '\n\
**pause/stop/=**: pause song' + '\n\
**resume/go/unpause/>**: resume song' + '\n\
**skip/s/next/n**: skip to next song in the queue' + '\n\
**loop/l**: toggle looping of current song on/off' + '\n\
**lyrics/lyric/ly** `query`: get lyrics of `query` song' + '\n\
┗ leave `query` blank for current song' + '\n\
★**autoplay/auto/ap**: toggle autoplaying on/off; auto queue next song when queue is empty' + '\n\
**radio/ra** `channel/link`: play live radio station' + '\n\
┣ `channel`s available: `class 95` `kiss 92` `987 fm` `gold 905` `symphony924`' + '\n\
┗ or use a `link` from: [fmstream](http://fmstream.org/index.php) [fmstream - singapore](http://fmstream.org/index.php?c=SNG)' + '\n\
---┗ get links with HE or HE2, MP3 also works but quality is usually shit' + '\n\
'
commands_queue = '**nowplaying/np**: show current playing song' + '\n\
**queue/q**: show song queue' + '\n\
**clear/c**: clear entire queue' + '\n\
**remove/rm** `queue-number`: remove track `x` from queue' + '\n\
┗ leave `queue-number` blank to remove last track' + '\n\
**move/m** `old` `new`: move track from `old` queue number to `new` queue number' + '\n\
┣ leave both blank to move last track to front of the queue' + '\n\
┗ leave `new` blank to move `old` to front of the queue' + '\n\
**jump/jm** `queue-number`: jump to track `x` in queue' + '\n\
**shuffle/sh**: shuffle queue' + '\n\
'
commands_save_queue = '★**save** `name`: save current queue as `name`' + '\n\
★**load/ld** `name`: load a saved queue' + '\n\
★**loadfrom/lf** `@user` `name`: load a saved queue from `@user`' + '\n\
★**show/sw** `@user`: show `@user`\'s saved queues' + '\n\
┗ leave `@user` blank for your saved queues' + '\n\
'
commands_control = '**join/j/jion**: bot join voice channel' + '\n\
**leave/lv/disconnect/dc/fuckoff**: bot leaves voice channel (clears queue)' + '\n\
**forceplay/fp**: for when the bot stops playing but theres still shit in the queue' + '\n\
'
commands_others = '**ping**: pong' + '\n\
**help**: helping' + '\n\
**report** `message`: send feedback' + '\n\
'
commands_others2 = '**listdir** `dir` `dir` `dir`: shows directory' + '\n\
**run** `code`: run code' + '\n\
**sync**: sync slash commands' + '\n\
'
