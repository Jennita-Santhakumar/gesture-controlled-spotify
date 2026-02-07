import mediapipe as mp
import cv2
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pyautogui
import webbrowser
import time
from flask import Flask, request
import threading

SPOTIFY_CLIENT_ID = "Your-client_id"
SPOTIFY_CLIENT_SECRET = "Your-client_secret"
REDIRECT_URI = "Your-redirect_uri"

# Spotify Authentication
sp = None
auth_completed = False

# Flask app for handling the redirect
app = Flask(__name__)
server_thread = None


@app.route("/callback")
def callback():
    global sp, auth_completed
    try:
        code = request.args.get('code')
        if not code:
            return "Error: No authorization code provided", 400

        # Fix the deprecated approach
        token_info = auth_manager.get_access_token(code, check_cache=False)
        access_token = token_info['access_token']
        sp = spotipy.Spotify(auth=access_token)
        auth_completed = True
        print("Spotify Authentication successful!")
        return "Authentication successful! You can close this window."
    except Exception as e:
        print(f"Authentication error: {str(e)}")
        return f"Authentication error: {str(e)}", 500


# Start the Flask server in a separate thread
def run_flask_server():
    app.run(port=8888, debug=False)


def change_spotify_volume(direction):
    try:
        # Get current playback state
        current_playback = sp.current_playback()
        if not current_playback:
            print("No active playback found")
            return

        # Get current volume
        current_volume = current_playback['device']['volume_percent']

        # Adjust volume (in 5% increments)
        if direction == "up":
            new_volume = min(100, current_volume + 5)
        else:
            new_volume = max(0, current_volume - 5)

        # Set new volume
        sp.volume(new_volume)
        print(f"Spotify volume set to {new_volume}%")

    except Exception as e:
        print(f"Error changing volume: {str(e)}")


# Gesture detection class to encapsulate the functionality
class GestureController:
    def __init__(self):
        # MediaPipe Setup
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5
        )
        self.mp_draw = mp.solutions.drawing_utils

        # Gesture cooldown to prevent rapid triggering
        self.last_gesture_time = 0
        self.cooldown_period = 1.0  # seconds

        # Store previous gesture to detect changes
        self.previous_gesture = None

    def get_fingers_up(self, hand_landmarks):
        """Returns a list like [thumb, index, middle, ring, pinky] -> 1 = up, 0 = down"""
        tip_ids = [4, 8, 12, 16, 20]
        fingers = []

        # Thumb - check based on hand orientation
        if hand_landmarks.landmark[tip_ids[0]].x < hand_landmarks.landmark[tip_ids[0] - 1].x:
            fingers.append(1)
        else:
            fingers.append(0)

        # Other four fingers
        for id in range(1, 5):
            if hand_landmarks.landmark[tip_ids[id]].y < hand_landmarks.landmark[tip_ids[id] - 2].y:
                fingers.append(1)
            else:
                fingers.append(0)

        return fingers

    def detect_gesture(self, fingers):
        """Decides action based on finger state"""
        if fingers == [0, 1, 1, 0, 0]:  # Peace ✌️
            return "pause"
        elif fingers == [0, 0, 0, 0, 0]:  # Fist ✊
            return "play"
        elif fingers == [1, 0, 0, 0, 0]:  # Thumbs up 👍
            return "volume_up"
        elif fingers == [0, 0, 0, 0, 1]:  # Pinky only (thumbs down 👎 alternative)
            return "volume_down"
        elif fingers == [1, 1, 0, 0, 0]:  # Thumb and index finger (next track)
            return "next_track"
        elif fingers == [1, 1, 1, 0, 0]:  # Thumb, index, and middle (previous track)
            return "previous_track"
        else:
            return None

    def process_gesture(self, gesture):
        """Execute actions based on detected gesture with cooldown"""
        current_time = time.time()

        # Only process gesture if cooldown has passed and it's different from previous
        if (current_time - self.last_gesture_time > self.cooldown_period and
                gesture != self.previous_gesture and
                gesture is not None and
                sp is not None):

            try:
                if gesture == "pause":
                    print("Peace Sign detected! Pausing music...")
                    sp.pause_playback()
                elif gesture == "play":
                    print("Fist detected! Playing music...")
                    active_device = get_active_device()
                    if active_device:
                        sp.start_playback(device_id=active_device)
                elif gesture == "volume_up":
                    print("Thumbs Up detected! Volume Up...")
                    change_spotify_volume("up")  # Use Spotify API for volume control
                elif gesture == "volume_down":
                    print("Pinky detected! Volume Down...")
                    change_spotify_volume("down")  # Use Spotify API for volume control
                elif gesture == "next_track":
                    print("Next track gesture detected!")
                    sp.next_track()
                elif gesture == "previous_track":
                    print("Previous track gesture detected!")
                    sp.previous_track()

                self.last_gesture_time = current_time
                self.previous_gesture = gesture
            except Exception as e:
                print(f"Error executing gesture: {str(e)}")


def authenticate_spotify():
    global sp, auth_manager, server_thread

    # Your Spotify API credentials
    CLIENT_ID = "b05d01e148514893b1357abb4ab29fd7"
    CLIENT_SECRET = "0f3ed20fc28a4750a6e7c4f4e0b5b642"
    REDIRECT_URI = "http://127.0.0.1:8888/callback"

    # Initialize auth manager
    auth_manager = SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope="user-modify-playback-state user-read-playback-state"
    )

    # Start Flask server in a separate thread
    server_thread = threading.Thread(target=run_flask_server)
    server_thread.daemon = True
    server_thread.start()

    # Open authorization URL
    auth_url = auth_manager.get_authorize_url()
    print("Please visit this URL to authorize the application:")
    print(auth_url)
    webbrowser.open(auth_url)

    # Wait for authentication to complete
    print("Waiting for authentication...")
    timeout = 60  # seconds
    start_time = time.time()
    while not auth_completed and time.time() - start_time < timeout:
        time.sleep(0.5)

    if not auth_completed:
        print("Authentication timed out. Please try again.")
        return False

    return True


def get_active_device():
    try:
        devices = sp.devices()
        if not devices or 'devices' not in devices:
            print("No devices found or unable to fetch devices")
            return None

        # First try to find an active device
        for device in devices['devices']:
            if device['is_active']:
                return device['id']

        # If no active device, use the first available one
        if devices['devices']:
            device_id = devices['devices'][0]['id']
            print(f"No active device found, using: {devices['devices'][0]['name']}")
            return device_id

        return None
    except Exception as e:
        print(f"Error getting devices: {str(e)}")
        return None


def main():
    if not authenticate_spotify():
        print("Failed to authenticate with Spotify.")
        return

    controller = GestureController()
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Could not open camera.")
        return

    print("Starting hand gesture control. Press 'q' to quit.")
    print("Recognized gestures:")
    print("- Peace sign (✌️): Pause music")
    print("- Fist (✊): Play music")
    print("- Thumbs up (👍): Volume up")
    print("- Pinky up (🤙): Volume down")
    print("- Thumb + index: Next track")
    print("- Thumb + index + middle: Previous track")

    try:
        while True:
            success, img = cap.read()
            if not success:
                print("Failed to get frame from camera")
                break

            # Flip the image horizontally for a more intuitive mirror view
            img = cv2.flip(img, 1)

            # Convert to RGB for MediaPipe
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            results = controller.hands.process(img_rgb)

            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    # Draw hand landmarks
                    controller.mp_draw.draw_landmarks(
                        img,
                        hand_landmarks,
                        controller.mp_hands.HAND_CONNECTIONS
                    )

                    # Get finger positions and detect gesture
                    fingers = controller.get_fingers_up(hand_landmarks)
                    gesture = controller.detect_gesture(fingers)

                    # Display detected gesture on screen
                    if gesture:
                        cv2.putText(
                            img,
                            f"Gesture: {gesture}",
                            (10, 50),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            1,
                            (0, 255, 0),
                            2
                        )

                    # Process the detected gesture
                    controller.process_gesture(gesture)

            # Display FPS
            fps = cap.get(cv2.CAP_PROP_FPS)
            cv2.putText(
                img,
                f"FPS: {int(fps)}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (255, 0, 0),
                2
            )

            # Show the image
            cv2.imshow("Hand Gesture Controller", img)

            # Break the loop when 'q' is pressed
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        # Clean up resources
        cap.release()
        cv2.destroyAllWindows()
        print("Application closed.")


if __name__ == "__main__":
    main()