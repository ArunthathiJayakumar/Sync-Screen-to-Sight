# 🎤 Voice-Based Features Guide

## Overview
This application now supports voice-based input for eye testing and brightness adjustment. You can speak letters during the vision test and set your eye power value using voice commands.

## Features

### 1. Voice Input for Letter Recognition During Eye Test
- **Location**: Vision Test Page (`/start_test_page/`)
- **How to Use**:
  1. Start the vision test as usual
  2. When a letter is displayed, click the **"Speak Letter"** button (microphone icon)
  3. Speak the letter you see on the chart
  4. The system will recognize your voice and check if it matches the correct letter
  5. You can also still use the button clicks if preferred

- **Supported Letters**: 
  - Е (E) - Say "E" or "Eh"
  - М (M) - Say "M" or "Em"
  - Э (W) - Say "W" or "Double U"
  - Ш (S) - Say "S" or "Sh"

- **Browser Requirements**: 
  - Chrome, Edge, or Safari (Web Speech API support)
  - Microphone permissions must be granted

### 2. Voice Input for Eye Power Value with Auto-Brightness
- **Location**: Home Page (`/home`)
- **How to Use**:
  1. On the home page, find the **"Set Eye Power via Voice"** section
  2. Click the **"Speak Power Value"** button
  3. Speak your eye power value, for example:
     - "zero point one" for 0.1
     - "point five" for 0.5
     - "one point two" for 1.2
  4. The system will automatically adjust your screen brightness based on the power value
  5. You'll see a confirmation message showing the brightness percentage

- **Power Value Format**:
  - Visual acuity values: 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.5, 2.0
  - These values are automatically converted to diopter values for brightness calculation

- **Brightness Adjustment**:
  - The system calculates brightness based on your eye power
  - Lower power values (worse vision) = Higher brightness
  - Formula: Brightness = 70% + (|diopter| × 8)
  - Brightness ranges from 70% to 100%

### 3. Auto-Brightness Based on Eye Power
- **Automatic Adjustment**:
  - After completing the vision test, brightness is automatically set based on your results
  - When you log in with previous test data, brightness is restored
  - You can manually set brightness using voice input on the home page

- **How It Works**:
  - Power value (v) is converted to diopter: `diopter = -1.5 × (1.0 - v)`
  - Example: v = 0.1 → diopter = -1.35
  - Brightness is calculated from the worse eye (more negative diopter)

## Technical Details

### Backend Endpoints
- `/set_brightness_from_voice/` - POST endpoint to set brightness from voice input
  - Parameters: `power_value` (float)
  - Returns: JSON with success status, brightness percentage, and diopter value

### Frontend Implementation
- Uses Web Speech API (`webkitSpeechRecognition` / `SpeechRecognition`)
- Voice synthesis for instructions (`speechSynthesis`)
- Automatic letter mapping for Cyrillic characters
- Number parsing for power values

### Browser Compatibility
- **Chrome/Edge**: Full support ✅
- **Safari**: Full support ✅
- **Firefox**: Limited support (may need polyfill)

## Troubleshooting

### Voice Recognition Not Working
1. Check browser compatibility (Chrome/Edge recommended)
2. Grant microphone permissions when prompted
3. Ensure you're speaking clearly and in a quiet environment
4. Try clicking the button again if recognition fails

### Brightness Not Adjusting
1. Ensure `screen_brightness_control` package is installed
2. Check if you're on Windows (brightness control works best on Windows)
3. Verify the power value was recognized correctly
4. Check browser console for error messages

### Letter Recognition Issues
- Speak clearly and pronounce the letter name
- Try saying "E" for Е, "M" for М, "W" for Э, "S" for Ш
- If voice recognition fails, use the button clicks instead

## Example Usage Flow

1. **Set Initial Brightness** (Optional):
   - Go to home page
   - Click "Speak Power Value"
   - Say "zero point one"
   - Brightness adjusts automatically

2. **Take Vision Test**:
   - Click "Start Vision Test"
   - Cover right eye, test left eye
   - For each letter, either:
     - Click the button with the letter, OR
     - Click "Speak Letter" and say the letter
   - Continue until test completes

3. **Automatic Brightness**:
   - After test completion, brightness is set automatically
   - Based on your test results

## Notes
- Voice recognition requires an internet connection (uses browser's speech recognition service)
- Microphone permissions are required
- For best results, use in a quiet environment
- You can always fall back to button clicks if voice recognition doesn't work

