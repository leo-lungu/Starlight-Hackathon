# Import required libraries
import cv2
import streamlit as st
import queue
import base64
import os
import random
from pytube import YouTube
import tempfile

from youtubeAPIHandler import youtube_search




def download_youtube_audio(url):
    yt = YouTube(url)
    audio_stream = yt.streams.filter(only_audio=True).first()
    temp_folder = tempfile.mkdtemp()
    audio_path = f"{temp_folder}/{yt.title}.webm"
    audio_stream.download(filename=audio_path)
    return audio_path

def extract_urls(playlist):
    urls = []
    for line in playlist:
        url_start = line.rfind("https://")
        if url_start != -1:
            url = line[url_start:]
            urls.append(url)
    return urls

# Function to load a random mp3 file from a given folder
def load_random_song(folder, age_group):
    subfolder = "kids" if age_group in ['3-5', '6-10'] else "teens"
    folder_path = os.path.join(folder, subfolder)
    files = [f for f in os.listdir(folder_path) if f.endswith('.mp3')]
    
    if not files:
        return None
    
    random_file = random.choice(files)
    return open(os.path.join(folder_path, random_file), "rb").read()

# Query YouTube and generate a playlist
def generate_playlist(emotion, age):
    query = f"{emotion} songs for age {age}"
    playlist = youtube_search(query, max_results=20)
    return playlist


# Initialize session state if not already done
if "emotion" not in st.session_state:
    st.session_state.emotion = None
    st.session_state.emotions = queue.Queue()
    st.session_state.playing = None
    st.session_state.audio_player = None
    st.session_state.scanning = False  # Add a scanning flag

# Import DeepFace for emotion recognition
with st.spinner("Importing DeepFace..."):
    from deepface import DeepFace

# Function to get the emotion from a given frame
def get_emotion(frame):
    result = DeepFace.analyze(frame, actions=["emotion"], enforce_detection=False, silent=True)
    if isinstance(result, list) and len(result) > 0:
        emotion = result[0].get("dominant_emotion", None)
        if emotion:
            st.session_state.emotions.put(emotion)
            # Maintain the queue length to 50
            if st.session_state.emotions.qsize() > 50:
                st.session_state.emotions.get()
            return emotion
    return None

# Function to get the current dominant emotion
def get_current_emotion():
    emotions = list(st.session_state.emotions.queue)
    if emotions:
        emotion = max(set(emotions), key=emotions.count)
        # Minimum count for a dominant emotion to be valid
        if emotions.count(emotion) > 25:
            return emotion
    return None

# UI elements
st.header("Face Tracking")
col1, col2, col3 = st.columns(3)
detected = col1.empty()
current = col2.empty()
playing = col3.empty()
audio = st.empty()  # Use empty() for dynamic content

# "Scan Again" button to restart scanning
if st.button("Scan"):
    st.session_state.scanning = True  # Set the scanning flag to True to start scanning again

# Adding the dropdown for age selection
with col1:
    age = st.selectbox('Select Age Group', ['3-5', '6-10', '10-15', '15-20'])





# Start the camera
with st.spinner("Accessing Camera..."):
    camera = cv2.VideoCapture(0)
with st.spinner("Starting Camera..."):
    while True:
        ret, frame = camera.read()
        if ret is not None:
            break


#Main loop for the camera feed
while st.session_state.scanning:  # Continue scanning while the flag is True
    ret, frame = camera.read()
    if ret:
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        st.session_state.emotion = get_emotion(frame)
        current_emotion = get_current_emotion()

        if current_emotion and (current_emotion != st.session_state.playing):
            st.session_state.playing = current_emotion

            try:
                playlist_text = generate_playlist(current_emotion, age=age)
                urls = extract_urls(playlist_text)
                random_song_url = random.choice(urls)
                
                if random_song_url:
                    audio_path = download_youtube_audio(random_song_url)
                    audio_data = open(audio_path, "rb").read()
                    st.audio(audio_data, format="audio/webm")
                
                st.session_state.scanning = False
                
            except Exception as e:
                st.write(f"Can't reach The internet, Offline songs Active.")
                
                # Pass the age group to the function
                song_data = load_random_song(f"music/{current_emotion}", age)
                if song_data:
                    encoded_song = base64.b64encode(song_data).decode('utf-8')
                    audio.markdown(f'<audio style="width: 100%;" src="data:audio/mp3;base64,{encoded_song}" autoplay controls></audio>', unsafe_allow_html=True)
    
                st.session_state.scanning = False
                
               

        detected.write(f"Detected emotion: `{st.session_state.emotion}`")
        current.write(f"Current emotion: `{str(current_emotion)}`")
        playing.write(f"Playing: `{str(st.session_state.playing)}`")


    



# Release the camera when scanning is finished
camera.release()






