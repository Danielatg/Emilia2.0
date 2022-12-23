import asyncio
import re
import os
from typing import Union
from datetime import datetime
from typing import List
from imdb import IMDb

imdb = IMDb() 

async def get_poster(query, bulk=False, id=False):
    return {}
    if not id:
        # https://t.me/GetTGLink/4183
        pattern = re.compile(r"^(([a-zA-Z\s])*)?\s?([1-2]\d\d\d)?", re.IGNORECASE)
        match = pattern.match(query)
        year = None
        if match:
            title = match.group(1)
            year = match.group(3)
        else:
            title = query
        movieid = imdb.search_movie(title.lower(), results=10)
        if not movieid:
            return None
        if year:
            filtered=list(filter(lambda k: str(k.get('year')) == str(year), movieid))
            if not filtered:
                filtered = movieid
        else:
            filtered = movieid
        movieid=list(filter(lambda k: k.get('kind') in ['movie', 'tv series'], filtered))
        if not movieid:
            movieid = filtered
        if bulk:
            return movieid
        movieid = movieid[0].movieID
    else:
        movieid = int(query)
    movie = imdb.get_movie(movieid)
    title = movie.get('title')
    genres = ", ".join(movie.get("genres")) if movie.get("genres") else None
    rating = str(movie.get("rating"))
    if movie.get("original air date"):
        date = movie["original air date"]
    elif movie.get("year"):
        date = movie.get("year")
    else:
        date = "N/A"
    poster = movie.get('full-size cover url')
    plot = movie.get('plot outline')
    if plot and len(plot) > 800:
        plot = plot[0:800] + "..."
    return {
        'title': title,
        'year': date,
        'genres': genres,
        'poster': poster,
        'plot': plot,
        'rating': rating,        
        'url':f'https://www.imdb.com/title/tt{movieid}'

    }
