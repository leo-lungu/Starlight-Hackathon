import cv2
import streamlit as st
import queue

happy = open("music/happy.mp3", "rb").read()
sad = open("music/sad.mp3", "rb").read()

if "emotion" not in st.session_state:
    st.session_state.emotion = None
    st.session_state.emotions = queue.Queue()
    st.session_state.playing = None
    st.session_state.audio_player = None

with st.spinner("Importing DeepFace..."):
    from deepface import DeepFace

def get_emotion(frame):
    result = DeepFace.analyze(frame, actions=["emotion"], enforce_detection=False, silent=True)
    if isinstance(result, list) and len(result) > 0:
        emotion = result[0].get("dominant_emotion", None)
        if emotion:
            st.session_state.emotions.put(emotion)
            if st.session_state.emotions.qsize() > 50:
                st.session_state.emotions.get()
        return emotion
    return None

def get_current_emotion():
    emotions = list(st.session_state.emotions.queue)
    if emotions:
        emotion = max(set(emotions), key=emotions.count)
        if emotions.count(emotion) > 25:
            return emotion
    return None

st.header("Face Tracking")

col1, col2, col3 = st.columns(3)
detected = col1.empty()
current = col2.empty()
playing = col3.empty()
audio = st.empty()

FRAME_WINDOW = st.image([])
with st.spinner("Accessing Camera..."):
    camera = cv2.VideoCapture(0)
with st.spinner("Starting Camera..."):
    while True:
        ret, frame = camera.read()
        if ret is not None:
            break

while True:
    ret, frame = camera.read()
    if ret:
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        FRAME_WINDOW.image(frame, use_column_width=True)

        st.session_state.emotion = get_emotion(frame)
        current_emotion = get_current_emotion()

        detected.write(f"Detected emotion: `{st.session_state.emotion}`")
        current.write(f"Current emotion: `{str(current_emotion)}`")
        playing.write(f"Playing: `{str(st.session_state.playing)}`")

        if current_emotion != st.session_state.emotion:
            if current_emotion == "happy":
                st.session_state.emotion = current_emotion
            elif current_emotion == "sad":
                st.session_state.emotion = current_emotion

        if current_emotion == "happy":
            if st.session_state.playing != current_emotion:
                st.session_state.playing = current_emotion
                audio.audio(happy, format="audio/mp3", start_time=0)

        elif current_emotion == "sad":
            if st.session_state.playing != current_emotion:
                st.session_state.playing = current_emotion
                audio.audio(sad, format="audio/mp3", start_time=0)