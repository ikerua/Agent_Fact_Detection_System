import os
import yt_dlp
import whisper
import torch

class AudioExtractor:
    def __init__(self, model_size="base"):
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Loading Whisper model '{model_size}' on device: {device.upper()}")
        self.model = whisper.load_model(model_size, device=device)
    
    def download_and_extract_audio(self, url: str, output_path: str = "downloads"):
        if not os.path.exists(output_path):
            os.makedirs(output_path)
            
        outtmpl = os.path.join(output_path, '%(title)s.%(ext)s')
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': outtmpl,
            'quiet': True,
            'no_warnings': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
                'preferredquality': '192',
            }],
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            video_title = info_dict.get('title', None)
            
            # Find the actual downloaded file name after postprocessing
            expected_filename = os.path.join(output_path, f"{video_title}.wav")
            downloaded_file = ydl.prepare_filename(info_dict)
            base, _ = os.path.splitext(downloaded_file)
            audio_file = f"{base}.wav"
            
            if os.path.exists(audio_file):
                return audio_file
            
            return expected_filename

    def transcribe(self, audio_path: str):
        fp16_mode = torch.cuda.is_available()
        result = self.model.transcribe(audio_path, fp16=fp16_mode)
        return result["text"]

    def process_url(self, url: str):
        audio_file = self.download_and_extract_audio(url)
        transcript = self.transcribe(audio_file)
        return transcript
