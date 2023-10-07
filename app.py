# Import required libraries
import cv2
import streamlit as st
import queue
import base64

# Load happy and sad mp3 files
happy = open("music/happy.mp3", "rb").read()
sad = open("music/sad.mp3", "rb").read()

# Initialize session state if not already done
if "emotion" not in st.session_state:
    st.session_state.emotion = None
    st.session_state.emotions = queue.Queue()
    st.session_state.playing = None
    st.session_state.audio_player = None

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
FRAME_WINDOW = st.image([])

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
        FRAME_WINDOW.image(frame, use_column_width=True)

        # Update session state with detected emotion
        st.session_state.emotion = get_emotion(frame)
        current_emotion = get_current_emotion()

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
        elif current_emotion == "sad":
            if st.session_state.playing != current_emotion:
                st.session_state.playing = current_emotion
                encoded_sad = base64.b64encode(sad).decode('utf-8')
                audio.markdown('<audio style="width: 100%;" src="data:audio/mp3;base64,{}" autoplay controls></audio>'.format(encoded_sad), unsafe_allow_html=True)