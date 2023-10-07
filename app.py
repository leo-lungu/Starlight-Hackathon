# Import required libraries
import cv2
import streamlit as st
import queue
import base64
import os
import random

from youtubeAPIHandler import youtube_search



# Load happy and sad mp3 files
happy = open("music/happy.mp3", "rb").read()
sad = open("music/sad.mp3", "rb").read()
# Function to load a random mp3 file from a given folder
def load_random_song(folder):
    files = [f for f in os.listdir(folder) if f.endswith('.mp3')]
    if not files:
        return None
    random_file = random.choice(files)
    return open(os.path.join(folder, random_file), "rb").read()

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
    st.session_state.scanning = True  # Add a scanning flag

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
audio = st.markdown("", unsafe_allow_html=True)


# Add button to toggle camera visibility
if st.button("Toggle Camera"):
    st.session_state.show_camera = not st.session_state.show_camera

# Only create the image placeholder if the camera is enabled
if st.session_state.show_camera:
    FRAME_WINDOW = st.image([])  # Initialize image placeholder
else:
    FRAME_WINDOW = None  # Set to None to skip updating the frame

# Start the camera
with st.spinner("Accessing Camera..."):
    camera = cv2.VideoCapture(0)
with st.spinner("Starting Camera..."):
    while True:
        ret, frame = camera.read()
        if ret is not None:
            break

# Main loop for the camera feed
while st.session_state.scanning:  # Continue scanning while the flag is True
    ret, frame = camera.read()
    if ret:
        # Convert the frame color to RGB
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Only update the frame if the camera is enabled
        if st.session_state.show_camera and FRAME_WINDOW is not None:
            FRAME_WINDOW.image(frame, use_column_width=True)

        # Update session state with detected emotion
        st.session_state.emotion = get_emotion(frame)
        current_emotion = get_current_emotion()

        # Update current emotion if it's changed and is not None
        if current_emotion and (current_emotion != st.session_state.playing):
            st.session_state.playing = current_emotion
            
            # Load random song based on current emotion 
            song_data = load_random_song(f"music/{current_emotion}")
            if song_data:
                encoded_song = base64.b64encode(song_data).decode('utf-8')
                audio.markdown(f'<audio style="width: 100%;" src="data:audio/mp3;base64,{encoded_song}" autoplay controls></audio>', unsafe_allow_html=True)

        detected.write(f"Detected emotion: `{st.session_state.emotion}`")
        current.write(f"Current emotion: `{str(current_emotion)}`")
        playing.write(f"Playing: `{str(st.session_state.playing)}`")

        # Update current emotion if it's changed
        if current_emotion != st.session_state.emotion:
            if current_emotion == "happy":
                st.session_state.emotion = current_emotion
            elif current_emotion == "sad":
                st.session_state.emotion = current_emotion

        # Play audio based on the current emotion
        if current_emotion == "happy":
            if st.session_state.playing != current_emotion:
                st.session_state.playing = current_emotion
                encoded_happy = base64.b64encode(happy).decode('utf-8')
                audio.markdown('<audio  style="width: 100%;" src="data:audio/mp3;base64,{}" autoplay controls></audio>'.format(encoded_happy), unsafe_allow_html=True)
                st.session_state.scanning = False  # Stop scanning when happy emotion is detected
        elif current_emotion == "sad":
            if st.session_state.playing != current_emotion:
                st.session_state.playing = current_emotion
                encoded_sad = base64.b64encode(sad).decode('utf-8')
                audio.markdown('<audio style="width: 100%;" src="data:audio/mp3;base64,{}" autoplay controls></audio>'.format(encoded_sad), unsafe_allow_html=True)
                st.session_state.scanning = False  # Stop scanning when sad emotion is detected

# Release the camera when scanning is finished
camera.release()
# "Scan Again" button to restart scanning
if st.button("Scan Again"):
    st.session_state.scanning = True  # Set the scanning flag to True to start scanning again


# Incorporate following code:
# Determine current mood
emotion = "happy"
age = 21

# Generate and display playlist
playlist = generate_playlist(emotion, age)

st.write("Generated Playlist:")
for song in playlist:
    st.write(song)