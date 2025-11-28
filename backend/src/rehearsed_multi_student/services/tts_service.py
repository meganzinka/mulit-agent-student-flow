"""Text-to-speech service using Gemini 2.5 Flash TTS."""

import base64
from typing import Optional
from google.cloud import texttospeech

from rehearsed_multi_student.models.domain import VoiceSettings


class TextToSpeechService:
    """Service for converting text to speech using Gemini 2.5 Flash TTS."""
    
    def __init__(self):
        """Initialize Gemini TTS client (uses Application Default Credentials)."""
        self.client = texttospeech.TextToSpeechClient()
        self.model_name = "gemini-2.5-flash-tts"
    
    async def synthesize_speech(
        self, 
        text: str, 
        voice_settings: VoiceSettings
    ) -> Optional[str]:
        """
        Convert text to speech using Gemini 2.5 Flash TTS and return base64-encoded audio.
        
        Args:
            text: The text to convert to speech
            voice_settings: Voice configuration for this student
            
        Returns:
            Base64-encoded MP3 audio data, or None if text is empty
        """
        if not text or not text.strip():
            return None
        
        try:
            import asyncio
            
            # Build synthesis input
            synthesis_input = texttospeech.SynthesisInput(text=text)
            
            # Select the voice
            voice = texttospeech.VoiceSelectionParams(
                language_code=voice_settings.language_code,
                name=voice_settings.voice_name,
                model_name=self.model_name
            )
            
            # Configure audio output
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3
            )
            
            # Perform the text-to-speech request
            response = await asyncio.to_thread(
                self.client.synthesize_speech,
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            
            # The response's audio_content is binary
            audio_bytes = response.audio_content
            
            # Encode to base64
            audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
            
            print(f"✓ Generated audio for: {text[:30]}... (size: {len(audio_bytes)} bytes)")
            return audio_base64
            
        except Exception as e:
            print(f"❌ Error synthesizing speech: {e}")
            import traceback
            traceback.print_exc()
            return None
