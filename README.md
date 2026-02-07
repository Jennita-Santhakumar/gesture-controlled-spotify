Gesture Controlled Spotify Player

A Python-based application that enables users to control Spotify(Premium) playback using hand gestures detected via a webcam.
This project combines computer vision with the Spotify Web API to provide a seamless, touch-free music control experience.

Features

Real-time hand gesture detection using MediaPipe
Play and pause Spotify playback
Control volume through hand gestures
Skip tracks hands-free
Secure Spotify authentication using OAuth
Live webcam-based interaction

Technologies Used

Python
MediaPipe
OpenCV
Flask
Spotify Web API (Spotipy)

Project Structure
gesture-controlled-spotify/
│
├── gesture_tracker.py
├── .gitignore
└── README.md

Installation
Step 1: Clone the Repository
git clone https://github.com/Jennita-Santhakumar/gesture-controlled-spotify.git

Step 2: Navigate to the Project Directory
cd gesture-controlled-spotify

Step 3: Create and Activate a Virtual Environment
python -m venv venv
venv\Scripts\activate

Step 4: Install Required Dependencies
pip install opencv-python mediapipe flask spotipy

Spotify API Configuration

Visit the Spotify Developer Dashboard
https://developer.spotify.com/dashboard

Create a new application

Add the following Redirect URI:
http://127.0.0.1:8888/callback
Save your Client ID and Client Secret securely

Running the Application
python gesture_tracker.py

Workflow:

A browser window opens for Spotify authorization
Grant access to your Spotify account
Webcam activates automatically
Control Spotify playback using hand gestures
