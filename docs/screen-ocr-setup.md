# Screen OCR Setup Guide

This guide explains how to set up the screen OCR functionality for extracting base64 encoded content from your screen.

## Prerequisites

### 1. Python 3.11+

Ensure you have Python 3.11 or later installed. You can download it from [python.org](https://www.python.org/downloads/).

### 2. Tesseract OCR Engine

Tesseract is required for OCR functionality. Follow these steps to install it:

#### Windows Installation
1. Download the Tesseract installer from [UB Mannheim Tesseract](https://github.com/UB-Mannheim/tesseract/wiki)
2. Run the installer and follow the prompts
3. Add the Tesseract installation directory to your system PATH
   - Default installation path: `C:\Program Files\Tesseract-OCR`
   - Add this path to your system environment variables

#### Verification
After installation, open a new command prompt and run:
```bash
tesseract --version
```
You should see the Tesseract version information.

### 3. Project Dependencies

Install the project dependencies using uv (recommended) or pip:

#### Using uv
```bash
uv install
```

#### Using pip
```bash
pip install -e .
```

## Usage

### Running the Screen OCR Command

1. Ensure the base64 content is visible on your screen
2. Open a command prompt
3. Run the screen OCR command:
   ```bash
   openchronicle screen_ocr
   ```
4. Follow the on-screen instructions
5. The program will:
   - Capture the screen
   - Perform OCR to extract text
   - Extract base64 encoded content
   - Scroll the screen to capture more content if needed
   - Save the extracted base64 content to `base64_output.txt`

### Example Output

```
Starting screen OCR and base64 extraction...
Please ensure the base64 content is visible on your screen.
The program will capture the screen, perform OCR, and extract base64 content.
It will also scroll the screen to capture more content if needed.

Press Enter to start...

Successfully extracted base64 content of length 12345

Extracted base64 content:
SGVsbG8gV29ybGQh...

Saving to base64_output.txt...
Saved to base64_output.txt
```

## Troubleshooting

### Common Issues

1. **Tesseract not found**
   - Ensure Tesseract is installed and added to your PATH
   - Restart your command prompt after adding Tesseract to PATH

2. **No base64 content found**
   - Ensure the base64 content is clearly visible on screen
   - Try adjusting the screen resolution or zoom level
   - Ensure there's enough contrast between the text and background

3. **OCR accuracy issues**
   - Ensure the text is clear and not blurry
   - Try increasing the font size if possible
   - Ensure there's good lighting

### Logs

Check the logs for more detailed error information:
```bash
openchronicle status
```

## Notes

- The screen OCR functionality uses `pyautogui` to simulate mouse scrolling, so your mouse cursor may move during the process
- The program will capture multiple screenshots and scroll the screen to ensure it captures all base64 content
- Extracted base64 content is saved to `base64_output.txt` in the current directory
- Large base64 encoded content may take longer to process
