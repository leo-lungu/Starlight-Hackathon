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

current_emotion = None

# Function to download audio from a YouTube URL
def download_youtube_audio(url):
    yt = YouTube(url)
    audio_stream = yt.streams.filter(only_audio=True).first()
    temp_folder = tempfile.mkdtemp()
    audio_path = f"{temp_folder}/audio.webm"
    audio_stream.download(filename=audio_path)
    return audio_path

# Function to extract URLs from a playlist text
def extract_urls(playlist):
    urls = []
    for line in playlist:
        url_start = line.rfind("https://")
        if url_start != -1:
            url = line[url_start:]
            urls.append(url)
    return urls

# Function to load a random song file from a folder based on age group
def load_random_song(folder, age_group):
    subfolder = "kids" if age_group in ["3-5", "6-10"] else "teens" # TODO: Add more age groups
    folder_path = os.path.join(folder, subfolder) # Path to the folder
    files = [f for f in os.listdir(folder_path) if f.endswith(".mp3")] # List of all files in the folder
    if not files: # If no files are found, return None
        return None #   TODO: Add a default song
    random_file = random.choice(files) # Select a random file
    # Update the current_song in the session state
    st.session_state.current_song = random_file[:-4] # Remove the .mp3 extension
    return open(os.path.join(folder_path, random_file), "rb").read() # Return the file data

# Function to query YouTube API and generate a playlist
def generate_playlist(emotion, age):
    if age == "3-5" or age == "6-10":
        age = "kids"
    elif age == "10-15" or age == "15-20":
        age = "teens"
    query = f"{emotion} songs for  {age}"
    playlist = youtube_search(query, max_results=20)
    return playlist

# Initialise Streamlit session state if not already initialised
if "emotion" not in st.session_state: # TODO: Add more session state variables
    st.session_state.emotion = None # Initialise emotion in session state
    st.session_state.emotions = queue.Queue() # Initialise emotions queue in session state
    st.session_state.audio_player = None # Initialise audio player in session state
    st.session_state.scanning = False # Initialise scanning flag in session state

# Initialise current_song in session state
if "current_song" not in st.session_state: # TODO: Add more session state variables
    st.session_state.current_song = None # Initialise current_song in session state

# Function to get emotion from a frame
def get_emotion(frame): # TODO: Add more emotion detection models
    result = DeepFace.analyze(frame, actions=["emotion"], enforce_detection=False, silent=True) # Analyze the frame
    if isinstance(result, list) and len(result) > 0: # If result is a non-empty list, proceed
        emotion = result[0].get("dominant_emotion", None) # Get the dominant emotion
        if emotion: # If emotion is not None, proceed
            st.session_state.emotions.put(emotion) # Add the emotion to the emotions queue
            if st.session_state.emotions.qsize() > 50: # If the queue size is greater than 50, remove the oldest emotion
                st.session_state.emotions.get()# Remove the oldest emotion from the queue
            return emotion
    return None

# Function to get the current dominant emotion from the session state
def get_current_emotion(): # TODO: Add more emotion detection models
    emotions = list(st.session_state.emotions.queue) # Get the emotions queue
    if emotions: #  If the queue is not empty, proceed
        emotion = max(set(emotions), key=emotions.count) # Get the emotion with the highest count
        if emotions.count(emotion) > 25: # If the count of the emotion is greater than 25, return the emotion
            return emotion # Return the emotion
    return None

def play(container, encoded_song):
    container.markdown(f"""
        <audio style='width: 100%;' src='data:audio/mp3;base64,{encoded_song}'
            autoplay controls>
        </audio>""",
        unsafe_allow_html=True
    )

# convert and cache image
@st.cache_data()
def background_md():
    with open("./image/background.jpg", "rb") as f:
        data = f.read()
    bin_str = base64.b64encode(data).decode()

    # Some styling for the button toggle button
    return ("""
        <style>
            header {visibility: hidden;}
            footer {visibility: hidden;}
            .block-container {
                padding-top: 130px;
                padding-bottom: 20px;
                margin-bottom: 0px;
            }
            .stApp {
                background-image: url("data:image/png;base64,%s");
                background-size: cover;
            }
            div.stButton > button:first-child {
                background-color: #0099ff;
                color:#ffffff;
                border-color: #0099ff;
            }
            div.stButton> button:hover,
            div.stButton> button:focus,
            div.stButton> button:focus:not(:active):hover {
                background-color: #2FEF10;
                color:#ffffff;
                border-color: #2FEF10
            }
            div.stButton> button:active,
            div.stButton> button:focus:not(:active) {
                background-color: #0099ff;
                color:#ffffff;
                border-color: #0099ff
            }
        </style>
    """ % bin_str)

# Set page config
st.set_page_config(
    page_title="Starlight",
    page_icon="📷"
)

# Display the background image
st.markdown(background_md(), unsafe_allow_html=True)

# Import DeepFace for emotion recognition
with st.spinner("Welcome to Starlight! Loading Emotion Recognition Model... (This may take a while) 🚀"):
    from deepface import DeepFace # Import DeepFace

# UI elements

# Centering the content
# for i in range(2):
#     st.text("")

# Title and description
st.header("Emotion Based Music Player")
st.write("Press the button below to start scanning for emotions and find your song!")

# Debugging for the emotion detection and audio player
col1, col2, col3 = st.columns(3)
detected = col1.empty()
current = col2.empty()
playing = col3.empty()

# Initialise these fields once to prevent them from disappearing
# if not st.session_state.scanning:
detected.write(f"Detected emotion: `{st.session_state.emotion}`")
current.write(f"Current emotion: `{str(current_emotion)}`")
playing.write(f"Playing: `{str(st.session_state.current_song)}`")

# Reserving space for the audio player
audio = st.empty()

# Age group select, random song button, and scan button
st.write("Select Age Group")
col1, col2 = st.columns(2)
subcol1, subcol2 = col2.columns([0.15, 0.85])

if subcol2.button("Scan"):
    st.session_state.scanning = True
    detected.write("Detected emotion: `Scanning...`")
    current.write("Current emotion: `Scanning...`")
    playing.write("Playing: `None`")

age = col1.selectbox(
    "Select Age Group",
    ["3-5", "6-10", "10-15", "15-20"],
    2,
    label_visibility="collapsed"
)

if subcol1.button("❓", use_container_width=True):
    current_emotion = random.choice(["happy", "sad", "angry", "surprise", "neutral", "fear"])

# Emotion buttons
st.write("Or select an emotion to play a song")
col1, col2, col3, col4, col5, col6 = st.columns(6)

with col1:
   if st.button("Happy", use_container_width=True):
       current_emotion = "happy"
   st.image("image/happy.png")

with col2:
   if st.button("Sad", use_container_width=True):
       current_emotion = "sad"
   st.image("image/sad.png")


with col3:
   if st.button("Angry", use_container_width=True):
       current_emotion = "angry"
   st.image("image/angry.png")

with col4:
   if st.button("Surprised", use_container_width=True):
       current_emotion = "surprise"
   st.image("image/surprised.png")

with col5:
   if st.button("Neutral", use_container_width=True):
       current_emotion = "neutral"
   st.image("image/neutral.png")

with col6:
   if st.button("Fear", use_container_width=True):
       current_emotion = "fear"
   st.image("image/fear.png")

# Scan for emotions
if st.session_state.scanning:

    # Initialise the camera
    with st.spinner("Accessing Camera..."):
        camera = cv2.VideoCapture(0)
    while True:
        ret, frame = camera.read()
        if ret is not None:
            break

    # Main loop for the camera feed and emotion detection
    with st.spinner("Detecting Emotions..."):
        while st.session_state.scanning:
            ret, frame = camera.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) # Convert the frame to RGB
                st.session_state.emotion = get_emotion(frame)

                # If current_emotion is set by button press, skip the auto-detection
                if not current_emotion:
                    current_emotion = get_current_emotion()

                if current_emotion:
                    st.session_state.scanning = False
                    st.session_state.emotions = queue.Queue() # Reset the emotion queue for next scan

                detected.write(f"Detected emotion: `{st.session_state.emotion}`") # Update the detected emotion
                current.write(f"Current emotion: `{str(current_emotion)}`")
                playing.write(f"Playing: `{str(st.session_state.current_song)}`")

    # Release the camera after scanning is complete
    camera.release()

# Play the song using the current emotion
if current_emotion:
    with st.spinner("Loading Song..."):

        # Code for handling online and offline music
        try:
            playlist_text = generate_playlist(current_emotion, age=age)
            urls = extract_urls(playlist_text)
            random_song_url = random.choice(urls)

            if random_song_url:
                audio_path = download_youtube_audio(random_song_url)
                audio_data = open(audio_path, "rb").read()
                encoded_song = base64.b64encode(audio_data).decode("utf-8")
                st.session_state.current_song = YouTube(random_song_url).title
                play(audio, encoded_song)

        except Exception as e:
            # st.write(f"An error occurred: {e}. Playing local files.")

            # Pass the age group to the function
            song_data = load_random_song(f"music/{current_emotion}", age)
            if song_data:
                encoded_song = base64.b64encode(song_data).decode("utf-8")
                st.session_state.current_song = current_emotion
                play(audio, encoded_song)

        playing.write(f"Playing: `{str(st.session_state.current_song)}`")