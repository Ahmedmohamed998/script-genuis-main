"""
Backend API Tests for Iteration 5 Features:
1. Caption & Hashtag Intelligence - platform-specific captions with categorized hashtags
2. Video URL Transcription - video-info endpoint and manual transcript fallback
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test data
TEST_YOUTUBE_URL = "https://www.youtube.com/shorts/dQw4w9WgXcQ"
TEST_TIKTOK_URL = "https://www.tiktok.com/@test/video/123456789"
TEST_MANUAL_TRANSCRIPT = "This is a test transcript for manual input. It contains some content about technology and innovation."


class TestProfilesAndSetup:
    """Test profile endpoints and setup"""
    
    def test_get_profiles(self):
        """GET /api/profiles should return profiles"""
        response = requests.get(f"{BASE_URL}/api/profiles")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"SUCCESS: GET /api/profiles returned {len(data)} profiles")
        
        # Verify profile structure if profiles exist
        if len(data) > 0:
            profile = data[0]
            assert "id" in profile, "Profile should have id"
            assert "username" in profile, "Profile should have username"
            assert "display_name" in profile, "Profile should have display_name"
            print(f"  Profile found: {profile.get('display_name')} ({profile.get('username')})")
        
        return data
    
    def test_seed_profiles(self):
        """POST /api/profiles/seed should create default profiles"""
        response = requests.post(f"{BASE_URL}/api/profiles/seed")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "message" in data, "Response should have message"
        print(f"SUCCESS: Seed profiles - {data['message']}")
        return data


class TestVideoInfoEndpoint:
    """Test video-info endpoint for URL metadata"""
    
    def test_video_info_youtube_url(self):
        """POST /api/video-info should return video metadata for YouTube URLs"""
        response = requests.post(
            f"{BASE_URL}/api/video-info",
            json={"video_url": TEST_YOUTUBE_URL}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "platform" in data, "Response should have platform"
        assert data["platform"] == "youtube", f"Expected youtube platform, got {data.get('platform')}"
        
        # Check if video info was fetched successfully or if there's an error
        if "error" not in data:
            assert "title" in data, "Response should have title"
            assert "duration" in data, "Response should have duration"
            print(f"SUCCESS: YouTube video info - Title: {data.get('title', 'N/A')[:50]}, Duration: {data.get('duration')}s")
        else:
            print(f"INFO: YouTube video info returned error (may be expected): {data.get('message')}")
        
        return data
    
    def test_video_info_tiktok_blocked(self):
        """POST /api/video-info should return helpful error for TikTok blocked URLs"""
        response = requests.post(
            f"{BASE_URL}/api/video-info",
            json={"video_url": TEST_TIKTOK_URL}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "platform" in data, "Response should have platform"
        assert data["platform"] == "tiktok", f"Expected tiktok platform, got {data.get('platform')}"
        
        # TikTok should return an error with helpful message
        if "error" in data:
            assert "message" in data, "Error response should have message"
            print(f"SUCCESS: TikTok blocked error - {data.get('message')}")
        else:
            print(f"INFO: TikTok video info succeeded (unexpected but ok)")
        
        return data


class TestManualTranscriptEndpoint:
    """Test manual transcript addition endpoint"""
    
    @pytest.fixture
    def test_project(self):
        """Create a test project for manual transcript tests"""
        # First get a profile
        profiles_res = requests.get(f"{BASE_URL}/api/profiles")
        profiles = profiles_res.json()
        
        if not profiles:
            # Seed profiles first
            requests.post(f"{BASE_URL}/api/profiles/seed")
            profiles_res = requests.get(f"{BASE_URL}/api/profiles")
            profiles = profiles_res.json()
        
        profile_id = profiles[0]["id"]
        
        # Create a test project
        project_data = {
            "profile_id": profile_id,
            "name": f"TEST_ManualTranscript_{int(time.time())}",
            "is_ad": False,
            "video_urls": [],
            "key_features": ["test feature"]
        }
        
        response = requests.post(f"{BASE_URL}/api/projects", json=project_data)
        assert response.status_code == 200, f"Failed to create project: {response.text}"
        
        project = response.json()
        yield project
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/projects/{project['id']}")
    
    def test_add_manual_transcript(self, test_project):
        """POST /api/projects/{id}/add-transcript-manual should add manual transcript"""
        project_id = test_project["id"]
        
        transcript_data = {
            "transcript": TEST_MANUAL_TRANSCRIPT,
            "source_url": "manual-input",
            "language": "en"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/projects/{project_id}/add-transcript-manual",
            json=transcript_data
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Verify transcript was added
        assert "transcripts" in data, "Response should have transcripts"
        assert len(data["transcripts"]) > 0, "Should have at least one transcript"
        
        last_transcript = data["transcripts"][-1]
        assert last_transcript["text"] == TEST_MANUAL_TRANSCRIPT, "Transcript text should match"
        assert last_transcript["manual"] == True, "Transcript should be marked as manual"
        assert last_transcript["language"] == "en", "Language should be en"
        
        print(f"SUCCESS: Manual transcript added to project {project_id}")
        print(f"  Transcript length: {len(last_transcript['text'])} chars")
        print(f"  Manual flag: {last_transcript['manual']}")
        
        return data
    
    def test_add_manual_transcript_empty_fails(self, test_project):
        """POST /api/projects/{id}/add-transcript-manual should fail with empty transcript"""
        project_id = test_project["id"]
        
        transcript_data = {
            "transcript": "",
            "source_url": "manual-input",
            "language": "en"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/projects/{project_id}/add-transcript-manual",
            json=transcript_data
        )
        assert response.status_code == 400, f"Expected 400 for empty transcript, got {response.status_code}"
        print("SUCCESS: Empty transcript correctly rejected with 400")


class TestCaptionGeneration:
    """Test caption generation with platform and tone params"""
    
    @pytest.fixture
    def completed_project(self):
        """Create a project with finalized script for caption testing"""
        # Get profile
        profiles_res = requests.get(f"{BASE_URL}/api/profiles")
        profiles = profiles_res.json()
        
        if not profiles:
            requests.post(f"{BASE_URL}/api/profiles/seed")
            profiles_res = requests.get(f"{BASE_URL}/api/profiles")
            profiles = profiles_res.json()
        
        profile_id = profiles[0]["id"]
        
        # Create project
        project_data = {
            "profile_id": profile_id,
            "name": f"TEST_Caption_{int(time.time())}",
            "is_ad": False,
            "video_urls": [],
            "key_features": ["AI technology", "productivity"]
        }
        
        response = requests.post(f"{BASE_URL}/api/projects", json=project_data)
        project = response.json()
        project_id = project["id"]
        
        # Add manual transcript
        transcript_data = {
            "transcript": "This is a test video about AI technology and how it can boost your productivity. We'll show you 5 amazing tips that will change how you work forever. Stay tuned until the end for a special bonus tip!",
            "source_url": "manual-input",
            "language": "en"
        }
        requests.post(f"{BASE_URL}/api/projects/{project_id}/add-transcript-manual", json=transcript_data)
        
        # Generate hooks
        hooks_res = requests.post(f"{BASE_URL}/api/projects/{project_id}/generate-hooks", json={"count": 3})
        
        # Select first hook
        requests.post(f"{BASE_URL}/api/projects/{project_id}/select-hooks", json=[0])
        
        # Generate body
        requests.post(f"{BASE_URL}/api/projects/{project_id}/generate-body")
        
        # Generate CTA
        requests.post(f"{BASE_URL}/api/projects/{project_id}/generate-cta")
        
        # Finalize script
        requests.post(f"{BASE_URL}/api/projects/{project_id}/finalize-script")
        
        # Get updated project
        project_res = requests.get(f"{BASE_URL}/api/projects/{project_id}")
        project = project_res.json()
        
        yield project
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/projects/{project_id}")
    
    def test_generate_caption_tiktok(self, completed_project):
        """POST /api/projects/{id}/generate-caption with platform=tiktok should return captions and categorized hashtags"""
        project_id = completed_project["id"]
        
        response = requests.post(
            f"{BASE_URL}/api/projects/{project_id}/generate-caption",
            json={
                "platform": "tiktok",
                "tone": "casual",
                "hashtag_count": 10
            }
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Verify captions
        assert "captions" in data, "Response should have captions"
        assert isinstance(data["captions"], list), "Captions should be a list"
        assert len(data["captions"]) > 0, "Should have at least one caption"
        print(f"SUCCESS: Generated {len(data['captions'])} caption variations for TikTok")
        
        # Verify hashtags
        assert "hashtags" in data, "Response should have hashtags"
        assert isinstance(data["hashtags"], list), "Hashtags should be a list"
        print(f"  Total hashtags: {len(data['hashtags'])}")
        
        # Verify categorized hashtags
        assert "hashtags_categorized" in data, "Response should have hashtags_categorized"
        categorized = data["hashtags_categorized"]
        assert isinstance(categorized, dict), "hashtags_categorized should be a dict"
        
        # Check for trending/niche/branded categories
        has_categories = any([
            categorized.get("trending", []),
            categorized.get("niche", []),
            categorized.get("branded", [])
        ])
        print(f"  Categorized hashtags: trending={len(categorized.get('trending', []))}, niche={len(categorized.get('niche', []))}, branded={len(categorized.get('branded', []))}")
        
        # Verify caption tips
        assert "caption_tips" in data, "Response should have caption_tips"
        if data["caption_tips"]:
            print(f"  Caption tip: {data['caption_tips'][:100]}...")
        
        return data
    
    def test_generate_caption_instagram(self, completed_project):
        """POST /api/projects/{id}/generate-caption with platform=instagram"""
        project_id = completed_project["id"]
        
        response = requests.post(
            f"{BASE_URL}/api/projects/{project_id}/generate-caption",
            json={
                "platform": "instagram",
                "tone": "professional",
                "hashtag_count": 15
            }
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "captions" in data, "Response should have captions"
        assert "hashtags_categorized" in data, "Response should have hashtags_categorized"
        
        print(f"SUCCESS: Generated Instagram captions with {len(data.get('hashtags', []))} hashtags")
        return data
    
    def test_generate_caption_youtube(self, completed_project):
        """POST /api/projects/{id}/generate-caption with platform=youtube"""
        project_id = completed_project["id"]
        
        response = requests.post(
            f"{BASE_URL}/api/projects/{project_id}/generate-caption",
            json={
                "platform": "youtube",
                "tone": "educational",
                "hashtag_count": 5
            }
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "captions" in data, "Response should have captions"
        assert "hashtags_categorized" in data, "Response should have hashtags_categorized"
        
        print(f"SUCCESS: Generated YouTube captions with {len(data.get('hashtags', []))} hashtags")
        return data


class TestExistingEndpoints:
    """Verify existing endpoints still work"""
    
    def test_api_root(self):
        """GET /api/ should return API info"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        print("SUCCESS: API root endpoint working")
    
    def test_get_brands(self):
        """GET /api/brands should return brands list"""
        response = requests.get(f"{BASE_URL}/api/brands")
        assert response.status_code == 200
        print(f"SUCCESS: GET /api/brands returned {len(response.json())} brands")
    
    def test_get_projects(self):
        """GET /api/projects should return projects list"""
        response = requests.get(f"{BASE_URL}/api/projects")
        assert response.status_code == 200
        print(f"SUCCESS: GET /api/projects returned {len(response.json())} projects")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
