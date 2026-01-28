# Mini Pupper AI Voice Control

A clean, minimal ROS2 package for AI-powered voice control of Mini Pupper.

## Features

- **Intent Classification**: Uses Google Gemini to understand natural language commands
- **Pre-programmed Responses**: Fast, predictable robot behavior
- **ROS2 Native**: Publishes to `/cmd_vel` - works with standard Mini Pupper bringup
- **Minimal Dependencies**: No langchain, no complex dependency chains
- **Fallback Mode**: Works even without internet (keyword matching)

## Architecture

```
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐    ┌──────────┐
│ Microphone  │───▶│ Google STT   │───▶│ Gemini Intent   │───▶│ /cmd_vel │
│             │    │ (on device)  │    │ Classification  │    │          │
└─────────────┘    └──────────────┘    └─────────────────┘    └──────────┘
                                              │
                                              ▼
                                    ┌─────────────────┐
                                    │ Pre-programmed  │
                                    │ Response + Move │
                                    └─────────────────┘
```

## Installation

### 1. Install Python Dependencies

```bash
# Required (uses sounddevice which already works on Mini Pupper!)
pip3 install google-genai sounddevice soundfile SpeechRecognition --break-system-packages

# Optional: For text-to-speech
pip3 install pyttsx3 --break-system-packages
# OR (better quality, needs internet)
pip3 install gTTS pygame --break-system-packages
```

### 2. Install the ROS2 Package

```bash
cd ~/ros2_ws/src
# Copy or clone pupper_ai_voice here

cd ~/ros2_ws
colcon build --packages-select pupper_ai_voice
source install/setup.bash
```

### 3. Set Your API Key

Get a free API key from [Google AI Studio](https://aistudio.google.com/apikey)

```bash
export GOOGLE_API_KEY="your-api-key-here"

# Add to .bashrc for persistence:
echo 'export GOOGLE_API_KEY="your-api-key-here"' >> ~/.bashrc
```

## Usage

### Start the Robot First

```bash
# Terminal 1: Start Mini Pupper
ros2 launch mini_pupper_bringup bringup.launch.py
```

### Option A: Voice Control (with microphone)

```bash
# Terminal 2: Start voice control
ros2 run pupper_ai_voice ai_voice_control
```

Then speak commands like:
- "Move forward"
- "Turn left"
- "Dance"
- "Stop"
- "Help" (to hear all commands)

### Option B: Keyboard Control (for testing)

```bash
# Terminal 2: Start keyboard control
ros2 run pupper_ai_voice keyboard_control
```

Then type commands:
```
> move forward
> dance
> hello
> help
> quit
```

### Option C: Add Text-to-Speech

```bash
# Terminal 3: Start TTS node
ros2 run pupper_ai_voice tts_node

# Then publish text to speak:
ros2 topic pub /ai/speak std_msgs/msg/String "{data: 'Hello world'}" --once
```

## Available Commands

| Command | What it does |
|---------|--------------|
| move forward / come here | Walk forward |
| move backward / go back | Walk backward |
| turn left / turn right | Turn in place |
| spin | Spin around |
| dance | Do a dance! |
| stop | Stop moving |
| hello / hi | Greeting |
| goodbye / bye | Say goodbye |
| help | List commands |
| shut up / sleep | Stop listening |
| wake up | Start listening again |

## Customization

### Adding New Commands

Edit `ai_voice_control.py` and add one line to `INTENT_CONFIG`:

```python
INTENT_CONFIG = [
    # ... existing commands ...
    
    # Add your new command here!
    # Format: (intent_name, response_text, linear_x, angular_z, duration)
    ("my_command", "Doing my thing!", 0.1, 0.5, 2.0),
]
```

Then update the `CLASSIFIER_PROMPT` to include your new intent.

### Adjusting Movement Speeds

Modify the values in `INTENT_CONFIG`:
- `linear_x`: Forward/backward speed (0.15 = walking pace)
- `angular_z`: Turn rate (0.5 = gentle turn, 1.0 = fast spin)
- `duration`: How long to execute (seconds)

### Changing the Voice

For TTS, modify `tts_node.py` or use a different TTS service.

## Topics

| Topic | Type | Description |
|-------|------|-------------|
| `/cmd_vel` | `geometry_msgs/Twist` | Movement commands (output) |
| `/ai/speech_text` | `std_msgs/String` | What was heard (output) |
| `/ai/intent` | `std_msgs/String` | Classified intent (output) |
| `/ai/speak` | `std_msgs/String` | Text to speak (input to TTS) |

## Troubleshooting

### "No module named sounddevice"
```bash
pip3 install sounddevice soundfile --break-system-packages
```

### "No module named speech_recognition"
```bash
pip3 install SpeechRecognition --break-system-packages
```

### Microphone not working
```bash
# Test microphone
arecord -d 3 test.wav && aplay test.wav

# List audio devices
arecord -l
```

### Robot not moving
1. Make sure bringup is running: `ros2 topic list | grep cmd_vel`
2. Check if commands are being published: `ros2 topic echo /cmd_vel`

### API key not working
1. Check it's set: `echo $GOOGLE_API_KEY`
2. Test directly:
```python
from google import genai
client = genai.Client(api_key="your-key")
response = client.models.generate_content(model="gemini-2.0-flash", contents="Hello")
print(response.text)
```

## License

Apache 2.0
