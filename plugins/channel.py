from pyrogram import Client, filters
from info import *
from database.aks_files import save_file, unpack_new_file_id
from utils import get_poster, temp
from Script import script
from database.users_chats_db import db
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

processed_movies = set()
media_filter = filters.document | filters.video


media_filter = filters.document | filters.video

@Client.on_message(filters.chat(CHANNELS) & media_filter)
async def media(bot, message):
    media = getattr(message, message.media.value, None)
    if media.mime_type in ['video/mp4', 'video/x-matroska']:  # Non .mp4 and .mkv files are skipped
        media.file_type = message.media.value
        media.caption = message.caption
        success_sts = await save_file(media)
        if success_sts == 'suc':
            file_id, file_ref = unpack_new_file_id(media.file_id)
            await send_movie_updates(bot, file_name=media.file_name, file_id=file_id)


def extract_year(file_name):
    """Extracts the year from the file name."""
    match = re.search(r'\b(19\d{2}|20\d{2})\b', file_name)
    if match:
        return match.group(1)
    return None


def extract_language(file_name):
    """Extracts the language from the file name."""
    language_patterns = [
        r'\b(Hindi|English|Tamil|Telugu|Malayalam|Kannada)\b',
    ]
    for pattern in language_patterns:
        match = re.search(pattern, file_name, re.IGNORECASE)
        if match:
            return match.group(1)
    return None

def name_format(file_name: str):
    file_name = file_name.lower()
    file_name = re.sub(r'http\S+', '', re.sub(r'@\w+|#\w+', '', file_name).replace('_', ' ').replace('[', '').replace(']', '')).strip()
    file_name = re.split(r's\d+|season\s*\d+|chapter\s*\d+', file_name, flags=re.IGNORECASE)[0]
    file_name = file_name.strip()
    words = file_name.split()[:4]
    file_name = ' '.join(words)
    return file_name 

async def get_imdb(file_name):
    imdb_file_name = name_format(file_name)
    imdb = await get_poster(imdb_file_name)
    if imdb:
        return imdb.get('title'), imdb.get('poster')
    return None, None    

async def send_movie_updates(bot, file_name, file_id):
    poster_url, movie_name = await get_imdb(file_name)    
    #movie_name = movie_name.title()
    year = extract_year(file_name)
    language = extract_language(file_name)              
    if movie_name in processed_movies:
        return
    processed_movies.add(movie_name)        
    btn = [
        [InlineKeyboardButton('Get File', url=MOVIE_GROUP_LINK)]
    ]
    reply_markup = InlineKeyboardMarkup(btn)    
    try:
        if poster_url:
            await bot.send_photo( 
                chat_id=LOG_CHANNEL,
                photo=poster_url,
                caption=script.INDEX_FILE_TXT.format(movie_name, year, language),
                reply_markup=reply_markup)
        else:
            await bot.send_message( 
                chat_id=LOG_CHANNEL,
                text=script.INDEX_FILE_TXT.format(movie_name, year, language),
                reply_markup=reply_markup)
    except Exception as e:
        print('ꜰᴀɪʟᴇᴅ ᴛᴏ ꜱᴇɴᴅ ᴍᴏᴠɪᴇ ᴜᴘᴅᴀᴛᴇ. ᴇʀʀᴏʀ - ', e)
        await bot.send_message(LOG_CHANNEL, f'ꜰᴀɪʟᴇᴅ ᴛᴏ ꜱᴇɴᴅ ᴍᴏᴠɪᴇ ᴜᴘᴅᴀᴛᴇ. ᴇʀʀᴏʀ - {e}')
