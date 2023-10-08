# Import required libraries
import cv2
import streamlit as st
import queue
import base64
import os
import random

# Function to load a random mp3 file from a given folder


def load_random_song(folder):
    files = [f for f in os.listdir(folder) if f.endswith('.mp3')]
    if not files:
        return None
    random_file = random.choice(files)
    return open(os.path.join(folder, random_file), "rb").read()


# Initialize session state if not already done
if "emotion" not in st.session_state:
    st.session_state.emotion = None
    st.session_state.emotions = queue.Queue()
    st.session_state.playing = None
    st.session_state.audio_player = None
    st.session_state.show_camera = False

# Import DeepFace for emotion recognition
with st.spinner("Importing DeepFace..."):
    from deepface import DeepFace

# Function to get the emotion from a given frame


def get_emotion(frame):
    result = DeepFace.analyze(
        frame, actions=["emotion"], enforce_detection=False, silent=True)
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


# convert and cache image
@st.cache_data()
def get_markdown_with_background():
    with open('./image/background.jpg', 'rb') as f:
        data = f.read()
    bin_str = base64.b64encode(data).decode()
    background_str = ('''
<style>
    .stApp {
    background-image: url("data:image/png;base64,%s");
    background-size: cover;
    }

    div.stButton > button:first-child {
    background-color: #0099ff;
    color:#ffffff;
    border-color: #0099ff;
    }
    div.stButton> button:hover, div.stButton> button:focus, div.stButton> button:focus:not(:active):hover {
    background-color: #2FEF10;
    color:#ffffff;
    border-color: #2FEF10
    }
     
    div.stButton> button:active,  div.stButton> button:focus:not(:active) {
    background-color: #0099ff;
    color:#ffffff;
    border-color: #0099ff
    }
</style>

''' % bin_str)
    return background_str


# UI elements
st.header("Face Tracking")
markdown_str = get_markdown_with_background()
col1, col2, col3 = st.columns(3)
detected = col1.empty()
current = col2.empty()
playing = col3.empty()
audio = st.markdown(markdown_str+"", unsafe_allow_html=True)


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
while True:
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
                audio.markdown(
                    markdown_str+f'''<audio style="width: 100%;"
                    src="data:audio/mp3;base64,{encoded_song}" autoplay controls></audio>''',
                    unsafe_allow_html=True)

        detected.write(f"Detected emotion: `{st.session_state.emotion}`")
        current.write(f"Current emotion: `{str(current_emotion)}`")
        playing.write(f"Playing: `{str(st.session_state.playing)}`")
