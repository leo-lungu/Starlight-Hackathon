import cv2
from deepface import DeepFace
import pygame

# Initialize pygame mixer 
pygame.mixer.init()

# Load audio files
happy_sound = pygame.mixer.Sound('/music/happy.mp3')
sad_sound = pygame.mixer.Sound('/music/sad.mp3')

# Initialize webcam
cap = cv2.VideoCapture(0)  

while True:
    # Capture frame
    ret, frame = cap.read()

    # Detect emotion
    try:
        result = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
            
        if isinstance(result, list) and len(result) > 0:
            emotion = result[0].get('dominant_emotion', "N/A")
        else:
            emotion = "N/A"

    except Exception as e:
        print(f"Exception: {e}")
        emotion = "Error"

    # Play audio based on emotion
    if emotion == "happy":
        happy_sound.play()
    elif emotion == "sad":
        sad_sound.play()

    # Display emotion text on frame 
    cv2.putText(frame, emotion, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
        
    # Display frame
    cv2.imshow('Emotion Detector', frame)

    # Break loop with 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
        
# Release resources
cap.release()
cv2.destroyAllWindows()