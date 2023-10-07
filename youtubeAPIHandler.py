from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv
import os

load_dotenv()
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

def youtube_search(query, max_results=10):
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    
    search_response = youtube.search().list(
        q=query,
        type='video',
        part='id,snippet',
        maxResults=max_results
    ).execute()
    
    videos = []
    for search_result in search_response.get('items', []):
        videos.append(f"{search_result['snippet']['title']} (https://www.youtube.com/watch?v={search_result['id']['videoId']})")
    
    return videos