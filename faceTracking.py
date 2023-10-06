import cv2
from deepface import DeepFace
import pygame

# Initialize pygame mixer
pygame.mixer.init() 

# Load audio files
happy_sound = pygame.mixer.Sound('/music/happy.mp3')
sad_sound = pygame.mixer.Sound('/music/sad.mp3')

# Initialize the webcam
cap = cv2.VideoCapture(0)  # 0 for the default webcam

while True:
    # Capture frame-by-frame
    ret, frame = cap.read()
    
    # Perform emotion analysis
    try:
        result = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
        
        # If result is a non-empty list, proceed
        if isinstance(result, list) and len(result) > 0:
            emotion = result[0].get('dominant_emotion', "N/A")
        else:
            emotion = "N/A"

    except Exception as e:
        print(f"An exception occurred: {e}")
        emotion = "Error"
    
    # Display the emotion on the frame
    cv2.putText(frame, emotion, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
    
    # Display the frame with the emotion text
    cv2.imshow('Emotion Detector', frame)
    
    # Press 'q' to quit the application
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the webcam and destroy all OpenCV windows
cap.release()

while True:

    # Emotion detection
    
    if emotion == "happy":
        happy_sound.play()
    elif emotion == "sad":
        sad_sound.play()
        
    # Rest of loop...

