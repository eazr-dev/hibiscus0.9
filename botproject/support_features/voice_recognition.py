"""
voice_recognition.py - Voice Recognition Module for Eazr Financial Assistant
Handles voice-to-text conversion using multiple providers
"""

from fastapi import UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import speech_recognition as sr
import tempfile
import os
import base64
import io
from pydub import AudioSegment
from pydub.playback import play
import logging
from typing import Optional, Dict
import json
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VoiceRecognitionService:
    """Service for handling voice recognition across multiple providers"""
    
    def __init__(self):
        self.recognizer = sr.Recognizer()
        # Adjust for ambient noise
        self.recognizer.energy_threshold = 4000
        self.recognizer.dynamic_energy_threshold = True
        
    def process_audio_file(self, audio_file: UploadFile) -> Dict[str, str]:
        """Process uploaded audio file and convert to text"""
        try:
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
                content = audio_file.file.read()
                tmp_file.write(content)
                tmp_file_path = tmp_file.name
            
            # Convert to text
            result = self.convert_audio_to_text(tmp_file_path)
            
            # Clean up
            os.unlink(tmp_file_path)
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing audio file: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    def process_audio_base64(self, audio_data: str, audio_format: str = 'webm') -> Dict[str, str]:
        """Process base64 encoded audio data"""
        try:
            # Decode base64 audio
            audio_bytes = base64.b64decode(audio_data.split(',')[1] if ',' in audio_data else audio_data)
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{audio_format}') as tmp_file:
                tmp_file.write(audio_bytes)
                tmp_file_path = tmp_file.name
            
            # Convert to WAV if needed
            if audio_format != 'wav':
                wav_path = self.convert_to_wav(tmp_file_path, audio_format)
                os.unlink(tmp_file_path)
                tmp_file_path = wav_path
            
            # Convert to text
            result = self.convert_audio_to_text(tmp_file_path)
            
            # Clean up
            os.unlink(tmp_file_path)
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing base64 audio: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    def convert_to_wav(self, input_path: str, input_format: str) -> str:
        """Convert audio file to WAV format"""
        try:
            audio = AudioSegment.from_file(input_path, format=input_format)
            wav_path = input_path.replace(f'.{input_format}', '.wav')
            audio.export(wav_path, format='wav')
            return wav_path
        except Exception as e:
            logger.error(f"Error converting audio to WAV: {str(e)}")
            raise
    
    def convert_audio_to_text(self, audio_path: str) -> Dict[str, str]:
        """Convert audio file to text using multiple recognition engines"""
        result = {
            "text": "",
            "confidence": 0,
            "provider": "",
            "alternatives": [],
            "error": None
        }
        
        try:
            with sr.AudioFile(audio_path) as source:
                # Record audio from file
                audio = self.recognizer.record(source)
                
                # Try Google Speech Recognition first (free, no API key required)
                try:
                    text = self.recognizer.recognize_google(audio, language='en-IN')
                    result["text"] = text
                    result["provider"] = "Google Speech Recognition"
                    result["confidence"] = 0.95  # Google doesn't provide confidence scores
                    
                    # Get alternatives if available
                    try:
                        alternatives = self.recognizer.recognize_google(
                            audio, 
                            language='en-IN', 
                            show_all=True
                        )
                        if isinstance(alternatives, dict) and 'alternative' in alternatives:
                            result["alternatives"] = [
                                alt['transcript'] 
                                for alt in alternatives['alternative'][1:4]  # Top 3 alternatives
                            ]
                    except:
                        pass
                    
                except sr.UnknownValueError:
                    result["error"] = "Speech was unclear. Please try again."
                except sr.RequestError as e:
                    result["error"] = f"Google Speech Recognition error: {str(e)}"
                    
                    # Fallback to offline recognition (PocketSphinx) if available
                    try:
                        import pocketsphinx
                        text = self.recognizer.recognize_sphinx(audio)
                        result["text"] = text
                        result["provider"] = "PocketSphinx (Offline)"
                        result["confidence"] = 0.7
                    except:
                        pass
                
        except Exception as e:
            logger.error(f"Error in speech recognition: {str(e)}")
            result["error"] = f"Recognition error: {str(e)}"
        
        return result
    
    def process_live_audio(self, duration: int = 5) -> Dict[str, str]:
        """Record and process live audio from microphone"""
        try:
            with sr.Microphone() as source:
                logger.info("Adjusting for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                
                logger.info(f"Recording for {duration} seconds...")
                audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=duration)
                
                logger.info("Processing speech...")
                
                # Save audio for debugging
                with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
                    tmp_file.write(audio.get_wav_data())
                    tmp_path = tmp_file.name
                
                result = self.convert_audio_to_text(tmp_path)
                os.unlink(tmp_path)
                
                return result
                
        except sr.WaitTimeoutError:
            return {"error": "No speech detected", "text": ""}
        except Exception as e:
            logger.error(f"Error recording live audio: {str(e)}")
            return {"error": str(e), "text": ""}

# Initialize service
voice_service = VoiceRecognitionService()

# Additional utility functions for the API

def validate_audio_file(file: UploadFile) -> bool:
    """Validate uploaded audio file"""
    allowed_formats = ['wav', 'mp3', 'ogg', 'webm', 'm4a', 'flac']
    file_extension = file.filename.split('.')[-1].lower()
    return file_extension in allowed_formats

def format_voice_response(recognition_result: Dict[str, str]) -> Dict:
    """Format voice recognition result for API response"""
    if recognition_result.get("error"):
        return {
            "success": False,
            "error": recognition_result["error"],
            "text": "",
            "suggestions": [
                "Please speak clearly",
                "Try reducing background noise",
                "Check your microphone"
            ]
        }
    
    return {
        "success": True,
        "text": recognition_result["text"],
        "confidence": recognition_result.get("confidence", 0),
        "provider": recognition_result.get("provider", ""),
        "alternatives": recognition_result.get("alternatives", []),
        "formatted_query": clean_voice_text(recognition_result["text"])
    }

def clean_voice_text(text: str) -> str:
    """Clean and format recognized text for better query processing"""
    # Remove filler words
    filler_words = ['um', 'uh', 'like', 'you know', 'basically', 'actually']
    words = text.lower().split()
    cleaned_words = [word for word in words if word not in filler_words]
    
    # Capitalize first letter
    if cleaned_words:
        cleaned_words[0] = cleaned_words[0].capitalize()
    
    cleaned_text = ' '.join(cleaned_words)
    
    # Add question mark for question words
    question_starters = ['what', 'how', 'when', 'where', 'why', 'who', 'which', 'can', 'could', 'would', 'should']
    first_word = cleaned_text.split()[0].lower() if cleaned_text else ''
    if first_word in question_starters and not cleaned_text.endswith('?'):
        cleaned_text += '?'
    
    return cleaned_text

# Voice command shortcuts mapping
VOICE_SHORTCUTS = {
    "check balance": "What is my account balance?",
    "apply loan": "I want to apply for personal loan",
    "get insurance": "I need insurance plan",
    "create wallet": "Create wallet account",
    "transaction history": "Show my transaction history",
    "help me": "What can you help me with?",
    "outstanding amount": "What is my outstanding amount?",
    "credit limit": "What is my credit limit?",
    "pay bill": "How much is my current bill?",
    "loan status": "What is my loan status?"
}

def process_voice_shortcuts(text: str) -> str:
    """Convert voice shortcuts to full queries"""
    text_lower = text.lower().strip()
    
    # Check for exact matches
    if text_lower in VOICE_SHORTCUTS:
        return VOICE_SHORTCUTS[text_lower]
    
    # Check for partial matches
    for shortcut, full_query in VOICE_SHORTCUTS.items():
        if shortcut in text_lower:
            return full_query
    
    return text

# API endpoint handlers for FastAPI integration

async def handle_voice_upload(file: UploadFile = File(...)):
    """Handle voice file upload endpoint"""
    if not validate_audio_file(file):
        raise HTTPException(status_code=400, detail="Invalid audio file format")
    
    result = voice_service.process_audio_file(file)
    response = format_voice_response(result)
    
    if response["success"]:
        response["processed_query"] = process_voice_shortcuts(response["text"])
    
    return response

async def handle_voice_base64(audio_data: Dict):
    """Handle base64 encoded audio data"""
    if "audio" not in audio_data:
        raise HTTPException(status_code=400, detail="Missing audio data")
    
    audio_format = audio_data.get("format", "webm")
    result = voice_service.process_audio_base64(audio_data["audio"], audio_format)
    response = format_voice_response(result)
    
    if response["success"]:
        response["processed_query"] = process_voice_shortcuts(response["text"])
    
    return response

async def handle_live_recording(duration: int = 5):
    """Handle live microphone recording"""
    if duration < 1 or duration > 30:
        raise HTTPException(status_code=400, detail="Duration must be between 1 and 30 seconds")
    
    result = voice_service.process_live_audio(duration)
    response = format_voice_response(result)
    
    if response["success"]:
        response["processed_query"] = process_voice_shortcuts(response["text"])
    
    return response

# Language support configuration
SUPPORTED_LANGUAGES = {
    "en-IN": "English (India)",
    "en-US": "English (US)",
    "hi-IN": "Hindi",
    "ta-IN": "Tamil",
    "te-IN": "Telugu",
    "kn-IN": "Kannada",
    "ml-IN": "Malayalam",
    "mr-IN": "Marathi",
    "gu-IN": "Gujarati",
    "bn-IN": "Bengali",
    "pa-IN": "Punjabi"
}

def get_language_code(language: str) -> str:
    """Get language code from language name"""
    language_lower = language.lower()
    for code, name in SUPPORTED_LANGUAGES.items():
        if language_lower in name.lower():
            return code
    return "en-IN"  # Default to English (India)