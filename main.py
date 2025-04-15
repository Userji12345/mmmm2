from kivy.app import App
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.slider import Slider
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.properties import StringProperty, NumericProperty, ObjectProperty
from kivy.clock import Clock
import yt_dlp
import os
import threading
import asyncio
import edge_tts
import tempfile
from pygame import mixer
import time

# Initialize pygame mixer for audio playback
mixer.init()

# Define default voices
DEFAULT_VOICES = [
    # Hindi Voices
    "hi-IN-MadhurNeural (Hindi-India)",
    "hi-IN-SwaraNeural (Hindi-India)",
    "hi-IN-MadhurNeural (Hindi-India)",
    
    # English Voices
    "en-US-ChristopherNeural (English-US)",
    "en-US-JennyNeural (English-US)",
    "en-US-EricNeural (English-US)",
    "en-US-AnaNeural (English-US)",
    "en-GB-SoniaNeural (English-UK)",
    "en-GB-RyanNeural (English-UK)",
    "en-IN-NeerjaNeural (English-India)",
    "en-IN-PrabhatNeural (English-India)",
    
    # Indian Languages
    "ta-IN-PallaviNeural (Tamil-India)",
    "ta-IN-ValluvarNeural (Tamil-India)",
    "te-IN-ShrutiNeural (Telugu-India)",
    "te-IN-MohanNeural (Telugu-India)",
    "mr-IN-AarohiNeural (Marathi-India)",
    "mr-IN-ManoharNeural (Marathi-India)",
    "gu-IN-DhwaniNeural (Gujarati-India)",
    "gu-IN-NiranjanNeural (Gujarati-India)",
    "bn-IN-BashkarNeural (Bengali-India)",
    "bn-IN-TanishaaNeural (Bengali-India)",
    "kn-IN-GaganNeural (Kannada-India)",
    "kn-IN-SapnaNeural (Kannada-India)",
    "ml-IN-SobhanaNeural (Malayalam-India)",
    "ml-IN-MidhunNeural (Malayalam-India)",
    "pa-IN-GurpreetNeural (Punjabi-India)",
    "pa-IN-AmritNeural (Punjabi-India)",
    
    # Other Languages
    "zh-CN-XiaoxiaoNeural (Chinese-Mainland)",
    "zh-CN-YunxiNeural (Chinese-Mainland)",
    "ja-JP-NanamiNeural (Japanese)",
    "ja-JP-KeitaNeural (Japanese)",
    "ko-KR-SunHiNeural (Korean)",
    "ko-KR-InJoonNeural (Korean)",
    "es-ES-AlvaroNeural (Spanish)",
    "es-ES-ElviraNeural (Spanish)",
    "fr-FR-DeniseNeural (French)",
    "fr-FR-HenriNeural (French)",
    "de-DE-KatjaNeural (German)",
    "de-DE-ConradNeural (German)",
    "it-IT-ElsaNeural (Italian)",
    "it-IT-DiegoNeural (Italian)",
    "ru-RU-SvetlanaNeural (Russian)",
    "ru-RU-DmitryNeural (Russian)"
]

class VideoDownloaderTab(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 10
        self.spacing = 10
        
        # Platform Selection
        platform_layout = BoxLayout(size_hint_y=None, height=40)
        self.platform = Spinner(
            text='YouTube',
            values=('YouTube', 'Facebook'),
            size_hint=(None, None),
            size=(150, 30)
        )
        platform_layout.add_widget(Label(text='Platform:'))
        platform_layout.add_widget(self.platform)
        self.add_widget(platform_layout)
        
        # URL Entry
        self.url_input = TextInput(
            hint_text='Enter video URL',
            multiline=False,
            size_hint_y=None,
            height=40
        )
        self.add_widget(self.url_input)
        
        # Load Info Button
        self.load_info_btn = Button(
            text='Load Video Information',
            size_hint_y=None,
            height=40
        )
        self.load_info_btn.bind(on_press=self.load_video_info)
        self.add_widget(self.load_info_btn)
        
        # Quality Selection
        quality_layout = BoxLayout(size_hint_y=None, height=40)
        self.quality = Spinner(
            text='Select Quality',
            values=[],
            size_hint=(None, None),
            size=(200, 30)
        )
        quality_layout.add_widget(Label(text='Quality:'))
        quality_layout.add_widget(self.quality)
        self.add_widget(quality_layout)
        
        # Download Location
        location_layout = BoxLayout(size_hint_y=None, height=40)
        self.location = TextInput(
            text=os.path.expanduser("~/Downloads"),
            readonly=True,
            size_hint_y=None,
            height=40
        )
        self.browse_btn = Button(
            text='Browse',
            size_hint=(None, None),
            size=(100, 40)
        )
        self.browse_btn.bind(on_press=self.change_location)
        location_layout.add_widget(self.location)
        location_layout.add_widget(self.browse_btn)
        self.add_widget(location_layout)
        
        # Download Button
        self.download_btn = Button(
            text='Download',
            size_hint_y=None,
            height=40
        )
        self.download_btn.bind(on_press=self.start_download)
        self.add_widget(self.download_btn)
        
        # Progress Bar
        self.progress = Label(text='Progress: 0%')
        self.add_widget(self.progress)
        
        # Status Label
        self.status = Label(text='')
        self.add_widget(self.status)
        
        # Video Title Label
        self.title = Label(text='')
        self.add_widget(self.title)
        
        # Store available formats
        self.available_formats = []

    def load_video_info(self, instance):
        url = self.url_input.text
        if not url:
            self.status.text = 'Please enter a URL'
            return
            
        self.status.text = 'Loading video information...'
        threading.Thread(target=self._load_video_info_thread, args=(url,), daemon=True).start()

    def _load_video_info_thread(self, url):
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                if not info:
                    Clock.schedule_once(lambda dt: setattr(self.status, 'text', 'Could not fetch video information'))
                    return
                
                Clock.schedule_once(lambda dt: setattr(self.title, 'text', f"Title: {info.get('title', 'YouTube Video')}"))
                
                formats = []
                for f in info.get('formats', []):
                    if f.get('ext') in ['mp4', 'webm']:
                        height = f.get('height', '')
                        format_id = f.get('format_id', '')
                        if height:
                            format_info = {
                                'format_id': format_id,
                                'height': height,
                                'ext': f.get('ext', 'mp4'),
                                'display': f"{height}p ({f.get('ext', 'mp4')})"
                            }
                            formats.append(format_info)
                
                self.available_formats = sorted(formats, key=lambda x: x['height'], reverse=True)
                format_displays = [f['display'] for f in self.available_formats]
                
                if not format_displays:
                    format_displays = ["720p (mp4)", "480p (mp4)"]
                    self.available_formats = [
                        {'format_id': 'best', 'height': 720, 'ext': 'mp4', 'display': '720p (mp4)'},
                        {'format_id': 'best', 'height': 480, 'ext': 'mp4', 'display': '480p (mp4)'},
                    ]
                
                Clock.schedule_once(lambda dt: self._update_formats(format_displays))
                Clock.schedule_once(lambda dt: setattr(self.status, 'text', 'Video information loaded successfully!'))
                
        except Exception as e:
            Clock.schedule_once(lambda dt: setattr(self.status, 'text', f'Error loading video information: {str(e)}'))

    def _update_formats(self, format_displays):
        self.quality.values = format_displays
        if format_displays:
            self.quality.text = format_displays[0]

    def change_location(self, instance):
        content = FileChooserListView(path=os.path.expanduser("~/Downloads"))
        popup = Popup(title='Choose Download Location',
                     content=content,
                     size_hint=(0.9, 0.9))
        content.bind(on_submit=lambda instance, selection, touch: self._set_location(selection, popup))
        popup.open()

    def _set_location(self, selection, popup):
        if selection:
            self.location.text = selection[0]
        popup.dismiss()

    def start_download(self, instance):
        if not self.quality.text or self.quality.text == 'Select Quality':
            self.status.text = 'Please select a quality'
            return
            
        threading.Thread(target=self.download_video, daemon=True).start()

    def download_video(self):
        try:
            url = self.url_input.text
            quality_display = self.quality.text
            output_path = self.location.text
            
            # Find selected format
            selected_format = None
            for fmt in self.available_formats:
                if fmt['display'] == quality_display:
                    selected_format = fmt
                    break
            
            if not selected_format:
                raise Exception("Selected quality format not found")
            
            # Configure download options
            ydl_opts = {
                'format': f'bestvideo[height<={selected_format["height"]}]+bestaudio/best[height<={selected_format["height"]}]',
                'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
                'progress_hooks': [self.progress_hook],
            }
            
            self.status.text = "Starting download..."
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            Clock.schedule_once(lambda dt: setattr(self.status, 'text', 'Download completed!'))
            
        except Exception as e:
            error_msg = str(e)
            if "requested format not available" in error_msg.lower():
                error_msg = "The selected quality is not available. Please try a different quality."
            elif "video is private" in error_msg.lower():
                error_msg = "This video is private or requires login."
            Clock.schedule_once(lambda dt: setattr(self.status, 'text', f'Download failed: {error_msg}'))

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            p = d.get('_percent_str', '0%')
            Clock.schedule_once(lambda dt: setattr(self.progress, 'text', f'Progress: {p}'))
        elif d['status'] == 'finished':
            Clock.schedule_once(lambda dt: setattr(self.progress, 'text', 'Progress: 100%'))

class TextToSpeechTab(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 10
        self.spacing = 10
        
        # Voice Selection
        voice_layout = BoxLayout(size_hint_y=None, height=40)
        self.voice = Spinner(
            text='Select Voice',
            values=DEFAULT_VOICES,
            size_hint=(None, None),
            size=(300, 30)
        )
        voice_layout.add_widget(Label(text='Voice:'))
        voice_layout.add_widget(self.voice)
        self.add_widget(voice_layout)
        
        # Speed Control
        speed_layout = BoxLayout(size_hint_y=None, height=40)
        self.speed = Slider(min=0.5, max=2.0, value=1.0)
        self.speed_label = Label(text='1.0x')
        speed_layout.add_widget(Label(text='Speed:'))
        speed_layout.add_widget(self.speed)
        speed_layout.add_widget(self.speed_label)
        self.speed.bind(value=lambda instance, value: setattr(self.speed_label, 'text', f'{value:.1f}x'))
        self.add_widget(speed_layout)
        
        # Pitch Control
        pitch_layout = BoxLayout(size_hint_y=None, height=40)
        self.pitch = Slider(min=-50, max=50, value=0)
        self.pitch_label = Label(text='0')
        pitch_layout.add_widget(Label(text='Pitch:'))
        pitch_layout.add_widget(self.pitch)
        pitch_layout.add_widget(self.pitch_label)
        self.pitch.bind(value=lambda instance, value: setattr(self.pitch_label, 'text', str(int(value))))
        self.add_widget(pitch_layout)
        
        # Text Input
        self.text_input = TextInput(
            hint_text='Enter text to convert to speech',
            multiline=True,
            size_hint_y=0.4
        )
        self.add_widget(self.text_input)
        
        # Control Buttons
        control_layout = BoxLayout(size_hint_y=None, height=40)
        self.speak_btn = Button(text='Speak')
        self.stop_btn = Button(text='Stop')
        self.save_btn = Button(text='Save Audio')
        
        self.speak_btn.bind(on_press=self.start_speaking)
        self.stop_btn.bind(on_press=self.stop_speaking)
        self.save_btn.bind(on_press=self.save_audio)
        
        control_layout.add_widget(self.speak_btn)
        control_layout.add_widget(self.stop_btn)
        control_layout.add_widget(self.save_btn)
        self.add_widget(control_layout)
        
        # Status Label
        self.status = Label(text='')
        self.add_widget(self.status)
        
        # TTS variables
        self.current_audio_file = None
        self.is_playing = False

    def start_speaking(self, instance):
        if self.is_playing:
            return
            
        text = self.text_input.text
        if not text:
            self.status.text = 'Please enter some text'
            return
            
        threading.Thread(target=self.speak_text, daemon=True).start()

    def stop_speaking(self, instance):
        if self.is_playing:
            mixer.music.stop()
            self.is_playing = False
            self.status.text = 'Stopped'

    def speak_text(self):
        text = self.text_input.text
        if not text:
            self.status.text = 'Please enter some text'
            return
            
        try:
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
                self.current_audio_file = temp_file.name
                
            async def generate_speech():
                voice = self.voice.text.split(' ')[0]
                
                # Fix rate and pitch format
                rate = f"+{int((self.speed.value - 1) * 100)}%"
                if self.speed.value < 1:
                    rate = f"{int((self.speed.value - 1) * 100)}%"
                
                pitch = f"+{int(self.pitch.value)}Hz"
                if self.pitch.value < 0:
                    pitch = f"{int(self.pitch.value)}Hz"
                
                communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
                await communicate.save(self.current_audio_file)
                
            asyncio.run(generate_speech())
            
            mixer.music.load(self.current_audio_file)
            mixer.music.play()
            self.is_playing = True
            self.status.text = 'Playing...'
            
            while mixer.music.get_busy():
                time.sleep(0.1)
                
            self.is_playing = False
            self.status.text = 'Done'
            
        except Exception as e:
            self.status.text = f'Error: {str(e)}'
            self.is_playing = False

    def save_audio(self, instance):
        if not self.text_input.text:
            self.status.text = 'Please enter some text'
            return
            
        content = FileChooserListView(path=os.path.expanduser("~/Downloads"))
        popup = Popup(title='Save Audio File',
                     content=content,
                     size_hint=(0.9, 0.9))
        content.bind(on_submit=lambda instance, selection, touch: self._save_audio_file(selection, popup))
        popup.open()

    def _save_audio_file(self, selection, popup):
        if selection:
            save_path = selection[0]
            if not save_path.endswith('.mp3'):
                save_path += '.mp3'
                
            threading.Thread(target=self.generate_and_save_audio, args=(save_path,), daemon=True).start()
        popup.dismiss()

    def generate_and_save_audio(self, save_path):
        text = self.text_input.text
        voice = self.voice.text.split(' ')[0]
        
        try:
            async def save():
                # Fix rate and pitch format
                rate = f"+{int((self.speed.value - 1) * 100)}%"
                if self.speed.value < 1:
                    rate = f"{int((self.speed.value - 1) * 100)}%"
                
                pitch = f"+{int(self.pitch.value)}Hz"
                if self.pitch.value < 0:
                    pitch = f"{int(self.pitch.value)}Hz"
                
                communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
                await communicate.save(save_path)
                
            asyncio.run(save())
            Clock.schedule_once(lambda dt: setattr(self.status, 'text', f'Audio saved to {save_path}'))
            
        except Exception as e:
            Clock.schedule_once(lambda dt: setattr(self.status, 'text', f'Error: {str(e)}'))

class VideoDownloaderApp(App):
    def build(self):
        self.title = 'Video & Audio Tools'
        Window.size = (400, 800)
        
        # Create tabbed panel
        panel = TabbedPanel(do_default_tab=False)
        
        # Add Video Downloader tab
        video_tab = TabbedPanelItem(text='Video Downloader')
        video_tab.add_widget(VideoDownloaderTab())
        panel.add_widget(video_tab)
        
        # Add Text to Speech tab
        tts_tab = TabbedPanelItem(text='Text to Speech')
        tts_tab.add_widget(TextToSpeechTab())
        panel.add_widget(tts_tab)
        
        return panel

if __name__ == '__main__':
    VideoDownloaderApp().run() 