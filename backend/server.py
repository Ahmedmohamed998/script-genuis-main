from fastapi import FastAPI, APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import Response
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone
import base64
import io
import requests
import tempfile
import subprocess
import asyncio
import json
import traceback

import re

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Tool paths
import shutil
YT_DLP_PATH = os.environ.get("YT_DLP_PATH") or (r"C:\Users\ahmed\AppData\Roaming\Python\Python312\Scripts\yt-dlp.exe" if os.name == 'nt' else (shutil.which("yt-dlp") or "yt-dlp"))
FFMPEG_DIR = os.environ.get("FFMPEG_DIR") or (r"C:\Users\ahmed\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1-full_build\bin" if os.name == 'nt' else "")
FFMPEG_PATH = os.environ.get("FFMPEG_PATH") or (os.path.join(FFMPEG_DIR, "ffmpeg.exe") if os.name == 'nt' else (shutil.which("ffmpeg") or "ffmpeg"))
FFPROBE_PATH = os.environ.get("FFPROBE_PATH") or (os.path.join(FFMPEG_DIR, "ffprobe.exe") if os.name == 'nt' else (shutil.which("ffprobe") or "ffprobe"))

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# AWS Bedrock Integration (Replaces emergentintegrations LlmChat)
import boto3

class ClaudeBedrockChat:
    def __init__(self, system_message: str):
        self.system_message = system_message
        self.aws_access_key = os.environ.get("AWS_ACCESS_KEY_ID")
        self.aws_secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
        self.region = os.environ.get("AWS_BEDROCK_REGION", "us-east-1")
        self.model_id = os.environ.get("AWS_BEDROCK_INFERENCE_PROFILE_ID")
        
        self.client = boto3.client(
            "bedrock-runtime",
            aws_access_key_id=self.aws_access_key,
            aws_secret_access_key=self.aws_secret_key,
            region_name=self.region
        )

    async def send_message(self, msg) -> str:
        text = msg.text if hasattr(msg, 'text') else str(msg)
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 4096,
            "system": self.system_message,
            "messages": [{"role": "user", "content": text}]
        }
        response = await asyncio.to_thread(
            self.client.invoke_model,
            modelId=self.model_id,
            body=json.dumps(body)
        )
        response_body = json.loads(response.get("body").read().decode("utf-8"))
        return response_body["content"][0]["text"]

class UserMessage:
    def __init__(self, text: str):
        self.text = text

# Azure STT Integration (Replaces OpenAISpeechToText)
import azure.cognitiveservices.speech as speechsdk
app = FastAPI()
api_router = APIRouter(prefix="/api")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# =============================================================================
# MODELS
# =============================================================================

# Profile Model - for derjotech & mohabtech
class Profile(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str  # derjotech or mohabtech
    display_name: str
    language: str = "en"  # en or ar
    script_type: str = "mixed"  # ads, organic, mixed
    
    # Voice DNA
    tone: str = ""  # casual, professional, energetic, etc.
    favorite_words: List[str] = []
    favorite_phrases: List[str] = []
    cta_style: str = ""
    hook_style: str = ""
    
    # Learning Data
    total_scripts: int = 0
    hook_preferences: Dict[str, int] = {}  # hook_style -> count
    successful_hooks: List[str] = []  # hooks that performed well
    writing_patterns: List[Dict[str, Any]] = []
    
    # Caption DNA
    caption_tone: str = ""
    emoji_usage: str = "moderate"  # none, minimal, moderate, heavy
    hashtag_count: int = 5
    preferred_hashtags: List[str] = []
    
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class ProfileCreate(BaseModel):
    username: str
    display_name: str
    language: str = "en"
    script_type: str = "mixed"
    tone: str = ""
    cta_style: str = ""
    hook_style: str = ""
    caption_tone: str = ""
    emoji_usage: str = "moderate"

# Brand with Voice DNA
class Brand(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    profile_id: str  # belongs to which profile
    name: str
    description: Optional[str] = ""
    
    # Voice DNA
    tone: str = ""  # friendly, professional, playful, urgent
    personality: str = ""  # describe brand personality
    favorite_words: List[str] = []
    forbidden_words: List[str] = []
    cta_templates: List[str] = []  # common CTAs for this brand
    hook_templates: List[str] = []  # common hooks for this brand
    
    # Caption DNA
    caption_style: str = ""
    emoji_style: str = "moderate"
    hashtags: List[str] = []
    caption_length: str = "medium"  # short, medium, long
    
    # Requirements
    requirements: Optional[Dict[str, Any]] = {}
    needs_thumbnail: bool = False
    needs_ad_code: bool = False
    needs_partnership_tag: bool = False
    
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class BrandCreate(BaseModel):
    profile_id: str
    name: str
    description: Optional[str] = ""
    tone: str = ""
    personality: str = ""
    favorite_words: List[str] = []
    forbidden_words: List[str] = []
    cta_templates: List[str] = []
    hook_templates: List[str] = []
    caption_style: str = ""
    emoji_style: str = "moderate"
    hashtags: List[str] = []
    caption_length: str = "medium"
    needs_thumbnail: bool = False
    needs_ad_code: bool = False
    needs_partnership_tag: bool = False

# Project with Multi-Video & A/B Testing
class Project(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    profile_id: str
    name: str
    brand_id: Optional[str] = None
    is_ad: bool = False
    status: str = "draft"
    
    # Multi-Video Support
    video_urls: List[str] = []
    transcripts: List[Dict[str, Any]] = []
    mixed_transcript: Optional[str] = ""  # Combined from multiple videos
    
    key_features: List[str] = []
    
    # Script Settings
    target_word_count: int = 150  # Target words for script
    target_duration_seconds: int = 60  # Target video duration
    writing_style: str = "natural"  # natural, formal, casual, energetic
    
    # Hooks with A/B Testing
    hooks: List[Dict[str, Any]] = []  # Each has: text, style, selected, performance
    selected_hook_indices: List[int] = []  # Multiple selections for A/B
    hook_performance: Dict[str, Dict[str, Any]] = {}  # hook_id -> {views, engagement, etc}
    
    body_content: Optional[str] = ""
    body_variations: List[Dict[str, Any]] = []  # Multiple body versions
    
    cta_content: Optional[str] = ""
    cta_variations: List[Dict[str, Any]] = []  # Multiple CTA versions
    
    final_script: Optional[str] = ""
    script_versions: List[Dict[str, Any]] = []  # Version history
    
    # Script Stats
    actual_word_count: int = 0
    estimated_duration_seconds: int = 0
    
    # Caption Intelligence
    caption: Optional[str] = ""
    caption_variations: List[str] = []
    hashtags: List[str] = []
    hashtags_categorized: Dict[str, List[str]] = {}  # {trending: [], niche: [], branded: []}
    caption_tips: Optional[str] = ""
    analyzed_captions: List[Dict[str, Any]] = []  # Captions from reference videos
    approval_status: str = "pending"
    approval_notes: Optional[str] = ""
    thumbnail_url: Optional[str] = None
    ad_code: Optional[str] = ""
    partnership_tag: Optional[str] = ""
    
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class ProjectCreate(BaseModel):
    profile_id: str
    name: str
    brand_id: Optional[str] = None
    is_ad: bool = False
    video_urls: List[str] = []
    key_features: List[str] = []
    target_word_count: int = 150
    target_duration_seconds: int = 60
    writing_style: str = "natural"

class TranscribeRequest(BaseModel):
    video_url: str
    target_language: str = "ar"

class VideoInfoRequest(BaseModel):
    video_url: str

class GenerateCaptionRequest(BaseModel):
    platform: str = "tiktok"  # tiktok, instagram, youtube
    tone: str = "auto"  # auto, casual, professional, funny, educational
    hashtag_count: int = 10

class MixScriptsRequest(BaseModel):
    project_id: str
    focus_areas: List[str] = []  # Which parts to prioritize from which video

class GenerateHooksRequest(BaseModel):
    project_id: str
    count: int = 5
    styles: List[str] = []  # question, statement, story, statistic, provocative

class HookPerformanceUpdate(BaseModel):
    hook_index: int
    views: int = 0
    engagement: float = 0
    clicks: int = 0
    notes: str = ""

class ChatRequest(BaseModel):
    project_id: str
    message: str
    section: Optional[str] = None

class ChatMessage(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str
    profile_id: str
    role: str
    content: str
    section: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

# =============================================================================
# TRACKED ACCOUNTS - For Auto-Analysis
# =============================================================================

class TrackedAccount(BaseModel):
    """Account to track and analyze for style learning"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    profile_id: str  # Which profile owns this tracking
    
    # Account Info
    platform: str  # tiktok, instagram, youtube
    account_url: str  # Full URL to the account
    account_name: str  # Display name
    account_handle: str  # @handle
    
    # Tracking Settings
    is_active: bool = True
    check_frequency: str = "weekly"  # daily, weekly, biweekly
    min_engagement_threshold: int = 1000  # Minimum views/likes to analyze
    
    # Analysis Results
    total_videos_analyzed: int = 0
    last_analysis_at: Optional[str] = None
    next_analysis_at: Optional[str] = None
    
    # Learned Patterns
    common_hook_styles: List[str] = []
    common_cta_styles: List[str] = []
    avg_script_length: int = 0
    top_performing_hooks: List[Dict[str, Any]] = []  # {text, engagement, video_url}
    writing_style_notes: str = ""
    content_themes: List[str] = []
    posting_frequency: str = ""
    best_performing_content_type: str = ""
    
    # Engagement Stats
    avg_views: int = 0
    avg_likes: int = 0
    avg_comments: int = 0
    engagement_rate: float = 0.0
    
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class TrackedAccountCreate(BaseModel):
    profile_id: str
    platform: str
    account_url: str
    account_name: str
    account_handle: str
    check_frequency: str = "weekly"
    min_engagement_threshold: int = 1000

class AnalyzedVideo(BaseModel):
    """Individual video analysis from tracked account"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tracked_account_id: str
    profile_id: str
    
    # Video Info
    video_url: str
    video_title: Optional[str] = ""
    posted_at: Optional[str] = None
    duration: int = 0  # seconds
    
    # Engagement
    views: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    engagement_rate: float = 0.0
    
    # Analysis
    transcript: str = ""
    detected_language: str = ""
    
    # Script Structure Analysis
    hook_text: str = ""
    hook_style: str = ""
    body_structure: str = ""
    cta_text: str = ""
    cta_style: str = ""
    
    # Style Analysis
    tone: str = ""
    pacing: str = ""  # fast, medium, slow
    key_phrases: List[str] = []
    emotional_triggers: List[str] = []
    
    analyzed_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class StyleInsight(BaseModel):
    """Aggregated style insights from all tracked accounts"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    profile_id: str
    
    # Generated insights
    insight_type: str  # hook_pattern, cta_pattern, engagement_tip, trend_alert
    title: str
    description: str
    examples: List[str] = []
    source_accounts: List[str] = []  # account handles
    confidence_score: float = 0.0
    
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def detect_platform(url: str) -> str:
    """Detect video platform from URL"""
    url_lower = url.lower()
    if "tiktok.com" in url_lower:
        return "tiktok"
    elif "instagram.com" in url_lower or "instagr.am" in url_lower:
        return "instagram"
    elif "youtube.com" in url_lower or "youtu.be" in url_lower:
        return "youtube"
    elif "facebook.com" in url_lower or "fb.watch" in url_lower:
        return "facebook"
    elif "twitter.com" in url_lower or "x.com" in url_lower:
        return "twitter"
    return "unknown"

def get_instagram_cookies_file(tmp_dir: str) -> Optional[str]:
    """Generate a Netscape-format cookie file for Instagram"""
    session_id = os.environ.get("SESSION_COOKIES_SESSION_ID")
    if not session_id:
        return None
        
    csrftoken = os.environ.get("SESSION_COOKIES_CSRF_TOKEN", "")
    ds_user_id = os.environ.get("SESSION_COOKIES_DS_USER_ID", "")
    mid = os.environ.get("SESSION_COOKIES_M_ID", "")
    ig_did = os.environ.get("SESSION_COOKIES_IG_DID", "")
    
    cookie_file = os.path.join(tmp_dir, "ig_cookies.txt")
    with open(cookie_file, "w") as f:
        f.write("# Netscape HTTP Cookie File\n")
        f.write("# http://curl.haxx.se/rfc/cookie_spec.html\n")
        f.write("# This is a generated file!  Do not edit.\n\n")
        
        # Format: domain  domain_specified  path  secure  expires  name  value
        if csrftoken: f.write(f".instagram.com\tTRUE\t/\tTRUE\t2147483647\tcsrftoken\t{csrftoken}\n")
        f.write(f".instagram.com\tTRUE\t/\tTRUE\t2147483647\tsessionid\t{session_id}\n")
        if ds_user_id: f.write(f".instagram.com\tTRUE\t/\tTRUE\t2147483647\tds_user_id\t{ds_user_id}\n")
        if mid: f.write(f".instagram.com\tTRUE\t/\tTRUE\t2147483647\tmid\t{mid}\n")
        if ig_did: f.write(f".instagram.com\tTRUE\t/\tTRUE\t2147483647\tig_did\t{ig_did}\n")
        
    return cookie_file

async def get_video_metadata(video_url: str) -> Dict:
    """Get video metadata without downloading"""
    platform = detect_platform(video_url)
    try:
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Setup yt-dlp arguments
            args = []
            if platform == "instagram":
                cookie_file = get_instagram_cookies_file(tmp_dir)
                if cookie_file:
                    args.extend(["--cookies", cookie_file])
            
            cmd = [
                YT_DLP_PATH,
                "--dump-json",
                "--no-download",
                "--extractor-args", "youtube:player_client=ios,android",
                "--socket-timeout", "15",
                "--js-runtimes", "node",
            ] + args + [video_url]
            
            def run_yt_dlp():
                return subprocess.run(cmd, capture_output=True, text=False)
                
            logger.info(f"Fetching metadata with yt-dlp: {' '.join(cmd)}")
            result = await asyncio.to_thread(run_yt_dlp)
            stdout, stderr = result.stdout, result.stderr
            
            if result.returncode != 0:
                error_msg = stderr.decode(errors='replace')
                if "blocked" in error_msg.lower() or "403" in error_msg:
                    return {
                        "platform": platform,
                        "error": "platform_blocked",
                        "message": f"{platform.title()} is blocking access from this server. Try YouTube links or paste the transcript manually."
                    }
                return {
                    "platform": platform,
                    "error": "fetch_failed",
                    "message": f"Could not fetch video info: {error_msg[:200]}"
                }
        
            data = json.loads(stdout.decode())
        return {
            "platform": platform,
            "title": data.get("title", ""),
            "duration": data.get("duration", 0),
            "view_count": data.get("view_count", 0),
            "like_count": data.get("like_count", 0),
            "comment_count": data.get("comment_count", 0),
            "uploader": data.get("uploader", ""),
            "upload_date": data.get("upload_date", ""),
            "description": (data.get("description", "") or "")[:300],
            "thumbnail": data.get("thumbnail", ""),
            "available": True
        }
    except Exception as e:
        logger.error(f"Video metadata error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "platform": platform,
            "error": "exception",
            "message": str(e)
        }

async def download_video_audio(video_url: str) -> bytes:
    """Download audio from video URL using yt-dlp with ffmpeg"""
    platform = detect_platform(video_url)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_template = os.path.join(tmpdir, "audio.%(ext)s")
        # Setup yt-dlp arguments
        args = []
        if platform == "instagram":
            cookie_file = get_instagram_cookies_file(tmpdir)
            if cookie_file:
                args.extend(["--cookies", cookie_file])

        cmd = [
            YT_DLP_PATH,
            "-x",
            "--audio-format", "mp3",
            "--audio-quality", "5",
            "--extractor-args", "youtube:player_client=ios,android",
            "--socket-timeout", "30",
            "--no-playlist",
            "--js-runtimes", "node",
            "--ffmpeg-location", FFMPEG_DIR if os.name == 'nt' else FFMPEG_PATH,
            "-o", output_template,
        ] + args 
        
        # Add platform-specific options
        if platform == "tiktok":
            cmd.extend(["--extractor-args", "tiktok:api_hostname=api22-normal-c-alisg.tiktokv.com"])
        
        cmd.append(video_url)

        def run_yt_dlp():
            return subprocess.run(cmd, capture_output=True, text=False)

        logger.info(f"Downloading with yt-dlp: {' '.join(cmd)}")
        result = await asyncio.to_thread(run_yt_dlp)
        stdout, stderr = result.stdout, result.stderr
        
        if result.returncode != 0:
            error_msg = stderr.decode(errors='replace')
            logger.error(f"yt-dlp error for {platform}: {error_msg}")
            
            if "blocked" in error_msg.lower() or "403" in error_msg:
                raise HTTPException(
                    status_code=400, 
                    detail=f"{platform.title()} is blocking access. Try a YouTube link or paste the transcript manually."
                )
            raise HTTPException(status_code=400, detail=f"Failed to download: {error_msg[:300]}")
        
        # Find the downloaded audio file
        for f in os.listdir(tmpdir):
            filepath = os.path.join(tmpdir, f)
            if os.path.isfile(filepath) and f.endswith(('.mp3', '.m4a', '.wav', '.opus', '.webm', '.ogg')):
                # Convert to mp3 if not already
                if not f.endswith('.mp3'):
                    mp3_path = os.path.join(tmpdir, "converted.mp3")
                    convert_cmd = [
                        FFMPEG_PATH, "-i", filepath, "-vn", "-acodec", "libmp3lame",
                        "-q:a", "5", "-y", mp3_path
                    ]
                    
                    def run_ffmpeg():
                        return subprocess.run(convert_cmd, capture_output=True)
                        
                    await asyncio.to_thread(run_ffmpeg)
                    
                    if os.path.exists(mp3_path):
                        filepath = mp3_path
                
                with open(filepath, 'rb') as audio_file:
                    return audio_file.read()
        
        raise HTTPException(status_code=400, detail="No audio file found after download")

async def transcribe_audio(audio_data: bytes) -> str:
    speech_key = os.environ.get("AZURE_SPEECH_KEY")
    service_region = os.environ.get("AZURE_SPEECH_REGION")
    
    if not speech_key or not service_region:
        raise HTTPException(status_code=500, detail="Azure Speech services not configured")

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        # Azure SDK typically prefers WAV for stream inputs or we can use the file directly
        tmp.write(audio_data)
        tmp_path = tmp.name
    
    try:
        # Convert whatever it is to wav if needed, but assuming yt-dlp/ffmpeg can output wav 
        # or we rely on Azure understanding the format. To be safe, Azure accepts WAV.
        # Actually Azure SDK can handle wav. Let's convert to wav using ffmpeg to be 100% sure it's compatible (16kHz 16bit)
        wav_path = tmp_path + ".converted.wav"
        convert_cmd = [
            FFMPEG_PATH, "-i", tmp_path, "-ac", "1", "-ar", "16000", "-sample_fmt", "s16", "-y", wav_path
        ]
        def run_ffmpeg():
            res = subprocess.run(convert_cmd, capture_output=True)
            if res.returncode != 0:
                logger.error(f"FFmpeg conversion failed: {res.stderr.decode(errors='replace')}")
            return res
            
        await asyncio.to_thread(run_ffmpeg)

        def sync_transcribe():
            import time
            speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
            
            # Configure Auto-Detect for English and Arabic dialects
            auto_detect_source_language_config = speechsdk.languageconfig.AutoDetectSourceLanguageConfig(
                languages=["ar-EG", "ar-SA", "en-US"]
            )
            
            audio_config = speechsdk.AudioConfig(filename=wav_path)
            speech_recognizer = speechsdk.SpeechRecognizer(
                speech_config=speech_config, 
                auto_detect_source_language_config=auto_detect_source_language_config,
                audio_config=audio_config
            )
            
            done = False
            transcript_parts = []
            
            def recognized_cb(evt):
                if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
                    transcript_parts.append(evt.result.text)
                    
            def stopped_cb(evt):
                nonlocal done
                if evt.result.reason == speechsdk.ResultReason.Canceled:
                    cancellation_details = evt.result.cancellation_details
                    logger.error(f"Speech Recognition canceled: {cancellation_details.reason}")
                    if cancellation_details.reason == speechsdk.CancellationReason.Error:
                        logger.error(f"Error details: {cancellation_details.error_details}")
                done = True
                
            speech_recognizer.recognized.connect(recognized_cb)
            speech_recognizer.session_stopped.connect(stopped_cb)
            speech_recognizer.canceled.connect(stopped_cb)
            
            speech_recognizer.start_continuous_recognition()
            while not done:
                time.sleep(0.1)
            speech_recognizer.stop_continuous_recognition()
            
            return " ".join(transcript_parts)

        return await asyncio.to_thread(sync_transcribe)
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        if 'wav_path' in locals() and os.path.exists(wav_path):
            os.unlink(wav_path)


async def get_claude_chat(session_id: str, system_message: str):
    return ClaudeBedrockChat(system_message=system_message)

def calculate_script_stats(text: str, language: str = "en") -> Dict:
    """Calculate word count and estimated duration"""
    if not text:
        return {"word_count": 0, "duration_seconds": 0, "duration_display": "0:00"}
    
    # Count words
    words = text.split()
    word_count = len(words)
    
    # Estimate duration based on speaking rate
    # English: ~150 words per minute, Arabic: ~130 words per minute
    words_per_minute = 130 if language == "ar" else 150
    duration_seconds = int((word_count / words_per_minute) * 60)
    
    # Format duration
    minutes = duration_seconds // 60
    seconds = duration_seconds % 60
    duration_display = f"{minutes}:{seconds:02d}"
    
    return {
        "word_count": word_count,
        "duration_seconds": duration_seconds,
        "duration_display": duration_display
    }

async def get_profile(profile_id: str) -> Optional[Dict]:
    return await db.profiles.find_one({"id": profile_id}, {"_id": 0})

async def get_brand(brand_id: str) -> Optional[Dict]:
    return await db.brands.find_one({"id": brand_id}, {"_id": 0})

async def learn_from_script(profile_id: str, project: Dict, final_script: str):
    """Learn from completed script to improve future suggestions"""
    profile = await get_profile(profile_id)
    if not profile:
        return
    
    # Update hook preferences
    hook_prefs = profile.get("hook_preferences", {})
    if project.get("hooks") and project.get("selected_hook_indices"):
        for idx in project["selected_hook_indices"]:
            if idx < len(project["hooks"]):
                style = project["hooks"][idx].get("style", "default")
                hook_prefs[style] = hook_prefs.get(style, 0) + 1
    
    # Extract patterns
    pattern = {
        "brand_id": project.get("brand_id"),
        "is_ad": project.get("is_ad"),
        "script_length": len(final_script),
        "num_videos": len(project.get("video_urls", [])),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    writing_patterns = profile.get("writing_patterns", [])
    writing_patterns.append(pattern)
    if len(writing_patterns) > 100:
        writing_patterns = writing_patterns[-100:]
    
    # Update profile
    await db.profiles.update_one(
        {"id": profile_id},
        {"$set": {
            "hook_preferences": hook_prefs,
            "writing_patterns": writing_patterns,
            "total_scripts": profile.get("total_scripts", 0) + 1,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )

def build_profile_context(profile: Dict) -> str:
    """Build context string from profile's voice DNA"""
    context = f"""
Profile: {profile.get('display_name')}
Language: {profile.get('language', 'en')}
Script Type: {profile.get('script_type', 'mixed')}
Tone: {profile.get('tone', 'professional')}
Hook Style: {profile.get('hook_style', '')}
CTA Style: {profile.get('cta_style', '')}
Total Scripts Written: {profile.get('total_scripts', 0)}
"""
    
    # Add learned hook preferences
    hook_prefs = profile.get("hook_preferences", {})
    if hook_prefs:
        sorted_prefs = sorted(hook_prefs.items(), key=lambda x: x[1], reverse=True)
        context += f"\nPreferred Hook Styles: {', '.join([f'{k}({v})' for k, v in sorted_prefs[:5]])}"
    
    return context

# =============================================================================
# ACCOUNT SCRAPING & ANALYSIS HELPERS
# =============================================================================

async def get_account_videos(account_url: str, platform: str, limit: int = 10) -> List[Dict]:
    import re
    import instaloader
    from googleapiclient.discovery import build
    
    videos = []
    try:
        if platform == "instagram":
            match = re.search(r'instagram\.com/([^/?]+)', account_url)
            if not match:
                return []
            username = match.group(1)
            
            L = instaloader.Instaloader()
            
            ig_user = os.environ.get("INSTAGRAM_USERNAME")
            session_id = os.environ.get("SESSION_COOKIES_SESSION_ID")
            csrftoken = os.environ.get("SESSION_COOKIES_CSRF_TOKEN")
            ds_user_id = os.environ.get("SESSION_COOKIES_DS_USER_ID")
            mid = os.environ.get("SESSION_COOKIES_M_ID")
            ig_did = os.environ.get("SESSION_COOKIES_IG_DID")
            
            if session_id and ig_user:
                try:
                    L.context._session.cookies.set("sessionid", session_id, domain=".instagram.com")
                    if csrftoken:
                        L.context._session.cookies.set("csrftoken", csrftoken, domain=".instagram.com")
                    if ds_user_id:
                        L.context._session.cookies.set("ds_user_id", ds_user_id, domain=".instagram.com")
                    if mid:
                        L.context._session.cookies.set("mid", mid, domain=".instagram.com")
                    if ig_did:
                        L.context._session.cookies.set("ig_did", ig_did, domain=".instagram.com")
                    
                    if csrftoken:
                        L.context._session.headers.update({'X-CSRFToken': csrftoken})
                    
                    L.context.username = ig_user
                    L.context.is_logged_in = True
                    logger.info(f"Instaloader session initialized for {ig_user}")
                except Exception as e:
                    logger.error(f"Instaloader cookie injection failed: {e}")
            
            profile = await asyncio.to_thread(instaloader.Profile.from_username, L.context, username)
            
            count = 0
            for post in profile.get_posts():
                if count >= limit:
                    break
                if post.is_video:
                    videos.append({
                        "url": f"https://www.instagram.com/p/{post.shortcode}/",
                        "title": (post.caption or "")[:100],
                        "view_count": post.video_view_count or 0,
                        "like_count": post.likes,
                        "comment_count": post.comments,
                        "duration": 0,
                        "upload_date": post.date_utc.isoformat(),
                        "platform": "instagram"
                    })
                    count += 1
            return videos
            
        elif platform == "youtube":
            api_key = os.environ.get("YOUTUBE_API_KEY")
            if not api_key:
                logger.error("YOUTUBE_API_KEY not set")
                return []
            
            youtube = await asyncio.to_thread(build, 'youtube', 'v3', developerKey=api_key)
            
            channel_id = None
            if "youtube.com/channel/" in account_url:
                channel_id = account_url.split("youtube.com/channel/")[1].split("/")[0]
            elif "youtube.com/@" in account_url:
                handle = account_url.split("youtube.com/@")[1].split("/")[0]
                request = youtube.search().list(part="snippet", type="channel", q=handle, maxResults=1)
                response = await asyncio.to_thread(request.execute)
                if response.get("items"):
                    channel_id = response["items"][0]["id"]["channelId"]
            
            if not channel_id:
                return []
                
            request = youtube.channels().list(part="contentDetails", id=channel_id)
            response = await asyncio.to_thread(request.execute)
            if not response.get("items"):
                return []
            
            uploads_playlist_id = response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
            
            request = youtube.playlistItems().list(part="snippet", playlistId=uploads_playlist_id, maxResults=limit)
            playlist_response = await asyncio.to_thread(request.execute)
            
            video_ids = [item["snippet"]["resourceId"]["videoId"] for item in playlist_response.get("items", [])]
            if not video_ids:
                return []
                
            request = youtube.videos().list(part="snippet,statistics,contentDetails", id=",".join(video_ids))
            videos_response = await asyncio.to_thread(request.execute)
            
            for item in videos_response.get("items", []):
                stats = item.get("statistics", {})
                duration_raw = item.get("contentDetails", {}).get("duration", "PT0S")
                # Very rough ISO duration approximation
                dur = re.findall(r'(\d+)[HMS]', duration_raw)
                duration_seconds = sum(int(x) * multiplier for x, multiplier in zip(reversed(dur), (1, 60, 3600))) if dur else 0
                
                videos.append({
                    "url": f"https://www.youtube.com/watch?v={item['id']}",
                    "title": item["snippet"]["title"],
                    "view_count": int(stats.get("viewCount", 0)),
                    "like_count": int(stats.get("likeCount", 0)),
                    "comment_count": int(stats.get("commentCount", 0)),
                    "duration": duration_seconds,
                    "upload_date": item["snippet"]["publishedAt"],
                    "platform": "youtube"
                })
            return videos
            
        elif platform == "tiktok":
            logger.info("TikTok scraping is disabled")
            return []
            
        else:
            logger.error(f"Unsupported platform: {platform}")
            return []
            
    except Exception as e:
        logger.error(f"Error getting account videos: {e}")
        return []

async def get_video_info(video_url: str) -> Dict:
    """Get detailed video info using yt-dlp"""
    try:
        cmd = [
            YT_DLP_PATH,
            "--dump-json",
            "--no-download",
            video_url
        ]
        
        def run_ffmpeg():
            return subprocess.run(cmd, capture_output=True)
            
        result = await asyncio.to_thread(run_ffmpeg)
        
        if result.returncode != 0:
            return {}
        
        return json.loads(result.stdout.decode())
    except Exception as e:
        logger.error(f"Error getting video info: {e}")
        return {}

async def analyze_script_structure(transcript: str, profile_language: str = "en") -> Dict:
    """Analyze transcript to extract hook, body, CTA structure"""
    lang_name = "Arabic (Egyptian dialect)" if profile_language == "ar" else "English"
    
    system_msg = f"""You are an expert script analyst. Analyze the given transcript and extract its structure.
Return ONLY valid JSON with no markdown or explanation."""

    chat = await get_claude_chat(
        session_id=f"analyze-{uuid.uuid4()}",
        system_message=system_msg
    )
    
    prompt = f"""Analyze this video script transcript and extract its structure.

TRANSCRIPT:
{transcript}

Return JSON in this exact format:
{{
    "hook_text": "the opening hook (first 1-2 sentences)",
    "hook_style": "question/statement/story/statistic/provocative/shock",
    "body_structure": "brief description of how the body is structured",
    "cta_text": "the call to action (last sentences)",
    "cta_style": "direct/soft/urgent/social-proof",
    "tone": "casual/professional/energetic/educational/entertaining",
    "pacing": "fast/medium/slow",
    "key_phrases": ["list", "of", "key", "phrases", "used"],
    "emotional_triggers": ["curiosity", "fomo", "etc"]
}}"""

    msg = UserMessage(text=prompt)
    response = await chat.send_message(msg)
    
    try:
        response_text = response.strip()
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        return json.loads(response_text)
    except:
        return {
            "hook_text": transcript[:200] if len(transcript) > 200 else transcript,
            "hook_style": "unknown",
            "body_structure": "Could not analyze",
            "cta_text": "",
            "cta_style": "unknown",
            "tone": "unknown",
            "pacing": "medium",
            "key_phrases": [],
            "emotional_triggers": []
        }

async def generate_style_insights(profile_id: str, analyzed_videos: List[Dict]) -> List[Dict]:
    """Generate insights from analyzed videos"""
    if not analyzed_videos:
        return []
    
    # Aggregate data
    hook_styles = {}
    cta_styles = {}
    tones = {}
    all_phrases = []
    all_triggers = []
    
    for video in analyzed_videos:
        # Count hook styles
        hs = video.get("hook_style", "unknown")
        hook_styles[hs] = hook_styles.get(hs, 0) + 1
        
        # Count CTA styles
        cs = video.get("cta_style", "unknown")
        cta_styles[cs] = cta_styles.get(cs, 0) + 1
        
        # Count tones
        t = video.get("tone", "unknown")
        tones[t] = tones.get(t, 0) + 1
        
        # Collect phrases and triggers
        all_phrases.extend(video.get("key_phrases", []))
        all_triggers.extend(video.get("emotional_triggers", []))
    
    insights = []
    
    # Top hook style insight
    if hook_styles:
        top_hook = max(hook_styles.items(), key=lambda x: x[1])
        insights.append({
            "id": str(uuid.uuid4()),
            "profile_id": profile_id,
            "insight_type": "hook_pattern",
            "title": f"Most Effective Hook Style: {top_hook[0].title()}",
            "description": f"Based on {len(analyzed_videos)} analyzed videos, {top_hook[0]} hooks appear {top_hook[1]} times and drive high engagement.",
            "examples": [v.get("hook_text", "") for v in analyzed_videos if v.get("hook_style") == top_hook[0]][:3],
            "source_accounts": [],
            "confidence_score": min(top_hook[1] / len(analyzed_videos), 1.0),
            "created_at": datetime.now(timezone.utc).isoformat()
        })
    
    # Top CTA insight
    if cta_styles:
        top_cta = max(cta_styles.items(), key=lambda x: x[1])
        insights.append({
            "id": str(uuid.uuid4()),
            "profile_id": profile_id,
            "insight_type": "cta_pattern",
            "title": f"Most Used CTA Style: {top_cta[0].title()}",
            "description": f"{top_cta[0].title()} CTAs are commonly used in high-performing content.",
            "examples": [v.get("cta_text", "") for v in analyzed_videos if v.get("cta_style") == top_cta[0]][:3],
            "source_accounts": [],
            "confidence_score": min(top_cta[1] / len(analyzed_videos), 1.0),
            "created_at": datetime.now(timezone.utc).isoformat()
        })
    
    # Common phrases insight
    if all_phrases:
        from collections import Counter
        phrase_counts = Counter(all_phrases)
        top_phrases = phrase_counts.most_common(5)
        if top_phrases:
            insights.append({
                "id": str(uuid.uuid4()),
                "profile_id": profile_id,
                "insight_type": "engagement_tip",
                "title": "Power Phrases That Drive Engagement",
                "description": "These phrases appear frequently in high-performing videos.",
                "examples": [p[0] for p in top_phrases],
                "source_accounts": [],
                "confidence_score": 0.7,
                "created_at": datetime.now(timezone.utc).isoformat()
            })
    
    return insights

def build_brand_context(brand: Dict) -> str:
    """Build context string from brand's voice DNA"""
    context = f"""
Brand: {brand.get('name')}
Tone: {brand.get('tone', '')}
Personality: {brand.get('personality', '')}
"""
    
    if brand.get("favorite_words"):
        context += f"\nFavorite Words: {', '.join(brand['favorite_words'][:10])}"
    
    if brand.get("forbidden_words"):
        context += f"\nAvoid These Words: {', '.join(brand['forbidden_words'][:10])}"
    
    if brand.get("cta_templates"):
        context += f"\nCTA Templates: {' | '.join(brand['cta_templates'][:3])}"
    
    if brand.get("hook_templates"):
        context += f"\nHook Templates: {' | '.join(brand['hook_templates'][:3])}"
    
    return context

# =============================================================================
# API ROUTES - PROFILES
# =============================================================================

@api_router.get("/")
async def root():
    return {"message": "Script Genius API v2"}

@api_router.post("/profiles", response_model=Profile)
async def create_profile(input: ProfileCreate):
    # Check if username exists
    existing = await db.profiles.find_one({"username": input.username}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    profile = Profile(**input.model_dump())
    await db.profiles.insert_one(profile.model_dump())
    return profile

@api_router.get("/profiles", response_model=List[Profile])
async def get_profiles():
    profiles = await db.profiles.find({}, {"_id": 0}).to_list(100)
    return profiles

@api_router.get("/profiles/{profile_id}", response_model=Profile)
async def get_profile_by_id(profile_id: str):
    profile = await db.profiles.find_one({"id": profile_id}, {"_id": 0})
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile

@api_router.get("/profiles/username/{username}", response_model=Profile)
async def get_profile_by_username(username: str):
    profile = await db.profiles.find_one({"username": username}, {"_id": 0})
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile

@api_router.put("/profiles/{profile_id}", response_model=Profile)
async def update_profile(profile_id: str, updates: Dict[str, Any]):
    profile = await db.profiles.find_one({"id": profile_id}, {"_id": 0})
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.profiles.update_one({"id": profile_id}, {"$set": updates})
    return await db.profiles.find_one({"id": profile_id}, {"_id": 0})

@api_router.post("/profiles/seed")
async def seed_profiles():
    """Seed the two default profiles: derjotech and mohabtech"""
    profiles_data = [
        {
            "username": "derjotech",
            "display_name": "Derjo Tech",
            "language": "en",
            "script_type": "ads",
            "tone": "professional",
            "hook_style": "benefit-focused, curiosity-driven",
            "cta_style": "direct, urgent",
            "caption_tone": "professional",
            "emoji_usage": "minimal"
        },
        {
            "username": "mohabtech",
            "display_name": "Mohab Tech",
            "language": "ar",
            "script_type": "mixed",
            "tone": "casual Egyptian",
            "hook_style": "relatable, storytelling",
            "cta_style": "friendly, conversational",
            "caption_tone": "casual Egyptian",
            "emoji_usage": "moderate"
        }
    ]
    
    created = []
    for data in profiles_data:
        existing = await db.profiles.find_one({"username": data["username"]}, {"_id": 0})
        if not existing:
            profile = Profile(**data)
            await db.profiles.insert_one(profile.model_dump())
            created.append(profile.username)
    
    return {"message": f"Created profiles: {created}" if created else "Profiles already exist"}

# =============================================================================
# API ROUTES - BRANDS
# =============================================================================

@api_router.post("/brands", response_model=Brand)
async def create_brand(input: BrandCreate):
    brand = Brand(**input.model_dump())
    await db.brands.insert_one(brand.model_dump())
    return brand

@api_router.get("/brands", response_model=List[Brand])
async def get_brands(profile_id: Optional[str] = None):
    query = {"profile_id": profile_id} if profile_id else {}
    brands = await db.brands.find(query, {"_id": 0}).to_list(100)
    return brands

@api_router.get("/brands/{brand_id}", response_model=Brand)
async def get_brand_by_id(brand_id: str):
    brand = await db.brands.find_one({"id": brand_id}, {"_id": 0})
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    return brand

@api_router.put("/brands/{brand_id}", response_model=Brand)
async def update_brand(brand_id: str, updates: Dict[str, Any]):
    brand = await db.brands.find_one({"id": brand_id}, {"_id": 0})
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    await db.brands.update_one({"id": brand_id}, {"$set": updates})
    return await db.brands.find_one({"id": brand_id}, {"_id": 0})

@api_router.delete("/brands/{brand_id}")
async def delete_brand(brand_id: str):
    result = await db.brands.delete_one({"id": brand_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Brand not found")
    return {"message": "Brand deleted"}

# =============================================================================
# API ROUTES - PROJECTS
# =============================================================================

@api_router.post("/projects", response_model=Project)
async def create_project(input: ProjectCreate):
    project = Project(**input.model_dump())
    await db.projects.insert_one(project.model_dump())
    return project

@api_router.get("/projects")
async def get_projects(profile_id: Optional[str] = None):
    query = {"profile_id": profile_id} if profile_id else {"profile_id": {"$exists": True, "$ne": None}}
    projects = await db.projects.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    return projects

@api_router.get("/projects/{project_id}", response_model=Project)
async def get_project(project_id: str):
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@api_router.put("/projects/{project_id}", response_model=Project)
async def update_project(project_id: str, updates: Dict[str, Any]):
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.projects.update_one({"id": project_id}, {"$set": updates})
    return await db.projects.find_one({"id": project_id}, {"_id": 0})

@api_router.delete("/projects/{project_id}")
async def delete_project(project_id: str):
    result = await db.projects.delete_one({"id": project_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"message": "Project deleted"}

# =============================================================================
# API ROUTES - TRANSCRIPTION & MULTI-VIDEO MIXING
# =============================================================================

@api_router.post("/transcribe")
async def transcribe_video(request: TranscribeRequest):
    try:
        logger.info(f"Downloading audio from: {request.video_url}")
        audio_data = await download_video_audio(request.video_url)
        
        logger.info("Transcribing audio...")
        transcript = await transcribe_audio(audio_data)
        
        if request.target_language in ["ar", "en"]:
            logger.info(f"Translating to {request.target_language}...")
            chat = await get_claude_chat(
                session_id=f"translate-{uuid.uuid4()}",
                system_message="You are a professional translator. Translate accurately while preserving tone and style."
            )
            
            lang_name = "Arabic (Egyptian dialect)" if request.target_language == "ar" else "English"
            translate_msg = UserMessage(
                text=f"Translate to {lang_name}. Keep the same style. Only return the translation:\n\n{transcript}"
            )
            transcript = await chat.send_message(translate_msg)
        
        return {
            "transcript": transcript,
            "original_url": request.video_url,
            "language": request.target_language
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Transcription error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/video-info")
async def get_video_info_endpoint(request: VideoInfoRequest):
    """Get video info/metadata without downloading"""
    info = await get_video_metadata(request.video_url)
    return info

@api_router.post("/projects/{project_id}/add-transcript-manual")
async def add_manual_transcript(project_id: str, data: Dict[str, Any]):
    """Manually add a transcript (for when video download is blocked)"""
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    transcript_text = data.get("transcript", "").strip()
    source_url = data.get("source_url", "manual-input")
    language = data.get("language", "ar")
    
    if not transcript_text:
        raise HTTPException(status_code=400, detail="Transcript text is required")
    
    video_urls = project.get("video_urls", [])
    transcripts = project.get("transcripts", [])
    
    video_urls.append(source_url)
    transcripts.append({
        "url": source_url,
        "text": transcript_text,
        "language": language,
        "manual": True,
        "added_at": datetime.now(timezone.utc).isoformat()
    })
    
    await db.projects.update_one(
        {"id": project_id},
        {"$set": {
            "video_urls": video_urls,
            "transcripts": transcripts,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return await db.projects.find_one({"id": project_id}, {"_id": 0})

@api_router.post("/projects/{project_id}/add-video")
async def add_video_to_project(project_id: str, request: TranscribeRequest):
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    result = await transcribe_video(request)
    
    video_urls = project.get("video_urls", [])
    transcripts = project.get("transcripts", [])
    
    video_urls.append(request.video_url)
    transcripts.append({
        "url": request.video_url,
        "text": result["transcript"],
        "language": result["language"],
        "added_at": datetime.now(timezone.utc).isoformat()
    })
    
    await db.projects.update_one(
        {"id": project_id},
        {"$set": {
            "video_urls": video_urls,
            "transcripts": transcripts,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return await db.projects.find_one({"id": project_id}, {"_id": 0})

@api_router.post("/projects/{project_id}/mix-scripts")
async def mix_scripts(project_id: str, request: MixScriptsRequest):
    """Mix multiple video transcripts into one optimized script"""
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    transcripts = project.get("transcripts", [])
    if len(transcripts) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 videos to mix")
    
    # Get profile and brand context
    profile = await get_profile(project["profile_id"])
    profile_context = build_profile_context(profile) if profile else ""
    
    brand_context = ""
    if project.get("brand_id"):
        brand = await get_brand(project["brand_id"])
        if brand:
            brand_context = build_brand_context(brand)
    
    # Combine transcripts
    combined = "\n\n---VIDEO SEPARATOR---\n\n".join([
        f"Video {i+1}:\n{t['text']}" for i, t in enumerate(transcripts)
    ])
    
    system_msg = f"""You are an expert script mixer. You combine multiple video scripts into one powerful, cohesive script.

{profile_context}
{brand_context}

Your task:
1. Analyze each video's strengths
2. Extract the best hooks, body content, and CTAs
3. Combine them into one script that flows naturally
4. Maintain consistent tone and style
5. Keep the structure: Hook → Body → CTA"""

    chat = await get_claude_chat(
        session_id=f"mix-{project_id}",
        system_message=system_msg
    )
    
    focus_text = ""
    if request.focus_areas:
        focus_text = f"\n\nFocus on: {', '.join(request.focus_areas)}"
    
    prompt = f"""Mix these video scripts into one optimized script:

{combined}
{focus_text}

Create one cohesive script combining the best elements from all videos.
Maintain the structure: Hook → Body → CTA"""

    msg = UserMessage(text=prompt)
    mixed_script = await chat.send_message(msg)
    
    await db.projects.update_one(
        {"id": project_id},
        {"$set": {
            "mixed_transcript": mixed_script,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {"mixed_script": mixed_script}

# =============================================================================
# API ROUTES - HOOKS WITH A/B TESTING
# =============================================================================

@api_router.post("/projects/{project_id}/generate-hooks")
async def generate_hooks(project_id: str, request: GenerateHooksRequest):
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get profile and brand context
    profile = await get_profile(project["profile_id"])
    profile_context = build_profile_context(profile) if profile else ""
    profile_language = profile.get("language", "en") if profile else "en"
    
    brand_context = ""
    if project.get("brand_id"):
        brand = await get_brand(project["brand_id"])
        if brand:
            brand_context = build_brand_context(brand)
            if brand.get("hook_templates"):
                brand_context += f"\n\nBrand Hook Templates to inspire from: {' | '.join(brand['hook_templates'])}"
    
    # Use mixed transcript or combine individual transcripts
    source_text = project.get("mixed_transcript") or "\n\n".join([t["text"] for t in project.get("transcripts", [])])
    
    if not source_text:
        raise HTTPException(status_code=400, detail="No transcripts to generate hooks from")
    
    features_text = ""
    if project.get("key_features"):
        features_text = f"\n\nKey features to highlight: {', '.join(project['key_features'])}"
    
    # Get writing style and word count settings
    writing_style = project.get("writing_style", "natural")
    target_words = project.get("target_word_count", 150)
    
    # Determine styles to generate
    styles = request.styles or ["question", "statement", "story", "statistic", "provocative"]
    
    lang_instruction = "Write in Arabic Egyptian dialect (مصري)" if profile_language == "ar" else "Write in English"
    
    system_msg = f"""You are an expert scriptwriter who writes like a real human, not AI.

{profile_context}
{brand_context}

CRITICAL RULES:
1. {lang_instruction}
2. Write naturally - like a real person talking to camera
3. NO AI phrases like "dive into", "game-changer", "unlock", "leverage"
4. NO corporate buzzwords
5. Use conversational language
6. Be direct and authentic
7. Match the style: {writing_style}

Generate hooks that:
- Stop the scroll immediately
- Sound like a real person, not a brand
- Create genuine curiosity
- Are punchy and memorable

IMPORTANT: Return ONLY a valid JSON array, no markdown."""

    chat = await get_claude_chat(
        session_id=f"hooks-{project_id}-{uuid.uuid4()}",
        system_message=system_msg
    )
    
    prompt = f"""Generate {request.count} different hooks.
Styles to use: {', '.join(styles)}

SOURCE CONTENT:
{source_text[:2000]}
{features_text}

{"AD SCRIPT - compelling but natural." if project.get("is_ad") else "ORGANIC - authentic and relatable."}

Return ONLY valid JSON: [{{"text": "hook text", "style": "style_name", "id": "unique_id"}}]"""

    msg = UserMessage(text=prompt)
    response = await chat.send_message(msg)
    
    try:
        response_text = response.strip()
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        hooks = json.loads(response_text)
        
        # Add IDs if missing
        for i, hook in enumerate(hooks):
            if "id" not in hook:
                hook["id"] = str(uuid.uuid4())
            hook["performance"] = {"views": 0, "engagement": 0, "clicks": 0}
    except:
        hooks = [{"text": response, "style": "default", "id": str(uuid.uuid4()), "performance": {}}]
    
    await db.projects.update_one(
        {"id": project_id},
        {"$set": {
            "hooks": hooks,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {"hooks": hooks}

@api_router.post("/projects/{project_id}/select-hooks")
async def select_hooks_for_ab(project_id: str, hook_indices: List[int]):
    """Select multiple hooks for A/B testing"""
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    await db.projects.update_one(
        {"id": project_id},
        {"$set": {
            "selected_hook_indices": hook_indices,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return await db.projects.find_one({"id": project_id}, {"_id": 0})

@api_router.post("/projects/{project_id}/update-hook-performance")
async def update_hook_performance(project_id: str, update: HookPerformanceUpdate):
    """Update performance metrics for a hook (A/B testing data)"""
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    hooks = project.get("hooks", [])
    if update.hook_index >= len(hooks):
        raise HTTPException(status_code=400, detail="Invalid hook index")
    
    hooks[update.hook_index]["performance"] = {
        "views": update.views,
        "engagement": update.engagement,
        "clicks": update.clicks,
        "notes": update.notes,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.projects.update_one(
        {"id": project_id},
        {"$set": {"hooks": hooks, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    # Learn from successful hooks
    if update.engagement > 0.05:  # 5% engagement threshold
        profile_id = project.get("profile_id")
        if profile_id:
            hook_text = hooks[update.hook_index].get("text", "")
            profile = await get_profile(profile_id)
            if profile:
                successful = profile.get("successful_hooks", [])
                successful.append(hook_text)
                if len(successful) > 50:
                    successful = successful[-50:]
                await db.profiles.update_one(
                    {"id": profile_id},
                    {"$set": {"successful_hooks": successful}}
                )
    
    return {"message": "Performance updated"}

# =============================================================================
# API ROUTES - BODY & CTA GENERATION
# =============================================================================

@api_router.post("/projects/{project_id}/generate-body")
async def generate_body(project_id: str):
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    selected_indices = project.get("selected_hook_indices", [])
    if not selected_indices and project.get("selected_hook_index") is not None:
        selected_indices = [project["selected_hook_index"]]
    
    if not selected_indices or not project.get("hooks"):
        raise HTTPException(status_code=400, detail="Please select a hook first")
    
    selected_hook = project["hooks"][selected_indices[0]]
    source_text = project.get("mixed_transcript") or "\n\n".join([t["text"] for t in project.get("transcripts", [])])
    
    # Get contexts
    profile = await get_profile(project["profile_id"])
    profile_context = build_profile_context(profile) if profile else ""
    profile_language = profile.get("language", "en") if profile else "en"
    
    brand_context = ""
    if project.get("brand_id"):
        brand = await get_brand(project["brand_id"])
        if brand:
            brand_context = build_brand_context(brand)
    
    features_text = ""
    if project.get("key_features"):
        features_text = f"\n\nKey features to include: {', '.join(project['key_features'])}"
    
    # Get script settings
    target_words = project.get("target_word_count", 150)
    writing_style = project.get("writing_style", "natural")
    
    # Calculate body word count (hook ~15 words, CTA ~20 words, rest is body)
    body_words = max(target_words - 35, 50)
    
    lang_instruction = "Write in Arabic Egyptian dialect (مصري عامي)" if profile_language == "ar" else "Write in English"
    
    system_msg = f"""You are a human scriptwriter, NOT an AI.

{profile_context}
{brand_context}

CRITICAL RULES:
1. {lang_instruction}
2. Write exactly like a real person talks - conversational, natural
3. FORBIDDEN PHRASES: "dive into", "game-changer", "unlock potential", "leverage", "empower", "cutting-edge", "revolutionary"
4. Use simple, everyday language
5. Be direct - no fluff or filler
6. Style: {writing_style}
7. Target approximately {body_words} words for the body

Write body content that:
- Flows naturally from the hook
- Keeps viewer attention
- Sounds authentic, not scripted
- Builds toward the CTA"""

    chat = await get_claude_chat(
        session_id=f"body-{project_id}",
        system_message=system_msg
    )
    
    prompt = f"""Write the BODY section (middle part) of a script.

HOOK: {selected_hook['text']}

SOURCE CONTENT:
{source_text[:2000]}
{features_text}

Target approximately {body_words} words.
{"AD SCRIPT - persuasive but natural." if project.get("is_ad") else "ORGANIC - authentic and relatable."}

Write ONLY the body content, no hook, no CTA."""

    msg = UserMessage(text=prompt)
    body_content = await chat.send_message(msg)
    
    await db.projects.update_one(
        {"id": project_id},
        {"$set": {
            "body_content": body_content,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {"body_content": body_content}

@api_router.post("/projects/{project_id}/generate-cta")
async def generate_cta(project_id: str):
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get contexts
    profile = await get_profile(project["profile_id"])
    profile_context = build_profile_context(profile) if profile else ""
    
    brand_context = ""
    if project.get("brand_id"):
        brand = await get_brand(project["brand_id"])
        if brand:
            brand_context = build_brand_context(brand)
            if brand.get("cta_templates"):
                brand_context += f"\n\nBrand CTA Templates: {' | '.join(brand['cta_templates'])}"
    
    selected_indices = project.get("selected_hook_indices", [])
    if not selected_indices and project.get("selected_hook_index") is not None:
        selected_indices = [project["selected_hook_index"]]
    
    selected_hook = project["hooks"][selected_indices[0]] if project.get("hooks") and selected_indices else {"text": ""}
    
    system_msg = f"""You are an expert at writing compelling calls-to-action.

{profile_context}
{brand_context}

Create CTAs that:
- Are clear and direct
- Create urgency
- Match the tone of the content
- Drive the desired action"""

    chat = await get_claude_chat(
        session_id=f"cta-{project_id}",
        system_message=system_msg
    )
    
    prompt = f"""Write a compelling CTA for this script.

HOOK: {selected_hook['text']}
BODY: {project.get('body_content', '')}

{"AD SCRIPT" if project.get("is_ad") else "ORGANIC CONTENT"}

Write ONLY the CTA, 1-3 sentences max."""

    msg = UserMessage(text=prompt)
    cta_content = await chat.send_message(msg)
    
    await db.projects.update_one(
        {"id": project_id},
        {"$set": {
            "cta_content": cta_content,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {"cta_content": cta_content}

@api_router.post("/projects/{project_id}/finalize-script")
async def finalize_script(project_id: str):
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get profile for language
    profile = await get_profile(project["profile_id"])
    profile_language = profile.get("language", "en") if profile else "en"
    
    selected_indices = project.get("selected_hook_indices", [])
    if not selected_indices and project.get("selected_hook_index") is not None:
        selected_indices = [project["selected_hook_index"]]
    
    selected_hook = project["hooks"][selected_indices[0]] if project.get("hooks") and selected_indices else {"text": ""}
    
    final_script = f"""{selected_hook.get('text', '')}

{project.get('body_content', '')}

{project.get('cta_content', '')}"""
    
    # Calculate stats
    stats = calculate_script_stats(final_script, profile_language)
    
    # Save version
    versions = project.get("script_versions", [])
    versions.append({
        "script": final_script,
        "hook_index": selected_indices[0] if selected_indices else None,
        "word_count": stats["word_count"],
        "duration_seconds": stats["duration_seconds"],
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    await db.projects.update_one(
        {"id": project_id},
        {"$set": {
            "final_script": final_script,
            "actual_word_count": stats["word_count"],
            "estimated_duration_seconds": stats["duration_seconds"],
            "script_versions": versions,
            "status": "completed",
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Learn from this script
    await learn_from_script(project["profile_id"], project, final_script)
    
    return {
        "final_script": final_script,
        "word_count": stats["word_count"],
        "estimated_duration": stats["duration_display"],
        "duration_seconds": stats["duration_seconds"]
    }

# =============================================================================
# API ROUTES - CAPTION INTELLIGENCE
# =============================================================================

@api_router.post("/projects/{project_id}/generate-caption")
async def generate_caption(project_id: str, request: GenerateCaptionRequest = None):
    if request is None:
        request = GenerateCaptionRequest()
    
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get profile and brand context
    profile = await get_profile(project["profile_id"])
    profile_language = profile.get("language", "en") if profile else "en"
    profile_context = ""
    if profile:
        profile_context = f"""
Caption Tone: {profile.get('caption_tone', 'professional')}
Emoji Usage: {profile.get('emoji_usage', 'moderate')}
Preferred Hashtag Count: {profile.get('hashtag_count', 5)}
"""
        if profile.get("preferred_hashtags"):
            profile_context += f"Always include: {', '.join(profile['preferred_hashtags'][:5])}"
    
    brand_context = ""
    brand_hashtags = []
    if project.get("brand_id"):
        brand = await get_brand(project["brand_id"])
        if brand:
            brand_context = f"""
Brand Caption Style: {brand.get('caption_style', '')}
Emoji Style: {brand.get('emoji_style', 'moderate')}
Caption Length: {brand.get('caption_length', 'medium')}
"""
            brand_hashtags = brand.get("hashtags", [])
    
    # Platform-specific limits and styles
    platform_config = {
        "tiktok": {
            "max_chars": 2200,
            "hashtag_placement": "inline or at end",
            "style": "casual, trendy, uses viral language. Short punchy captions work best.",
            "typical_hashtag_count": 5
        },
        "instagram": {
            "max_chars": 2200,
            "hashtag_placement": "in first comment or at end separated by dots",
            "style": "storytelling, relatable, call-to-action. Can be longer.",
            "typical_hashtag_count": 15
        },
        "youtube": {
            "max_chars": 5000,
            "hashtag_placement": "first 3 in description, rest in comments",
            "style": "SEO-optimized, descriptive, keyword-rich. Include timestamps if applicable.",
            "typical_hashtag_count": 5
        }
    }
    
    platform = request.platform or "tiktok"
    pconfig = platform_config.get(platform, platform_config["tiktok"])
    
    # Determine tone
    tone = request.tone
    if tone == "auto":
        tone = profile.get("caption_tone", "casual") if profile else "casual"
    
    lang_instruction = "Write in Arabic Egyptian dialect (مصري عامي)" if profile_language == "ar" else "Write in English"
    
    system_msg = f"""You are an expert social media manager specializing in {platform.title()} content.

{profile_context}
{brand_context}

Platform: {platform.title()}
Max Characters: {pconfig['max_chars']}
Hashtag Placement: {pconfig['hashtag_placement']}
Platform Style: {pconfig['style']}
Caption Tone: {tone}

CRITICAL RULES:
1. {lang_instruction}
2. Write like a real person, NOT an AI
3. Use emojis naturally based on the specified style
4. Create engagement hooks in captions (questions, CTAs)
5. Hashtags should be a mix of trending, niche-specific, and branded"""

    chat = await get_claude_chat(
        session_id=f"caption-{project_id}-{uuid.uuid4()}",
        system_message=system_msg
    )
    
    hashtag_count = request.hashtag_count or pconfig["typical_hashtag_count"]
    
    script_text = project.get('final_script', project.get('body_content', ''))
    transcripts_text = "\n".join([t.get("text", "")[:300] for t in project.get("transcripts", [])])
    
    prompt = f"""Write 3 caption variations and {hashtag_count} hashtags for this {platform.title()} video.

SCRIPT:
{script_text}

VIDEO CONTEXT:
{transcripts_text[:500]}

{"Brand hashtags to always include: " + ", ".join(brand_hashtags) if brand_hashtags else ""}

Return ONLY valid JSON in this exact format:
{{
    "captions": [
        "first caption variation",
        "second caption variation",
        "third caption variation"
    ],
    "hashtags": {{
        "trending": ["#tag1", "#tag2", "#tag3"],
        "niche": ["#tag4", "#tag5", "#tag6"],
        "branded": ["#tag7", "#tag8"]
    }},
    "caption_tips": "One sentence tip about what makes good captions for this content on {platform.title()}"
}}"""

    msg = UserMessage(text=prompt)
    response = await chat.send_message(msg)
    
    # Parse structured response
    captions = []
    hashtags_categorized = {"trending": [], "niche": [], "branded": []}
    all_hashtags = []
    caption_tips = ""
    
    try:
        response_text = response.strip()
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        parsed = json.loads(response_text)
        
        captions = parsed.get("captions", [])
        hashtags_categorized = parsed.get("hashtags", {})
        caption_tips = parsed.get("caption_tips", "")
        
        # Flatten hashtags
        for category in hashtags_categorized.values():
            if isinstance(category, list):
                all_hashtags.extend(category)
    except Exception:
        # Fallback: parse as text
        lines = response.strip().split("\n")
        for line in lines:
            if line.upper().startswith("CAPTION"):
                caption = line.split(":", 1)[1].strip() if ":" in line else ""
                if caption:
                    captions.append(caption)
            elif line.upper().startswith("HASHTAGS:"):
                hashtag_text = line.split(":", 1)[1].strip()
                all_hashtags = [h.strip() for h in hashtag_text.split() if h.startswith("#")]
    
    # Add brand hashtags
    for h in brand_hashtags:
        tag = h if h.startswith("#") else f"#{h}"
        if tag not in all_hashtags:
            all_hashtags.append(tag)
            if "branded" not in hashtags_categorized:
                hashtags_categorized["branded"] = []
            hashtags_categorized["branded"].append(tag)
    
    # Add profile preferred hashtags
    if profile and profile.get("preferred_hashtags"):
        for h in profile["preferred_hashtags"]:
            tag = h if h.startswith("#") else f"#{h}"
            if tag not in all_hashtags:
                all_hashtags.append(tag)
    
    await db.projects.update_one(
        {"id": project_id},
        {"$set": {
            "caption": captions[0] if captions else "",
            "caption_variations": captions,
            "hashtags": all_hashtags[:20],
            "hashtags_categorized": hashtags_categorized,
            "caption_tips": caption_tips,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {
        "captions": captions,
        "hashtags": all_hashtags,
        "hashtags_categorized": hashtags_categorized,
        "caption_tips": caption_tips,
        "platform": platform
    }

# =============================================================================
# API ROUTES - CHAT
# =============================================================================

@api_router.post("/projects/{project_id}/chat")
async def chat_with_claude(project_id: str, request: ChatRequest):
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get current content based on section
    current_content = ""
    if request.section == "hook" and project.get("hooks"):
        indices = project.get("selected_hook_indices", [])
        if not indices and project.get("selected_hook_index") is not None:
            indices = [project["selected_hook_index"]]
        if indices:
            current_content = project["hooks"][indices[0]].get("text", "")
    elif request.section == "body":
        current_content = project.get("body_content", "")
    elif request.section == "cta":
        current_content = project.get("cta_content", "")
    else:
        current_content = project.get("final_script", "")
    
    # Get chat history
    chat_history = await db.chat_messages.find(
        {"project_id": project_id},
        {"_id": 0}
    ).sort("created_at", 1).to_list(50)
    
    history_context = "\n".join([f"{m['role']}: {m['content']}" for m in chat_history[-10:]])
    
    # Get profile context
    profile = await get_profile(project["profile_id"])
    profile_context = build_profile_context(profile) if profile else ""
    
    system_msg = f"""You are an expert script editor helping improve social media video scripts.
{profile_context}

You maintain the SAME STRUCTURE and style while making improvements.
Be concise and direct.

Current {request.section or 'script'} content:
{current_content}

Previous conversation:
{history_context}"""

    chat = await get_claude_chat(
        session_id=f"chat-{project_id}",
        system_message=system_msg
    )
    
    msg = UserMessage(text=request.message)
    response = await chat.send_message(msg)
    
    # Save messages
    user_msg = ChatMessage(
        project_id=project_id,
        profile_id=project["profile_id"],
        role="user",
        content=request.message,
        section=request.section
    )
    assistant_msg = ChatMessage(
        project_id=project_id,
        profile_id=project["profile_id"],
        role="assistant",
        content=response,
        section=request.section
    )
    
    await db.chat_messages.insert_many([user_msg.model_dump(), assistant_msg.model_dump()])
    
    return {"response": response, "section": request.section}

@api_router.get("/projects/{project_id}/chat-history")
async def get_chat_history(project_id: str):
    messages = await db.chat_messages.find(
        {"project_id": project_id},
        {"_id": 0}
    ).sort("created_at", 1).to_list(100)
    return {"messages": messages}

# =============================================================================
# API ROUTES - ANALYTICS
# =============================================================================

@api_router.get("/profiles/{profile_id}/analytics")
async def get_profile_analytics(profile_id: str):
    """Get analytics and learning data for a profile"""
    profile = await get_profile(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # Get project stats
    projects = await db.projects.find({"profile_id": profile_id}, {"_id": 0}).to_list(1000)
    
    total_projects = len(projects)
    completed_projects = len([p for p in projects if p.get("status") == "completed"])
    ad_projects = len([p for p in projects if p.get("is_ad")])
    
    # Hook performance analysis
    hook_performance = {}
    for project in projects:
        for hook in project.get("hooks", []):
            style = hook.get("style", "unknown")
            perf = hook.get("performance", {})
            if style not in hook_performance:
                hook_performance[style] = {"count": 0, "total_engagement": 0}
            hook_performance[style]["count"] += 1
            hook_performance[style]["total_engagement"] += perf.get("engagement", 0)
    
    return {
        "profile": profile,
        "stats": {
            "total_projects": total_projects,
            "completed_projects": completed_projects,
            "ad_projects": ad_projects,
            "organic_projects": total_projects - ad_projects
        },
        "hook_preferences": profile.get("hook_preferences", {}),
        "hook_performance": hook_performance,
        "successful_hooks": profile.get("successful_hooks", [])[-10:]
    }

# =============================================================================
# API ROUTES - TRACKED ACCOUNTS
# =============================================================================

@api_router.post("/tracked-accounts", response_model=TrackedAccount)
async def create_tracked_account(input: TrackedAccountCreate):
    """Add a new account to track for style learning"""
    from datetime import timedelta
    
    # Calculate next analysis time
    freq_days = {"daily": 1, "weekly": 7, "biweekly": 14}.get(input.check_frequency, 7)
    next_analysis = datetime.now(timezone.utc) + timedelta(days=freq_days)
    
    account = TrackedAccount(
        **input.model_dump(),
        next_analysis_at=next_analysis.isoformat()
    )
    await db.tracked_accounts.insert_one(account.model_dump())
    return account

@api_router.get("/tracked-accounts", response_model=List[TrackedAccount])
async def get_tracked_accounts(profile_id: Optional[str] = None):
    """Get all tracked accounts, optionally filtered by profile"""
    query = {"profile_id": profile_id} if profile_id else {}
    accounts = await db.tracked_accounts.find(query, {"_id": 0}).to_list(100)
    return accounts

@api_router.get("/tracked-accounts/{account_id}", response_model=TrackedAccount)
async def get_tracked_account(account_id: str):
    """Get a specific tracked account"""
    account = await db.tracked_accounts.find_one({"id": account_id}, {"_id": 0})
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account

@api_router.delete("/tracked-accounts/{account_id}")
async def delete_tracked_account(account_id: str):
    """Remove a tracked account"""
    result = await db.tracked_accounts.delete_one({"id": account_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Account not found")
    # Also delete analyzed videos
    await db.analyzed_videos.delete_many({"tracked_account_id": account_id})
    return {"message": "Account and its videos deleted"}

@api_router.put("/tracked-accounts/{account_id}", response_model=TrackedAccount)
async def update_tracked_account(account_id: str, updates: Dict[str, Any]):
    """Update tracked account settings"""
    account = await db.tracked_accounts.find_one({"id": account_id}, {"_id": 0})
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.tracked_accounts.update_one({"id": account_id}, {"$set": updates})
    return await db.tracked_accounts.find_one({"id": account_id}, {"_id": 0})

@api_router.post("/tracked-accounts/{account_id}/analyze")
async def analyze_tracked_account(account_id: str, video_limit: int = 5):
    """Scrape and analyze videos from a tracked account"""
    from datetime import timedelta
    
    account = await db.tracked_accounts.find_one({"id": account_id}, {"_id": 0})
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    profile = await get_profile(account["profile_id"])
    profile_language = profile.get("language", "en") if profile else "en"
    
    # Get videos from account
    logger.info(f"Fetching videos from {account['account_url']}")
    videos = await get_account_videos(account["account_url"], account["platform"], video_limit)
    
    if not videos:
        return {
            "message": "No videos found or failed to fetch",
            "videos_analyzed": 0
        }
    
    # Filter by engagement threshold
    min_engagement = account.get("min_engagement_threshold", 1000)
    high_engagement_videos = [v for v in videos if v.get("view_count", 0) >= min_engagement]
    
    if not high_engagement_videos:
        high_engagement_videos = videos[:video_limit]  # Use top videos anyway
    
    analyzed_results = []
    
    for video_info in high_engagement_videos[:video_limit]:
        video_url = video_info.get("url")
        if not video_url:
            continue
        
        try:
            # Download and transcribe
            logger.info(f"Analyzing video: {video_url}")
            audio_data = await download_video_audio(video_url)
            transcript = await transcribe_audio(audio_data)
            
            # Translate if needed
            if profile_language == "ar":
                chat = await get_claude_chat(
                    session_id=f"translate-{uuid.uuid4()}",
                    system_message="Translate to Arabic Egyptian dialect. Only return translation."
                )
                msg = UserMessage(text=f"Translate this:\n\n{transcript}")
                transcript = await chat.send_message(msg)
            
            # Analyze structure
            analysis = await analyze_script_structure(transcript, profile_language)
            
            # Calculate engagement rate
            views = video_info.get("view_count", 0)
            likes = video_info.get("like_count", 0)
            engagement_rate = (likes / views * 100) if views > 0 else 0
            
            # Save analyzed video
            analyzed_video = AnalyzedVideo(
                tracked_account_id=account_id,
                profile_id=account["profile_id"],
                video_url=video_url,
                video_title=video_info.get("title", ""),
                duration=video_info.get("duration", 0),
                views=views,
                likes=likes,
                comments=video_info.get("comment_count", 0),
                engagement_rate=engagement_rate,
                transcript=transcript,
                detected_language=profile_language,
                hook_text=analysis.get("hook_text", ""),
                hook_style=analysis.get("hook_style", ""),
                body_structure=analysis.get("body_structure", ""),
                cta_text=analysis.get("cta_text", ""),
                cta_style=analysis.get("cta_style", ""),
                tone=analysis.get("tone", ""),
                pacing=analysis.get("pacing", ""),
                key_phrases=analysis.get("key_phrases", []),
                emotional_triggers=analysis.get("emotional_triggers", [])
            )
            
            await db.analyzed_videos.insert_one(analyzed_video.model_dump())
            analyzed_results.append(analysis)
            
        except Exception as e:
            logger.error(f"Error analyzing video {video_url}: {e}")
            continue
    
    # Update account stats
    freq_days = {"daily": 1, "weekly": 7, "biweekly": 14}.get(account.get("check_frequency", "weekly"), 7)
    next_analysis = datetime.now(timezone.utc) + timedelta(days=freq_days)
    
    # Aggregate common patterns
    all_hook_styles = [r.get("hook_style", "") for r in analyzed_results if r.get("hook_style")]
    all_cta_styles = [r.get("cta_style", "") for r in analyzed_results if r.get("cta_style")]
    
    await db.tracked_accounts.update_one(
        {"id": account_id},
        {"$set": {
            "total_videos_analyzed": account.get("total_videos_analyzed", 0) + len(analyzed_results),
            "last_analysis_at": datetime.now(timezone.utc).isoformat(),
            "next_analysis_at": next_analysis.isoformat(),
            "common_hook_styles": list(set(all_hook_styles)),
            "common_cta_styles": list(set(all_cta_styles)),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Generate and save insights
    insights = await generate_style_insights(account["profile_id"], analyzed_results)
    if insights:
        await db.style_insights.insert_many(insights)
    
    return {
        "message": f"Analyzed {len(analyzed_results)} videos",
        "videos_analyzed": len(analyzed_results),
        "insights_generated": len(insights),
        "next_analysis_at": next_analysis.isoformat()
    }

@api_router.get("/tracked-accounts/{account_id}/videos")
async def get_analyzed_videos(account_id: str, limit: int = 20):
    """Get analyzed videos for a tracked account"""
    videos = await db.analyzed_videos.find(
        {"tracked_account_id": account_id},
        {"_id": 0}
    ).sort("analyzed_at", -1).to_list(limit)
    return {"videos": videos}

@api_router.get("/profiles/{profile_id}/style-insights")
async def get_style_insights(profile_id: str, limit: int = 10):
    """Get style insights for a profile based on tracked account analysis"""
    insights = await db.style_insights.find(
        {"profile_id": profile_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(limit)
    
    # Also get aggregated data from all tracked accounts
    accounts = await db.tracked_accounts.find(
        {"profile_id": profile_id, "is_active": True},
        {"_id": 0}
    ).to_list(100)
    
    # Get recent analyzed videos
    recent_videos = await db.analyzed_videos.find(
        {"profile_id": profile_id},
        {"_id": 0}
    ).sort("analyzed_at", -1).to_list(50)
    
    # Aggregate top hooks
    top_hooks = []
    for video in recent_videos:
        if video.get("hook_text") and video.get("engagement_rate", 0) > 1:
            top_hooks.append({
                "text": video["hook_text"],
                "style": video.get("hook_style", ""),
                "engagement": video.get("engagement_rate", 0),
                "source": video.get("video_url", "")
            })
    
    # Sort by engagement
    top_hooks.sort(key=lambda x: x["engagement"], reverse=True)
    
    return {
        "insights": insights,
        "tracked_accounts_count": len(accounts),
        "total_videos_analyzed": sum(a.get("total_videos_analyzed", 0) for a in accounts),
        "top_performing_hooks": top_hooks[:10]
    }

@api_router.post("/profiles/{profile_id}/analyze-all-accounts")
async def analyze_all_accounts(profile_id: str, video_limit: int = 3):
    """Trigger analysis for all active tracked accounts of a profile"""
    accounts = await db.tracked_accounts.find(
        {"profile_id": profile_id, "is_active": True},
        {"_id": 0}
    ).to_list(100)
    
    if not accounts:
        return {"message": "No active tracked accounts found", "analyzed": 0}
    
    results = []
    for account in accounts:
        try:
            result = await analyze_tracked_account(account["id"], video_limit)
            results.append({
                "account": account["account_name"],
                "videos_analyzed": result.get("videos_analyzed", 0)
            })
        except Exception as e:
            results.append({
                "account": account["account_name"],
                "error": str(e)
            })
    
    return {
        "message": f"Analyzed {len(results)} accounts",
        "results": results
    }

# Include router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    logger.info("Application starting up...")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
