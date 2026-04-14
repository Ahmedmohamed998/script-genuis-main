# Script Genius - PRD (Product Requirements Document)

## Original Problem Statement
AI Script Writing System with advanced features:
- Multi-Video Mixing & transcription
- Smart Learning System
- A/B Hook Testing (5+ options)
- Brand Voice DNA
- Caption & Hashtag Intelligence
- Two separate profiles: derjotech (English Ads) & mohabtech (Arabic Egyptian natural scripts)
- Style Tracker: track top-performing accounts to learn their style
- ElevenLabs Voiceover integration
- Client Approval Workflow

## Architecture

### Backend (FastAPI + MongoDB)
- **server.py**: Main API with all endpoints
- **Models**: Profile, Brand, Project, TrackedAccount, AnalyzedVideo, StyleInsight, ChatMessage
- **Integrations**: 
  - Claude Opus 4.6 (via Emergent LLM Key)
  - OpenAI Whisper (for transcription via Emergent)
  - ElevenLabs TTS (MOCKED - needs user API key)
  - Emergent Object Storage
  - yt-dlp + ffmpeg (video download & audio extraction)

### Frontend (React + Tailwind + Shadcn UI + Phosphor Icons)
- **Dashboard**: Stats overview, recent projects
- **Projects**: List, create, edit with multi-video support
- **Brands**: Voice DNA management
- **Style Tracker**: Track accounts, analyze videos, view insights
- **Analytics**: Learning insights, hook preferences
- **Project Editor**: Full script workflow (Hooks > Body > CTA > Final)

## User Personas
1. **derjotech**: English, AD scripts, professional tone
2. **mohabtech**: Arabic Egyptian, mixed content, casual/natural tone

## Core Requirements
- [x] Video URL transcription (YouTube works, TikTok/Instagram blocked from server)
- [x] Manual transcript paste (fallback for blocked platforms)
- [x] Video info preview before transcribing
- [x] Platform detection (TikTok/Instagram/YouTube)
- [x] Language translation (Arabic Egyptian/English)
- [x] Multi-video mixing
- [x] Hook generation with A/B testing (5+ hooks)
- [x] Body content generation
- [x] CTA generation
- [x] Script finalization with word count/duration stats
- [x] Post-generation word count slider (Final tab)
- [x] Chat editing with Claude
- [x] Caption Intelligence with platform-specific optimization
- [x] Hashtag categorization (trending/niche/branded)
- [x] Caption tone selection (auto/casual/professional/funny/educational)
- [x] Brand Voice DNA management
- [x] Profile-based learning & preference tracking
- [x] Analytics dashboard
- [x] Style Tracker - account tracking & video analysis

## What's Been Implemented

### 2026-04-11 (Session 1)
- Full MVP: Dashboard, Projects, Brands, Script Editor, Style Tracker, Analytics
- Dual profile system (Derjo Tech / Mohab Tech)
- Brand Voice DNA with personality, favorite/forbidden words
- Multi-video support with mixing
- A/B Hook testing with 5+ hooks
- Script generation pipeline: Hooks > Body > CTA > Final
- Post-generation word count slider in Final tab
- Chat interface for iterative editing
- Basic caption generation

### 2026-04-11 (Session 2 - Current)
- **Caption & Hashtag Intelligence**: Platform-specific captions (TikTok/Instagram/YouTube), tone selector, categorized hashtags (trending/niche/branded), caption tips
- **Video URL Transcription**: Real yt-dlp + ffmpeg integration, video info preview, platform detection with icons, helpful error messages for blocked platforms
- **Manual Transcript**: Paste Script mode for when video URLs are blocked
- Fixed old projects validation error (missing profile_id)
- Fixed yt-dlp/ffmpeg paths for subprocess execution

## Prioritized Backlog

### P0 (Critical) - DONE
- [x] Profile system with data isolation
- [x] Multi-video mixing
- [x] A/B hook testing
- [x] Brand Voice DNA
- [x] Style Tracker
- [x] Caption & Hashtag Intelligence
- [x] Video URL Transcription (real)

### P1 (High)
- [ ] ElevenLabs Voiceover (needs user API key)
- [ ] Client Approval Workflow (shareable link for client review/approve)
- [ ] Scheduled auto-analysis for Style Tracker (cron)

### P2 (Medium)
- [ ] Refactor App.js (~2900 lines) into smaller components
- [ ] Export scripts to PDF/Doc
- [ ] Competitor comparison view
- [ ] Trend alerts

### P3 (Low)
- [ ] Team collaboration features
- [ ] Email notifications

## Next Tasks
1. ElevenLabs Voiceover integration (user API key required)
2. Client Approval Workflow (shareable link)
3. Refactor App.js into components
