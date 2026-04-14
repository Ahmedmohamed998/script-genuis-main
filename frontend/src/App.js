import { useState, useEffect, useCallback } from "react";
import "@/App.css";
import axios from "axios";
import { Toaster, toast } from "sonner";

// Phosphor Icons
import {
  House,
  FolderOpen,
  Buildings,
  Gear,
  Plus,
  Play,
  MicrophoneStage,
  ChatCircle,
  Link as LinkIcon,
  Sparkle,
  ArrowRight,
  Check,
  X,
  Trash,
  PencilSimple,
  Copy,
  CaretRight,
  SpeakerHigh,
  Lightning,
  Hash,
  TextT,
  ArrowClockwise,
  PaperPlaneTilt,
  VideoCamera,
  Translate,
  Article,
  UserCircle,
  ChartBar,
  Shuffle,
  Star,
  Trophy,
  Brain,
  Target,
  Eye,
  TrendUp,
  Users,
  MagnifyingGlass,
  Calendar,
  Lightbulb,
  TiktokLogo,
  InstagramLogo,
  YoutubeLogo
} from "@phosphor-icons/react";

// Shadcn UI Components
import { Button } from "./components/ui/button";
import { Input } from "./components/ui/input";
import { Textarea } from "./components/ui/textarea";
import { ScrollArea } from "./components/ui/scroll-area";
import { Badge } from "./components/ui/badge";
import { Separator } from "./components/ui/separator";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "./components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
  DialogDescription,
} from "./components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./components/ui/tabs";
import { Slider } from "./components/ui/slider";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// ============================================================================
// PROFILE SELECTOR
// ============================================================================

const ProfileSelector = ({ profiles, currentProfile, onSelect, onSeedProfiles }) => {
  const handleValueChange = (id) => {
    if (!id) return;
    const profile = profiles.find(p => p.id === id);
    if (profile) onSelect(profile);
  };

  if (profiles.length === 0) {
    return (
      <Button
        data-testid="seed-profiles-btn"
        onClick={onSeedProfiles}
        className="bg-yellow-500 hover:bg-yellow-400 text-black font-semibold"
      >
        <Plus size={16} className="mr-1" />
        Create Profiles
      </Button>
    );
  }

  return (
    <Select 
      value={currentProfile?.id || undefined} 
      onValueChange={handleValueChange}
    >
      <SelectTrigger data-testid="profile-selector" className="w-52 bg-[#09090b] border-[#27272a] text-white">
        {currentProfile ? (
          <div className="flex items-center gap-2">
            <span>{currentProfile.language === "ar" ? "🇪🇬" : "🇺🇸"}</span>
            <span className="font-medium">{currentProfile.display_name}</span>
          </div>
        ) : (
          <span className="text-zinc-400">Select Profile</span>
        )}
      </SelectTrigger>
      <SelectContent className="bg-[#18181b] border-[#27272a]">
        {profiles.map((profile) => (
          <SelectItem key={profile.id} value={profile.id}>
            <div className="flex items-center gap-2">
              <span>{profile.language === "ar" ? "🇪🇬" : "🇺🇸"}</span>
              <span>{profile.display_name}</span>
            </div>
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
};

// ============================================================================
// SIDEBAR
// ============================================================================

const Sidebar = ({ activeTab, setActiveTab, currentProfile }) => {
  const navItems = [
    { id: "dashboard", icon: House, label: "Dashboard" },
    { id: "projects", icon: FolderOpen, label: "Projects" },
    { id: "brands", icon: Buildings, label: "Brands" },
    { id: "tracked", icon: Eye, label: "Style Tracker" },
    { id: "analytics", icon: ChartBar, label: "Analytics" },
  ];

  return (
    <div className="w-64 bg-[#18181b] border-r border-[#27272a] h-screen flex flex-col">
      <div className="p-6 border-b border-[#27272a]">
        <h1 className="text-2xl font-bold text-white font-['Outfit'] flex items-center gap-2">
          <Sparkle weight="fill" className="text-yellow-500" size={28} />
          Script Genius
        </h1>
        <p className="text-xs text-zinc-500 mt-1">AI Script Writing System</p>
        
        {currentProfile && (
          <div className="mt-3 p-2 rounded-lg bg-[#09090b] border border-[#27272a]">
            <div className="flex items-center gap-2">
              <span>{currentProfile.language === "ar" ? "🇪🇬" : "🇺🇸"}</span>
              <div>
                <p className="text-sm font-medium text-white">{currentProfile.display_name}</p>
                <p className="text-xs text-zinc-500">{currentProfile.language === "ar" ? "Arabic" : "English"} Scripts</p>
              </div>
            </div>
          </div>
        )}
      </div>
      
      <nav className="flex-1 p-4 space-y-2">
        {navItems.map((item) => (
          <button
            key={item.id}
            data-testid={`nav-${item.id}`}
            onClick={() => setActiveTab(item.id)}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${
              activeTab === item.id
                ? "bg-yellow-500/10 text-yellow-500 border border-yellow-500/20"
                : "text-zinc-400 hover:text-white hover:bg-white/5"
            }`}
          >
            <item.icon size={20} weight={activeTab === item.id ? "fill" : "regular"} />
            <span className="font-medium">{item.label}</span>
          </button>
        ))}
      </nav>
      

    </div>
  );
};

// ============================================================================
// VIDEO INPUT WITH PREVIEW & MANUAL TRANSCRIPT
// ============================================================================

const detectPlatform = (url) => {
  const lower = url.toLowerCase();
  if (lower.includes("tiktok.com")) return "tiktok";
  if (lower.includes("instagram.com") || lower.includes("instagr.am")) return "instagram";
  if (lower.includes("youtube.com") || lower.includes("youtu.be")) return "youtube";
  if (lower.includes("facebook.com") || lower.includes("fb.watch")) return "facebook";
  return "unknown";
};

const PlatformIcon = ({ platform, size = 16 }) => {
  switch (platform) {
    case "tiktok": return <TiktokLogo size={size} weight="fill" />;
    case "instagram": return <InstagramLogo size={size} weight="fill" />;
    case "youtube": return <YoutubeLogo size={size} weight="fill" />;
    default: return <VideoCamera size={size} />;
  }
};

const VideoInput = ({ onAddVideo, onAddManualTranscript, isLoading, profileLanguage }) => {
  const [url, setUrl] = useState("");
  const [language, setLanguage] = useState(profileLanguage || "ar");
  const [videoInfo, setVideoInfo] = useState(null);
  const [fetchingInfo, setFetchingInfo] = useState(false);
  const [showManual, setShowManual] = useState(false);
  const [manualText, setManualText] = useState("");

  useEffect(() => {
    setLanguage(profileLanguage || "ar");
  }, [profileLanguage]);

  const platform = url.trim() ? detectPlatform(url) : null;

  const fetchVideoInfo = async () => {
    if (!url.trim()) return;
    setFetchingInfo(true);
    try {
      const res = await axios.post(`${API}/video-info`, { video_url: url.trim() });
      setVideoInfo(res.data);
      if (res.data.error) {
        toast.error(res.data.message || "Could not fetch video info");
      }
    } catch (e) {
      setVideoInfo(null);
    } finally {
      setFetchingInfo(false);
    }
  };

  const handleSubmit = () => {
    if (url.trim()) {
      onAddVideo(url.trim(), language);
      setUrl("");
      setVideoInfo(null);
    }
  };

  const handleManualSubmit = () => {
    if (manualText.trim()) {
      onAddManualTranscript(manualText.trim(), language, url.trim() || "manual-input");
      setManualText("");
      setShowManual(false);
      setUrl("");
      setVideoInfo(null);
    }
  };

  const formatDuration = (seconds) => {
    if (!seconds) return "";
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}:${s.toString().padStart(2, '0')}`;
  };

  const formatNumber = (n) => {
    if (!n) return "0";
    if (n >= 1000000) return `${(n / 1000000).toFixed(1)}M`;
    if (n >= 1000) return `${(n / 1000).toFixed(1)}K`;
    return n.toString();
  };

  return (
    <div className="p-4 bg-[#09090b] border border-[#27272a] rounded-xl">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <VideoCamera size={18} className="text-yellow-500" />
          <span className="text-sm font-semibold text-white">Add Video</span>
        </div>
        <Button
          variant="ghost"
          size="sm"
          data-testid="toggle-manual-btn"
          onClick={() => setShowManual(!showManual)}
          className="text-xs text-zinc-500 hover:text-yellow-500"
        >
          <PencilSimple size={14} className="mr-1" />
          {showManual ? "URL Mode" : "Paste Script"}
        </Button>
      </div>
      
      {showManual ? (
        <div className="space-y-3">
          <Textarea
            data-testid="manual-transcript-input"
            value={manualText}
            onChange={(e) => setManualText(e.target.value)}
            placeholder="Paste the video script/transcript here..."
            className="bg-[#18181b] border-[#27272a] text-white placeholder:text-zinc-600 min-h-[100px] text-sm"
            rows={5}
          />
          <div className="flex gap-3">
            <Select value={language} onValueChange={setLanguage}>
              <SelectTrigger className="w-40 bg-[#18181b] border-[#27272a] text-white">
                <Translate size={16} className="mr-2" />
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-[#18181b] border-[#27272a]">
                <SelectItem value="ar">Arabic</SelectItem>
                <SelectItem value="en">English</SelectItem>
              </SelectContent>
            </Select>
            <Button
              data-testid="add-manual-transcript-btn"
              onClick={handleManualSubmit}
              disabled={!manualText.trim()}
              className="flex-1 bg-yellow-500 hover:bg-yellow-400 text-black font-semibold"
            >
              <Plus size={18} className="mr-2" />
              Add Script
            </Button>
          </div>
        </div>
      ) : (
        <div className="space-y-3">
          <div className="relative">
            <Input
              data-testid="video-url-input"
              value={url}
              onChange={(e) => { setUrl(e.target.value); setVideoInfo(null); }}
              onBlur={() => url.trim() && fetchVideoInfo()}
              placeholder="Paste TikTok, Instagram, or YouTube URL..."
              className="bg-[#18181b] border-[#27272a] text-white placeholder:text-zinc-600 pr-10"
            />
            {platform && (
              <div className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500">
                <PlatformIcon platform={platform} size={18} />
              </div>
            )}
          </div>
          
          {/* Video Info Preview */}
          {fetchingInfo && (
            <div className="flex items-center gap-2 p-2 bg-[#18181b] rounded-lg">
              <ArrowClockwise size={14} className="animate-spin text-yellow-500" />
              <span className="text-xs text-zinc-400">Fetching video info...</span>
            </div>
          )}
          
          {videoInfo && !videoInfo.error && (
            <div className="p-3 bg-[#18181b] border border-[#27272a] rounded-lg space-y-2" data-testid="video-preview">
              <p className="text-xs text-white font-medium line-clamp-2">{videoInfo.title}</p>
              <div className="flex items-center gap-3 text-xs text-zinc-500">
                {videoInfo.duration > 0 && (
                  <span>{formatDuration(videoInfo.duration)}</span>
                )}
                {videoInfo.view_count > 0 && (
                  <span><Eye size={12} className="inline mr-1" />{formatNumber(videoInfo.view_count)}</span>
                )}
                {videoInfo.uploader && (
                  <span className="truncate">@{videoInfo.uploader}</span>
                )}
              </div>
            </div>
          )}

          {videoInfo?.error && (
            <div className="p-3 bg-red-500/5 border border-red-500/20 rounded-lg">
              <p className="text-xs text-red-400">{videoInfo.message}</p>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowManual(true)}
                className="text-xs text-yellow-500 hover:text-yellow-400 mt-1 px-0"
              >
                Paste transcript manually instead
              </Button>
            </div>
          )}
          
          <div className="flex gap-3">
            <Select value={language} onValueChange={setLanguage}>
              <SelectTrigger data-testid="language-select" className="w-40 bg-[#18181b] border-[#27272a] text-white">
                <Translate size={16} className="mr-2" />
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-[#18181b] border-[#27272a]">
                <SelectItem value="ar">Arabic</SelectItem>
                <SelectItem value="en">English</SelectItem>
              </SelectContent>
            </Select>
            
            <Button
              data-testid="add-video-btn"
              onClick={handleSubmit}
              disabled={!url.trim() || isLoading}
              className="flex-1 bg-yellow-500 hover:bg-yellow-400 text-black font-semibold"
            >
              {isLoading ? (
                <ArrowClockwise size={18} className="animate-spin mr-2" />
              ) : (
                <Plus size={18} className="mr-2" />
              )}
              {isLoading ? "Transcribing..." : "Transcribe"}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};

// ============================================================================
// HOOK SELECTOR WITH A/B TESTING
// ============================================================================

const HookSelector = ({ hooks, selectedIndices, onSelect, onRegenerate, isLoading }) => {
  if (!hooks || hooks.length === 0) {
    return (
      <div className="text-center py-8 text-zinc-500">
        <Sparkle size={32} className="mx-auto mb-2 opacity-50" />
        <p>Generate hooks first</p>
      </div>
    );
  }

  const toggleHook = (index) => {
    const current = selectedIndices || [];
    if (current.includes(index)) {
      onSelect(current.filter(i => i !== index));
    } else {
      onSelect([...current, index]);
    }
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Lightning size={18} className="text-yellow-500" />
          <span className="text-sm font-semibold text-white">Choose Hooks</span>
          <Badge variant="secondary" className="text-xs">A/B Testing</Badge>
        </div>
        <Button
          data-testid="regenerate-hooks-btn"
          variant="ghost"
          size="sm"
          onClick={onRegenerate}
          disabled={isLoading}
          className="text-zinc-400 hover:text-white"
        >
          <ArrowClockwise size={16} className={isLoading ? "animate-spin" : ""} />
        </Button>
      </div>
      
      <p className="text-xs text-zinc-500 mb-3">Select multiple hooks for A/B testing</p>
      
      {hooks.map((hook, index) => {
        const isSelected = (selectedIndices || []).includes(index);
        const perf = hook.performance || {};
        
        return (
          <div
            key={index}
            data-testid={`hook-card-${index}`}
            onClick={() => toggleHook(index)}
            className={`p-4 rounded-lg border cursor-pointer transition-all ${
              isSelected
                ? "border-yellow-500 bg-yellow-500/5"
                : "border-[#27272a] bg-[#09090b] hover:border-[#3f3f46]"
            }`}
          >
            <div className="flex items-start justify-between gap-3">
              <p className="text-sm text-zinc-300 flex-1">{hook.text}</p>
              {isSelected && (
                <Check size={18} className="text-yellow-500 flex-shrink-0" />
              )}
            </div>
            <div className="flex items-center gap-2 mt-2">
              {hook.style && (
                <Badge variant="secondary" className="text-xs bg-[#27272a] text-zinc-400">
                  {hook.style}
                </Badge>
              )}
              {perf.engagement > 0 && (
                <Badge className="text-xs bg-green-500/10 text-green-400">
                  {(perf.engagement * 100).toFixed(1)}% engagement
                </Badge>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
};

// ============================================================================
// SCRIPT BLOCK
// ============================================================================

const ScriptBlock = ({ title, content, onEdit, icon: Icon, color = "yellow" }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editContent, setEditContent] = useState(content || "");

  useEffect(() => {
    setEditContent(content || "");
  }, [content]);

  const handleSave = () => {
    onEdit(editContent);
    setIsEditing(false);
  };

  return (
    <div className="p-4 bg-[#09090b] border border-[#27272a] rounded-xl">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Icon size={18} className={`text-${color}-500`} />
          <span className="text-sm font-semibold text-white">{title}</span>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setIsEditing(!isEditing)}
          className="text-zinc-400 hover:text-white"
        >
          {isEditing ? <X size={16} /> : <PencilSimple size={16} />}
        </Button>
      </div>
      
      {isEditing ? (
        <div className="space-y-2">
          <Textarea
            value={editContent}
            onChange={(e) => setEditContent(e.target.value)}
            className="min-h-32 bg-[#18181b] border-[#27272a] text-white"
          />
          <Button
            onClick={handleSave}
            size="sm"
            className="bg-yellow-500 hover:bg-yellow-400 text-black"
          >
            <Check size={16} className="mr-1" /> Save
          </Button>
        </div>
      ) : (
        <p className="text-sm text-zinc-300 whitespace-pre-wrap">
          {content || <span className="text-zinc-600 italic">Not generated yet...</span>}
        </p>
      )}
    </div>
  );
};

// ============================================================================
// CHAT INTERFACE
// ============================================================================

const ChatInterface = ({ projectId, profileId, onScriptUpdate }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [section, setSection] = useState("all");

  useEffect(() => {
    if (projectId) {
      loadChatHistory();
    }
  }, [projectId]);

  const loadChatHistory = async () => {
    try {
      const res = await axios.get(`${API}/projects/${projectId}/chat-history`);
      setMessages(res.data.messages || []);
    } catch (e) {
      console.error("Failed to load chat history", e);
    }
  };

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMsg = { role: "user", content: input, section };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsLoading(true);

    try {
      const res = await axios.post(`${API}/projects/${projectId}/chat`, {
        project_id: projectId,
        message: input,
        section: section === "all" ? null : section,
      });

      const assistantMsg = { role: "assistant", content: res.data.response, section: res.data.section };
      setMessages((prev) => [...prev, assistantMsg]);
      
      if (onScriptUpdate) onScriptUpdate();
    } catch (e) {
      toast.error("Failed to send message");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="h-full flex flex-col bg-[#18181b] rounded-xl border border-[#27272a]">
      <div className="p-4 border-b border-[#27272a]">
        <div className="flex items-center gap-2">
          <ChatCircle size={18} className="text-yellow-500" />
          <span className="font-semibold text-white">Edit with AI</span>
        </div>
        <Select value={section} onValueChange={setSection}>
          <SelectTrigger className="mt-2 bg-[#09090b] border-[#27272a] text-sm">
            <SelectValue placeholder="Select section" />
          </SelectTrigger>
          <SelectContent className="bg-[#18181b] border-[#27272a]">
            <SelectItem value="all">Entire Script</SelectItem>
            <SelectItem value="hook">Hook</SelectItem>
            <SelectItem value="body">Body</SelectItem>
            <SelectItem value="cta">CTA</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <ScrollArea className="flex-1 p-4">
        {messages.length === 0 ? (
          <div className="text-center py-8 text-zinc-500">
            <ChatCircle size={32} className="mx-auto mb-2 opacity-50" />
            <p className="text-sm">Start chatting to edit your script</p>
          </div>
        ) : (
          <div className="space-y-4">
            {messages.map((msg, i) => (
              <div
                key={i}
                className={`max-w-[85%] p-3 rounded-lg ${
                  msg.role === "user"
                    ? "ml-auto bg-[#27272a] rounded-br-sm"
                    : "bg-yellow-500/10 border border-yellow-500/20 rounded-bl-sm"
                }`}
              >
                <p className="text-sm text-zinc-300 whitespace-pre-wrap">{msg.content}</p>
              </div>
            ))}
            {isLoading && (
              <div className="flex items-center gap-2 text-zinc-500">
                <ArrowClockwise size={16} className="animate-spin" />
                <span className="text-sm">Thinking...</span>
              </div>
            )}
          </div>
        )}
      </ScrollArea>

      <div className="p-4 border-t border-[#27272a]">
        <div className="flex gap-2">
          <Input
            data-testid="chat-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === "Enter" && sendMessage()}
            placeholder="Type your edit request..."
            className="bg-[#09090b] border-[#27272a] text-white"
          />
          <Button
            data-testid="send-chat-btn"
            onClick={sendMessage}
            disabled={!input.trim() || isLoading}
            className="bg-yellow-500 hover:bg-yellow-400 text-black"
          >
            <PaperPlaneTilt size={18} />
          </Button>
        </div>
      </div>
    </div>
  );
};

// ============================================================================
// CAPTION & HASHTAG INTELLIGENCE PANEL
// ============================================================================

const CaptionPanel = ({ captions, hashtags, hashtagsCategorized, captionTips, activePlatform, onGenerate, isLoading }) => {
  const [selectedCaption, setSelectedCaption] = useState(0);
  const [platform, setPlatform] = useState(activePlatform || "tiktok");
  const [tone, setTone] = useState("auto");
  const [showAllHashtags, setShowAllHashtags] = useState(false);
  
  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    toast.success("Copied!");
  };

  const copyAllHashtags = () => {
    const allTags = hashtags?.join(" ") || "";
    navigator.clipboard.writeText(allTags);
    toast.success("All hashtags copied!");
  };

  const copyCaptionWithHashtags = () => {
    if (!captions?.length) return;
    const text = `${captions[selectedCaption]}\n\n${hashtags?.join(" ") || ""}`;
    navigator.clipboard.writeText(text);
    toast.success("Caption + hashtags copied!");
  };

  const handleGenerate = () => {
    onGenerate(platform, tone);
  };

  const platformOptions = [
    { id: "tiktok", label: "TikTok", icon: TiktokLogo },
    { id: "instagram", label: "Instagram", icon: InstagramLogo },
    { id: "youtube", label: "YouTube", icon: YoutubeLogo },
  ];

  const toneOptions = [
    { id: "auto", label: "Auto" },
    { id: "casual", label: "Casual" },
    { id: "professional", label: "Professional" },
    { id: "funny", label: "Funny" },
    { id: "educational", label: "Educational" },
  ];

  const categorized = hashtagsCategorized || {};
  const hasCategories = Object.keys(categorized).some(k => categorized[k]?.length > 0);

  return (
    <div className="p-4 bg-[#09090b] border border-[#27272a] rounded-xl" data-testid="caption-panel">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <TextT size={18} className="text-yellow-500" />
          <span className="text-sm font-semibold text-white">Caption Intelligence</span>
        </div>
        <Button
          data-testid="generate-caption-btn"
          variant="ghost"
          size="sm"
          onClick={handleGenerate}
          disabled={isLoading}
          className="text-zinc-400 hover:text-white"
        >
          {isLoading ? <ArrowClockwise size={16} className="animate-spin" /> : <Sparkle size={16} />}
        </Button>
      </div>

      {/* Platform & Tone Selectors */}
      <div className="flex gap-2 mb-4">
        <div className="flex gap-1 p-1 bg-[#18181b] rounded-lg flex-1">
          {platformOptions.map((p) => (
            <button
              key={p.id}
              data-testid={`platform-${p.id}`}
              onClick={() => setPlatform(p.id)}
              className={`flex-1 flex items-center justify-center gap-1.5 px-2 py-1.5 rounded-md text-xs font-medium transition-all ${
                platform === p.id 
                  ? "bg-yellow-500 text-black" 
                  : "text-zinc-500 hover:text-zinc-300"
              }`}
            >
              <p.icon size={14} weight={platform === p.id ? "fill" : "regular"} />
              {p.label}
            </button>
          ))}
        </div>
      </div>

      <div className="mb-4">
        <Select value={tone} onValueChange={setTone}>
          <SelectTrigger className="bg-[#18181b] border-[#27272a] text-white text-xs h-8">
            <SelectValue placeholder="Tone" />
          </SelectTrigger>
          <SelectContent className="bg-[#18181b] border-[#27272a]">
            {toneOptions.map(t => (
              <SelectItem key={t.id} value={t.id}>{t.label}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {captions && captions.length > 0 ? (
        <div className="space-y-4">
          {/* Caption Variations */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <div className="flex gap-1.5">
                {captions.map((_, i) => (
                  <Button
                    key={i}
                    size="sm"
                    variant={selectedCaption === i ? "default" : "secondary"}
                    onClick={() => setSelectedCaption(i)}
                    className={`h-7 text-xs ${selectedCaption === i ? "bg-yellow-500 text-black" : ""}`}
                  >
                    V{i + 1}
                  </Button>
                ))}
              </div>
              <Button
                variant="ghost"
                size="sm"
                data-testid="copy-caption-hashtags-btn"
                onClick={copyCaptionWithHashtags}
                className="text-xs text-zinc-500 hover:text-yellow-500 h-7"
              >
                <Copy size={12} className="mr-1" />
                Copy All
              </Button>
            </div>
            
            <div className="relative">
              <p className="text-sm text-zinc-300 p-3 bg-[#18181b] rounded-lg pr-10 whitespace-pre-wrap">
                {captions[selectedCaption]}
              </p>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => copyToClipboard(captions[selectedCaption])}
                className="absolute top-2 right-2 text-zinc-500 hover:text-white h-6 w-6 p-0"
              >
                <Copy size={12} />
              </Button>
              <p className="text-xs text-zinc-600 mt-1 text-right">
                {captions[selectedCaption]?.length || 0} chars
              </p>
            </div>
          </div>
          
          {/* Hashtags */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-medium text-zinc-400">
                <Hash size={12} className="inline mr-1" />
                Hashtags ({hashtags?.length || 0})
              </span>
              <Button
                variant="ghost"
                size="sm"
                data-testid="copy-all-hashtags-btn"
                onClick={copyAllHashtags}
                className="text-xs text-zinc-500 hover:text-yellow-500 h-6"
              >
                <Copy size={12} className="mr-1" />
                Copy All
              </Button>
            </div>
            
            {hasCategories ? (
              <div className="space-y-2">
                {categorized.trending?.length > 0 && (
                  <div>
                    <p className="text-xs text-yellow-500/70 mb-1 flex items-center gap-1">
                      <TrendUp size={10} /> Trending
                    </p>
                    <div className="flex flex-wrap gap-1.5">
                      {categorized.trending.map((tag, i) => (
                        <Badge
                          key={`t-${i}`}
                          variant="secondary"
                          className="bg-yellow-500/5 border border-yellow-500/20 text-yellow-500/80 cursor-pointer hover:bg-yellow-500/10 text-xs"
                          onClick={() => copyToClipboard(tag)}
                        >
                          {tag}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
                {categorized.niche?.length > 0 && (
                  <div>
                    <p className="text-xs text-blue-400/70 mb-1 flex items-center gap-1">
                      <Target size={10} /> Niche
                    </p>
                    <div className="flex flex-wrap gap-1.5">
                      {categorized.niche.map((tag, i) => (
                        <Badge
                          key={`n-${i}`}
                          variant="secondary"
                          className="bg-blue-500/5 border border-blue-500/20 text-blue-400/80 cursor-pointer hover:bg-blue-500/10 text-xs"
                          onClick={() => copyToClipboard(tag)}
                        >
                          {tag}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
                {categorized.branded?.length > 0 && (
                  <div>
                    <p className="text-xs text-purple-400/70 mb-1 flex items-center gap-1">
                      <Star size={10} /> Branded
                    </p>
                    <div className="flex flex-wrap gap-1.5">
                      {categorized.branded.map((tag, i) => (
                        <Badge
                          key={`b-${i}`}
                          variant="secondary"
                          className="bg-purple-500/5 border border-purple-500/20 text-purple-400/80 cursor-pointer hover:bg-purple-500/10 text-xs"
                          onClick={() => copyToClipboard(tag)}
                        >
                          {tag}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="flex flex-wrap gap-1.5">
                {hashtags?.map((tag, i) => (
                  <Badge
                    key={i}
                    variant="secondary"
                    className="bg-[#18181b] text-zinc-400 cursor-pointer hover:text-yellow-500 text-xs"
                    onClick={() => copyToClipboard(tag)}
                  >
                    {tag}
                  </Badge>
                ))}
              </div>
            )}
          </div>

          {/* Caption Tips */}
          {captionTips && (
            <div className="p-2 bg-yellow-500/5 border border-yellow-500/10 rounded-lg">
              <p className="text-xs text-yellow-500/70 flex items-start gap-1.5">
                <Lightbulb size={12} className="mt-0.5 flex-shrink-0" />
                {captionTips}
              </p>
            </div>
          )}
        </div>
      ) : (
        <div className="text-center py-6">
          <TextT size={28} className="mx-auto mb-2 text-zinc-700" />
          <p className="text-sm text-zinc-500">Generate captions after finalizing your script</p>
          <p className="text-xs text-zinc-600 mt-1">AI will create platform-optimized captions with trending hashtags</p>
        </div>
      )}
    </div>
  );
};

// ============================================================================
// VOICEOVER PANEL
// ============================================================================

const VoiceoverPanel = ({ projectId, voiceoverUrl, onGenerate, isLoading }) => {
  const [isPlaying, setIsPlaying] = useState(false);

  return (
    <div className="p-4 bg-[#09090b] border border-[#27272a] rounded-xl">
      <div className="flex items-center gap-2 mb-4">
        <MicrophoneStage size={18} className="text-yellow-500" />
        <span className="text-sm font-semibold text-white">Voice Over</span>
      </div>

      {voiceoverUrl ? (
        <div className="space-y-3">
          <div className="flex items-center justify-center gap-1 h-16 bg-[#18181b] rounded-lg">
            {[...Array(12)].map((_, i) => (
              <div
                key={i}
                className={`w-1 bg-yellow-500 rounded-full ${isPlaying ? "animate-waveform" : ""}`}
                style={{
                  height: `${Math.random() * 60 + 20}%`,
                  animationDelay: `${i * 0.1}s`,
                }}
              />
            ))}
          </div>
          <Button
            data-testid="play-voiceover-btn"
            onClick={() => setIsPlaying(!isPlaying)}
            variant="secondary"
            className="w-full"
          >
            {isPlaying ? <SpeakerHigh size={18} /> : <Play size={18} />}
            <span className="ml-2">{isPlaying ? "Playing..." : "Play"}</span>
          </Button>
        </div>
      ) : (
        <Button
          data-testid="generate-voiceover-btn"
          onClick={onGenerate}
          disabled={isLoading}
          className="w-full bg-yellow-500 hover:bg-yellow-400 text-black"
        >
          {isLoading ? (
            <ArrowClockwise size={18} className="animate-spin mr-2" />
          ) : (
            <MicrophoneStage size={18} className="mr-2" />
          )}
          {isLoading ? "Generating..." : "Generate Voice Over"}
        </Button>
      )}
      
      <p className="text-xs text-zinc-500 mt-3 text-center">
        Powered by ElevenLabs (Adam Voice)
      </p>
    </div>
  );
};

// ============================================================================
// DASHBOARD
// ============================================================================

const Dashboard = ({ projects, brands, currentProfile, onNewProject }) => {
  const profileProjects = projects.filter(p => p.profile_id === currentProfile?.id);
  const profileBrands = brands.filter(b => b.profile_id === currentProfile?.id);
  const recentProjects = profileProjects.slice(0, 5);
  
  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white font-['Outfit']">Dashboard</h1>
          <p className="text-zinc-500 mt-1">
            {currentProfile ? `Welcome, ${currentProfile.display_name}!` : "Select a profile to get started"}
          </p>
        </div>
        <Button
          data-testid="new-project-btn"
          onClick={onNewProject}
          disabled={!currentProfile}
          className="bg-yellow-500 hover:bg-yellow-400 text-black font-semibold"
        >
          <Plus size={18} className="mr-2" />
          New Project
        </Button>
      </div>

      {currentProfile && (
        <div className="mb-8 p-4 bg-gradient-to-r from-yellow-500/10 to-transparent border border-yellow-500/20 rounded-xl">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-yellow-500/20 rounded-full">
              <Brain size={24} className="text-yellow-500" />
            </div>
            <div>
              <h3 className="font-semibold text-white">Learning Mode Active</h3>
              <p className="text-sm text-zinc-400">
                {currentProfile.total_scripts || 0} scripts analyzed • 
                {currentProfile.language === "ar" ? " Arabic Egyptian" : " English"} style
              </p>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-[#18181b] border border-[#27272a] rounded-xl p-6">
          <div className="flex items-center justify-between">
            <span className="text-zinc-400">Total Projects</span>
            <FolderOpen size={24} className="text-yellow-500" />
          </div>
          <p className="text-3xl font-bold text-white mt-2">{profileProjects.length}</p>
        </div>
        
        <div className="bg-[#18181b] border border-[#27272a] rounded-xl p-6">
          <div className="flex items-center justify-between">
            <span className="text-zinc-400">Active Brands</span>
            <Buildings size={24} className="text-yellow-500" />
          </div>
          <p className="text-3xl font-bold text-white mt-2">{profileBrands.length}</p>
        </div>
        
        <div className="bg-[#18181b] border border-[#27272a] rounded-xl p-6">
          <div className="flex items-center justify-between">
            <span className="text-zinc-400">Completed</span>
            <Trophy size={24} className="text-yellow-500" />
          </div>
          <p className="text-3xl font-bold text-white mt-2">
            {profileProjects.filter(p => p.status === "completed").length}
          </p>
        </div>
      </div>

      <div className="bg-[#18181b] border border-[#27272a] rounded-xl p-6">
        <h2 className="text-xl font-semibold text-white mb-4">Recent Projects</h2>
        {recentProjects.length > 0 ? (
          <div className="space-y-3">
            {recentProjects.map((project) => (
              <div
                key={project.id}
                className="flex items-center justify-between p-4 bg-[#09090b] border border-[#27272a] rounded-lg hover:border-[#3f3f46] transition-all"
              >
                <div>
                  <p className="font-medium text-white">{project.name}</p>
                  <p className="text-sm text-zinc-500">
                    {new Date(project.created_at).toLocaleDateString()}
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  {project.is_ad && (
                    <Badge className="bg-yellow-500/10 text-yellow-500">AD</Badge>
                  )}
                  <Badge className={project.status === "completed" ? "bg-green-500/10 text-green-400" : "bg-zinc-500/10 text-zinc-400"}>
                    {project.status}
                  </Badge>
                  <CaretRight size={16} className="text-zinc-500" />
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-zinc-500 text-center py-8">No projects yet. Create your first one!</p>
        )}
      </div>
    </div>
  );
};

// ============================================================================
// PROJECTS LIST
// ============================================================================

const ProjectsList = ({ projects, currentProfile, onSelect, onDelete, onNew }) => {
  const profileProjects = projects.filter(p => p.profile_id === currentProfile?.id);
  
  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white font-['Outfit']">Projects</h1>
          <p className="text-zinc-500 mt-1">Manage your script projects</p>
        </div>
        <Button
          data-testid="new-project-btn-list"
          onClick={onNew}
          disabled={!currentProfile}
          className="bg-yellow-500 hover:bg-yellow-400 text-black font-semibold"
        >
          <Plus size={18} className="mr-2" />
          New Project
        </Button>
      </div>

      {profileProjects.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {profileProjects.map((project) => (
            <div
              key={project.id}
              data-testid={`project-card-${project.id}`}
              className="bg-[#18181b] border border-[#27272a] rounded-xl p-6 cursor-pointer hover:border-[#3f3f46] transition-all"
              onClick={() => onSelect(project)}
            >
              <div className="flex items-start justify-between mb-3">
                <h3 className="font-semibold text-white">{project.name}</h3>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation();
                    onDelete(project.id);
                  }}
                  className="text-zinc-500 hover:text-red-500"
                >
                  <Trash size={16} />
                </Button>
              </div>
              
              <div className="flex items-center gap-2 mb-3">
                <Badge variant="secondary" className="text-xs">
                  {project.video_urls?.length || 0} videos
                </Badge>
                {project.is_ad && (
                  <Badge className="text-xs bg-yellow-500/10 text-yellow-500">AD</Badge>
                )}
              </div>
              
              <p className="text-sm text-zinc-500">
                {new Date(project.created_at).toLocaleDateString()}
              </p>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-16">
          <FolderOpen size={48} className="mx-auto text-zinc-600 mb-4" />
          <p className="text-zinc-500">No projects yet</p>
          <Button
            onClick={onNew}
            disabled={!currentProfile}
            className="mt-4 bg-yellow-500 hover:bg-yellow-400 text-black"
          >
            Create Your First Project
          </Button>
        </div>
      )}
    </div>
  );
};

// ============================================================================
// BRANDS PAGE
// ============================================================================

const BrandsPage = ({ brands, currentProfile, onSave, onDelete }) => {
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingBrand, setEditingBrand] = useState(null);
  const [formData, setFormData] = useState({
    name: "",
    description: "",
    tone: "",
    personality: "",
    favorite_words: "",
    forbidden_words: "",
    cta_templates: "",
    hook_templates: "",
    caption_style: "",
    emoji_style: "moderate",
    hashtags: "",
  });

  const profileBrands = brands.filter(b => b.profile_id === currentProfile?.id);

  const handleSubmit = async () => {
    const data = {
      ...formData,
      profile_id: currentProfile.id,
      favorite_words: formData.favorite_words.split(",").map(w => w.trim()).filter(Boolean),
      forbidden_words: formData.forbidden_words.split(",").map(w => w.trim()).filter(Boolean),
      cta_templates: formData.cta_templates.split("\n").map(t => t.trim()).filter(Boolean),
      hook_templates: formData.hook_templates.split("\n").map(t => t.trim()).filter(Boolean),
      hashtags: formData.hashtags.split(",").map(h => h.trim()).filter(Boolean),
    };
    await onSave(data, editingBrand?.id);
    setIsDialogOpen(false);
    setEditingBrand(null);
    setFormData({
      name: "", description: "", tone: "", personality: "",
      favorite_words: "", forbidden_words: "", cta_templates: "",
      hook_templates: "", caption_style: "", emoji_style: "moderate", hashtags: ""
    });
  };

  const openEdit = (brand) => {
    setEditingBrand(brand);
    setFormData({
      name: brand.name,
      description: brand.description || "",
      tone: brand.tone || "",
      personality: brand.personality || "",
      favorite_words: brand.favorite_words?.join(", ") || "",
      forbidden_words: brand.forbidden_words?.join(", ") || "",
      cta_templates: brand.cta_templates?.join("\n") || "",
      hook_templates: brand.hook_templates?.join("\n") || "",
      caption_style: brand.caption_style || "",
      emoji_style: brand.emoji_style || "moderate",
      hashtags: brand.hashtags?.join(", ") || "",
    });
    setIsDialogOpen(true);
  };

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white font-['Outfit']">Brands</h1>
          <p className="text-zinc-500 mt-1">Manage brand voice DNA and styles</p>
        </div>
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button
              data-testid="new-brand-btn"
              disabled={!currentProfile}
              className="bg-yellow-500 hover:bg-yellow-400 text-black font-semibold"
              onClick={() => {
                setEditingBrand(null);
                setFormData({
                  name: "", description: "", tone: "", personality: "",
                  favorite_words: "", forbidden_words: "", cta_templates: "",
                  hook_templates: "", caption_style: "", emoji_style: "moderate", hashtags: ""
                });
              }}
            >
              <Plus size={18} className="mr-2" />
              New Brand
            </Button>
          </DialogTrigger>
          <DialogContent className="bg-[#18181b] border-[#27272a] text-white max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="font-['Outfit']">
                {editingBrand ? "Edit Brand" : "New Brand"}
              </DialogTitle>
              <DialogDescription className="text-zinc-500">
                Define the brand's voice DNA for consistent scripts
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 mt-4">
              <div className="grid grid-cols-2 gap-4">
                <Input
                  data-testid="brand-name-input"
                  placeholder="Brand Name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="bg-[#09090b] border-[#27272a]"
                />
                <Select value={formData.tone} onValueChange={(v) => setFormData({ ...formData, tone: v })}>
                  <SelectTrigger className="bg-[#09090b] border-[#27272a]">
                    <SelectValue placeholder="Brand Tone" />
                  </SelectTrigger>
                  <SelectContent className="bg-[#18181b] border-[#27272a]">
                    <SelectItem value="professional">Professional</SelectItem>
                    <SelectItem value="casual">Casual</SelectItem>
                    <SelectItem value="friendly">Friendly</SelectItem>
                    <SelectItem value="urgent">Urgent</SelectItem>
                    <SelectItem value="playful">Playful</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <Textarea
                placeholder="Brand Description"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="bg-[#09090b] border-[#27272a]"
              />
              
              <Textarea
                placeholder="Brand Personality (describe how the brand talks)"
                value={formData.personality}
                onChange={(e) => setFormData({ ...formData, personality: e.target.value })}
                className="bg-[#09090b] border-[#27272a]"
              />
              
              <div className="grid grid-cols-2 gap-4">
                <Input
                  placeholder="Favorite Words (comma separated)"
                  value={formData.favorite_words}
                  onChange={(e) => setFormData({ ...formData, favorite_words: e.target.value })}
                  className="bg-[#09090b] border-[#27272a]"
                />
                <Input
                  placeholder="Forbidden Words (comma separated)"
                  value={formData.forbidden_words}
                  onChange={(e) => setFormData({ ...formData, forbidden_words: e.target.value })}
                  className="bg-[#09090b] border-[#27272a]"
                />
              </div>
              
              <Textarea
                placeholder="Hook Templates (one per line)"
                value={formData.hook_templates}
                onChange={(e) => setFormData({ ...formData, hook_templates: e.target.value })}
                className="bg-[#09090b] border-[#27272a] min-h-20"
              />
              
              <Textarea
                placeholder="CTA Templates (one per line)"
                value={formData.cta_templates}
                onChange={(e) => setFormData({ ...formData, cta_templates: e.target.value })}
                className="bg-[#09090b] border-[#27272a] min-h-20"
              />
              
              <div className="grid grid-cols-2 gap-4">
                <Input
                  placeholder="Caption Style"
                  value={formData.caption_style}
                  onChange={(e) => setFormData({ ...formData, caption_style: e.target.value })}
                  className="bg-[#09090b] border-[#27272a]"
                />
                <Select value={formData.emoji_style} onValueChange={(v) => setFormData({ ...formData, emoji_style: v })}>
                  <SelectTrigger className="bg-[#09090b] border-[#27272a]">
                    <SelectValue placeholder="Emoji Usage" />
                  </SelectTrigger>
                  <SelectContent className="bg-[#18181b] border-[#27272a]">
                    <SelectItem value="none">No Emojis</SelectItem>
                    <SelectItem value="minimal">Minimal</SelectItem>
                    <SelectItem value="moderate">Moderate</SelectItem>
                    <SelectItem value="heavy">Heavy</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <Input
                placeholder="Brand Hashtags (comma separated)"
                value={formData.hashtags}
                onChange={(e) => setFormData({ ...formData, hashtags: e.target.value })}
                className="bg-[#09090b] border-[#27272a]"
              />
            </div>
            <DialogFooter className="mt-6">
              <Button variant="secondary" onClick={() => setIsDialogOpen(false)}>
                Cancel
              </Button>
              <Button
                data-testid="save-brand-btn"
                onClick={handleSubmit}
                className="bg-yellow-500 hover:bg-yellow-400 text-black"
              >
                {editingBrand ? "Update" : "Create"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {profileBrands.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {profileBrands.map((brand) => (
            <div
              key={brand.id}
              data-testid={`brand-card-${brand.id}`}
              className="bg-[#18181b] border border-[#27272a] rounded-xl p-6"
            >
              <div className="flex items-start justify-between mb-3">
                <div>
                  <h3 className="font-semibold text-white">{brand.name}</h3>
                  {brand.tone && (
                    <Badge variant="secondary" className="mt-1 text-xs">
                      {brand.tone}
                    </Badge>
                  )}
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => openEdit(brand)}
                    className="text-zinc-500 hover:text-white"
                  >
                    <PencilSimple size={16} />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onDelete(brand.id)}
                    className="text-zinc-500 hover:text-red-500"
                  >
                    <Trash size={16} />
                  </Button>
                </div>
              </div>
              
              {brand.description && (
                <p className="text-sm text-zinc-400 mb-3">{brand.description}</p>
              )}
              
              {brand.hashtags?.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {brand.hashtags.slice(0, 3).map((tag, i) => (
                    <Badge key={i} variant="secondary" className="text-xs">
                      #{tag.replace("#", "")}
                    </Badge>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-16">
          <Buildings size={48} className="mx-auto text-zinc-600 mb-4" />
          <p className="text-zinc-500">No brands yet</p>
        </div>
      )}
    </div>
  );
};

// ============================================================================
// ANALYTICS PAGE
// ============================================================================

const AnalyticsPage = ({ currentProfile }) => {
  const [analytics, setAnalytics] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (currentProfile) {
      loadAnalytics();
    }
  }, [currentProfile]);

  const loadAnalytics = async () => {
    setIsLoading(true);
    try {
      const res = await axios.get(`${API}/profiles/${currentProfile.id}/analytics`);
      setAnalytics(res.data);
    } catch (e) {
      console.error("Failed to load analytics", e);
    } finally {
      setIsLoading(false);
    }
  };

  if (!currentProfile) {
    return (
      <div className="p-8 text-center">
        <p className="text-zinc-500">Select a profile to view analytics</p>
      </div>
    );
  }

  if (isLoading || !analytics) {
    return (
      <div className="p-8 text-center">
        <ArrowClockwise size={32} className="animate-spin mx-auto text-yellow-500" />
      </div>
    );
  }

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white font-['Outfit']">Analytics</h1>
        <p className="text-zinc-500 mt-1">Learning insights for {currentProfile.display_name}</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-[#18181b] border border-[#27272a] rounded-xl p-6">
          <div className="flex items-center justify-between">
            <span className="text-zinc-400">Total Scripts</span>
            <Article size={24} className="text-yellow-500" />
          </div>
          <p className="text-3xl font-bold text-white mt-2">{analytics.stats.total_projects}</p>
        </div>
        
        <div className="bg-[#18181b] border border-[#27272a] rounded-xl p-6">
          <div className="flex items-center justify-between">
            <span className="text-zinc-400">Completed</span>
            <Check size={24} className="text-green-500" />
          </div>
          <p className="text-3xl font-bold text-white mt-2">{analytics.stats.completed_projects}</p>
        </div>
        
        <div className="bg-[#18181b] border border-[#27272a] rounded-xl p-6">
          <div className="flex items-center justify-between">
            <span className="text-zinc-400">Ad Scripts</span>
            <Target size={24} className="text-yellow-500" />
          </div>
          <p className="text-3xl font-bold text-white mt-2">{analytics.stats.ad_projects}</p>
        </div>
        
        <div className="bg-[#18181b] border border-[#27272a] rounded-xl p-6">
          <div className="flex items-center justify-between">
            <span className="text-zinc-400">Organic</span>
            <Sparkle size={24} className="text-blue-500" />
          </div>
          <p className="text-3xl font-bold text-white mt-2">{analytics.stats.organic_projects}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-[#18181b] border border-[#27272a] rounded-xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <Lightning size={20} className="text-yellow-500" />
            Hook Style Preferences
          </h3>
          {Object.entries(analytics.hook_preferences || {}).length > 0 ? (
            <div className="space-y-3">
              {Object.entries(analytics.hook_preferences)
                .sort(([,a], [,b]) => b - a)
                .slice(0, 5)
                .map(([style, count]) => (
                  <div key={style} className="flex items-center justify-between">
                    <span className="text-zinc-300 capitalize">{style}</span>
                    <div className="flex items-center gap-2">
                      <div className="w-32 h-2 bg-[#27272a] rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-yellow-500 rounded-full"
                          style={{ width: `${Math.min(count * 10, 100)}%` }}
                        />
                      </div>
                      <span className="text-sm text-zinc-500 w-8">{count}</span>
                    </div>
                  </div>
                ))}
            </div>
          ) : (
            <p className="text-zinc-500">No data yet. Create more scripts!</p>
          )}
        </div>

        <div className="bg-[#18181b] border border-[#27272a] rounded-xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <Trophy size={20} className="text-yellow-500" />
            Top Performing Hooks
          </h3>
          {analytics.successful_hooks?.length > 0 ? (
            <div className="space-y-3">
              {analytics.successful_hooks.slice(0, 5).map((hook, i) => (
                <div key={i} className="p-3 bg-[#09090b] border border-[#27272a] rounded-lg">
                  <p className="text-sm text-zinc-300">{hook}</p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-zinc-500">No successful hooks recorded yet</p>
          )}
        </div>
      </div>
    </div>
  );
};

// ============================================================================
// TRACKED ACCOUNTS PAGE - Style Tracker
// ============================================================================

const TrackedAccountsPage = ({ currentProfile }) => {
  const [accounts, setAccounts] = useState([]);
  const [styleInsights, setStyleInsights] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [analyzingAccount, setAnalyzingAccount] = useState(null);
  const [selectedAccount, setSelectedAccount] = useState(null);
  const [analyzedVideos, setAnalyzedVideos] = useState([]);
  
  const [formData, setFormData] = useState({
    platform: "instagram",
    account_url: "",
    account_name: "",
    account_handle: "",
    check_frequency: "weekly",
    min_engagement_threshold: 1000,
  });

  useEffect(() => {
    if (currentProfile) {
      loadAccounts();
      loadInsights();
    }
  }, [currentProfile]);

  const loadAccounts = async () => {
    try {
      const res = await axios.get(`${API}/tracked-accounts?profile_id=${currentProfile.id}`);
      setAccounts(res.data);
    } catch (e) {
      console.error("Failed to load accounts", e);
    }
  };

  const loadInsights = async () => {
    try {
      const res = await axios.get(`${API}/profiles/${currentProfile.id}/style-insights`);
      setStyleInsights(res.data);
    } catch (e) {
      console.error("Failed to load insights", e);
    }
  };

  const loadAnalyzedVideos = async (accountId) => {
    try {
      const res = await axios.get(`${API}/tracked-accounts/${accountId}/videos`);
      setAnalyzedVideos(res.data.videos || []);
    } catch (e) {
      console.error("Failed to load videos", e);
    }
  };

  const handleSubmit = async () => {
    try {
      await axios.post(`${API}/tracked-accounts`, {
        ...formData,
        profile_id: currentProfile.id,
      });
      setIsDialogOpen(false);
      setFormData({
        platform: "tiktok",
        account_url: "",
        account_name: "",
        account_handle: "",
        check_frequency: "weekly",
        min_engagement_threshold: 1000,
      });
      loadAccounts();
      toast.success("Account added!");
    } catch (e) {
      toast.error("Failed to add account");
    }
  };

  const analyzeAccount = async (account) => {
    setAnalyzingAccount(account.id);
    try {
      const res = await axios.post(`${API}/tracked-accounts/${account.id}/analyze?video_limit=5`);
      toast.success(`Analyzed ${res.data.videos_analyzed} videos!`);
      loadAccounts();
      loadInsights();
    } catch (e) {
      toast.error("Analysis failed - check account URL");
    } finally {
      setAnalyzingAccount(null);
    }
  };

  const analyzeAllAccounts = async () => {
    setIsLoading(true);
    try {
      const res = await axios.post(`${API}/profiles/${currentProfile.id}/analyze-all-accounts?video_limit=3`);
      toast.success(`Analyzed ${res.data.results.length} accounts!`);
      loadAccounts();
      loadInsights();
    } catch (e) {
      toast.error("Analysis failed");
    } finally {
      setIsLoading(false);
    }
  };

  const deleteAccount = async (id) => {
    try {
      await axios.delete(`${API}/tracked-accounts/${id}`);
      setAccounts(accounts.filter(a => a.id !== id));
      toast.success("Account removed");
    } catch (e) {
      toast.error("Failed to delete");
    }
  };

  const getPlatformIcon = (platform) => {
    switch (platform) {
      case "tiktok": return <VideoCamera size={20} className="text-pink-500" />;
      case "instagram": return <VideoCamera size={20} className="text-purple-500" />;
      case "youtube": return <VideoCamera size={20} className="text-red-500" />;
      default: return <VideoCamera size={20} className="text-zinc-500" />;
    }
  };

  if (!currentProfile) {
    return (
      <div className="p-8 text-center">
        <p className="text-zinc-500">Select a profile to track accounts</p>
      </div>
    );
  }

  // Show account details view
  if (selectedAccount) {
    return (
      <div className="p-8">
        <div className="flex items-center gap-4 mb-8">
          <Button
            variant="ghost"
            onClick={() => {
              setSelectedAccount(null);
              setAnalyzedVideos([]);
            }}
            className="text-zinc-400 hover:text-white"
          >
            <CaretRight size={18} className="rotate-180 mr-1" />
            Back
          </Button>
          <div>
            <h1 className="text-2xl font-bold text-white font-['Outfit'] flex items-center gap-2">
              {getPlatformIcon(selectedAccount.platform)}
              {selectedAccount.account_name}
            </h1>
            <p className="text-zinc-500">@{selectedAccount.account_handle}</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-[#18181b] border border-[#27272a] rounded-xl p-4">
            <span className="text-zinc-400 text-sm">Videos Analyzed</span>
            <p className="text-2xl font-bold text-white">{selectedAccount.total_videos_analyzed}</p>
          </div>
          <div className="bg-[#18181b] border border-[#27272a] rounded-xl p-4">
            <span className="text-zinc-400 text-sm">Last Analysis</span>
            <p className="text-lg text-white">
              {selectedAccount.last_analysis_at 
                ? new Date(selectedAccount.last_analysis_at).toLocaleDateString()
                : "Never"}
            </p>
          </div>
          <div className="bg-[#18181b] border border-[#27272a] rounded-xl p-4">
            <span className="text-zinc-400 text-sm">Common Hook Style</span>
            <p className="text-lg text-yellow-500 capitalize">
              {selectedAccount.common_hook_styles?.[0] || "Unknown"}
            </p>
          </div>
          <div className="bg-[#18181b] border border-[#27272a] rounded-xl p-4">
            <span className="text-zinc-400 text-sm">Common CTA Style</span>
            <p className="text-lg text-green-500 capitalize">
              {selectedAccount.common_cta_styles?.[0] || "Unknown"}
            </p>
          </div>
        </div>

        <div className="bg-[#18181b] border border-[#27272a] rounded-xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Analyzed Videos</h3>
          {analyzedVideos.length > 0 ? (
            <div className="space-y-4">
              {analyzedVideos.map((video) => (
                <div key={video.id} className="p-4 bg-[#09090b] border border-[#27272a] rounded-lg">
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <p className="text-sm text-zinc-300 font-medium">{video.video_title || "Video"}</p>
                      <div className="flex items-center gap-3 mt-1">
                        <span className="text-xs text-zinc-500 flex items-center gap-1">
                          <Eye size={12} /> {video.views?.toLocaleString()}
                        </span>
                        <span className="text-xs text-zinc-500">
                          {video.engagement_rate?.toFixed(2)}% engagement
                        </span>
                      </div>
                    </div>
                    <Badge className={`text-xs ${video.engagement_rate > 5 ? "bg-green-500/10 text-green-400" : "bg-zinc-500/10 text-zinc-400"}`}>
                      {video.hook_style}
                    </Badge>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <p className="text-xs text-yellow-500 font-semibold mb-1">HOOK</p>
                      <p className="text-sm text-zinc-300">{video.hook_text}</p>
                    </div>
                    <div>
                      <p className="text-xs text-green-500 font-semibold mb-1">CTA ({video.cta_style})</p>
                      <p className="text-sm text-zinc-300">{video.cta_text}</p>
                    </div>
                  </div>
                  
                  {video.key_phrases?.length > 0 && (
                    <div className="mt-3 flex flex-wrap gap-2">
                      {video.key_phrases.slice(0, 5).map((phrase, i) => (
                        <Badge key={i} variant="secondary" className="text-xs">
                          {phrase}
                        </Badge>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <Button
                onClick={() => {
                  loadAnalyzedVideos(selectedAccount.id);
                }}
                variant="secondary"
              >
                Load Analyzed Videos
              </Button>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white font-['Outfit']">Style Tracker</h1>
          <p className="text-zinc-500 mt-1">Track accounts to learn winning styles</p>
        </div>
        <div className="flex gap-3">
          <Button
            onClick={analyzeAllAccounts}
            disabled={isLoading || accounts.length === 0}
            variant="secondary"
          >
            {isLoading ? (
              <ArrowClockwise size={18} className="animate-spin mr-2" />
            ) : (
              <MagnifyingGlass size={18} className="mr-2" />
            )}
            Analyze All
          </Button>
          <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
            <DialogTrigger asChild>
              <Button
                data-testid="add-account-btn"
                className="bg-yellow-500 hover:bg-yellow-400 text-black font-semibold"
              >
                <Plus size={18} className="mr-2" />
                Track Account
              </Button>
            </DialogTrigger>
            <DialogContent className="bg-[#18181b] border-[#27272a] text-white">
              <DialogHeader>
                <DialogTitle className="font-['Outfit']">Track New Account</DialogTitle>
                <DialogDescription className="text-zinc-500">
                  Add an account to analyze their top-performing content
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 mt-4">
                <Select value={formData.platform} onValueChange={(v) => setFormData({ ...formData, platform: v })}>
                  <SelectTrigger className="bg-[#09090b] border-[#27272a]">
                    <SelectValue placeholder="Platform" />
                  </SelectTrigger>
                  <SelectContent className="bg-[#18181b] border-[#27272a]">
                    <SelectItem value="instagram">Instagram</SelectItem>
                    <SelectItem value="youtube">YouTube</SelectItem>
                  </SelectContent>
                </Select>
                
                <Input
                  placeholder="Account URL (e.g., https://instagram.com/username)"
                  value={formData.account_url}
                  onChange={(e) => setFormData({ ...formData, account_url: e.target.value })}
                  className="bg-[#09090b] border-[#27272a]"
                />
                
                <div className="grid grid-cols-2 gap-4">
                  <Input
                    placeholder="Account Name"
                    value={formData.account_name}
                    onChange={(e) => setFormData({ ...formData, account_name: e.target.value })}
                    className="bg-[#09090b] border-[#27272a]"
                  />
                  <Input
                    placeholder="@handle"
                    value={formData.account_handle}
                    onChange={(e) => setFormData({ ...formData, account_handle: e.target.value })}
                    className="bg-[#09090b] border-[#27272a]"
                  />
                </div>
                
                <Select value={formData.check_frequency} onValueChange={(v) => setFormData({ ...formData, check_frequency: v })}>
                  <SelectTrigger className="bg-[#09090b] border-[#27272a]">
                    <Calendar size={16} className="mr-2" />
                    <SelectValue placeholder="Check Frequency" />
                  </SelectTrigger>
                  <SelectContent className="bg-[#18181b] border-[#27272a]">
                    <SelectItem value="daily">Daily</SelectItem>
                    <SelectItem value="weekly">Weekly</SelectItem>
                    <SelectItem value="biweekly">Every 2 Weeks</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <DialogFooter className="mt-6">
                <Button variant="secondary" onClick={() => setIsDialogOpen(false)}>
                  Cancel
                </Button>
                <Button
                  onClick={handleSubmit}
                  disabled={!formData.account_url || !formData.account_name}
                  className="bg-yellow-500 hover:bg-yellow-400 text-black"
                >
                  Add Account
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Style Insights Summary */}
      {styleInsights && (styleInsights.insights?.length > 0 || styleInsights.top_performing_hooks?.length > 0) && (
        <div className="mb-8">
          <div className="flex items-center gap-2 mb-4">
            <Lightbulb size={20} className="text-yellow-500" />
            <h2 className="text-xl font-semibold text-white">Style Insights</h2>
            <Badge className="bg-yellow-500/10 text-yellow-500">
              {styleInsights.total_videos_analyzed} videos analyzed
            </Badge>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Insights */}
            {styleInsights.insights?.length > 0 && (
              <div className="bg-[#18181b] border border-[#27272a] rounded-xl p-6">
                <h3 className="text-lg font-semibold text-white mb-4">Key Findings</h3>
                <div className="space-y-3">
                  {styleInsights.insights.slice(0, 3).map((insight) => (
                    <div key={insight.id} className="p-3 bg-[#09090b] border border-[#27272a] rounded-lg">
                      <p className="text-sm font-medium text-yellow-500">{insight.title}</p>
                      <p className="text-xs text-zinc-400 mt-1">{insight.description}</p>
                      {insight.examples?.length > 0 && (
                        <p className="text-xs text-zinc-500 mt-2 italic">"{insight.examples[0]}"</p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Top Hooks */}
            {styleInsights.top_performing_hooks?.length > 0 && (
              <div className="bg-[#18181b] border border-[#27272a] rounded-xl p-6">
                <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                  <TrendUp size={18} className="text-green-500" />
                  Top Performing Hooks
                </h3>
                <div className="space-y-3">
                  {styleInsights.top_performing_hooks.slice(0, 5).map((hook, i) => (
                    <div key={i} className="p-3 bg-[#09090b] border border-[#27272a] rounded-lg">
                      <p className="text-sm text-zinc-300">{hook.text}</p>
                      <div className="flex items-center gap-2 mt-2">
                        <Badge variant="secondary" className="text-xs">{hook.style}</Badge>
                        <span className="text-xs text-green-400">{hook.engagement?.toFixed(2)}% engagement</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tracked Accounts */}
      <h2 className="text-xl font-semibold text-white mb-4">Tracked Accounts</h2>
      {accounts.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {accounts.map((account) => (
            <div
              key={account.id}
              className="bg-[#18181b] border border-[#27272a] rounded-xl p-6 cursor-pointer hover:border-[#3f3f46] transition-all"
              onClick={() => {
                setSelectedAccount(account);
                loadAnalyzedVideos(account.id);
              }}
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  {getPlatformIcon(account.platform)}
                  <div>
                    <h3 className="font-semibold text-white">{account.account_name}</h3>
                    <p className="text-sm text-zinc-500">@{account.account_handle}</p>
                  </div>
                </div>
                <div className="flex gap-1">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      analyzeAccount(account);
                    }}
                    disabled={analyzingAccount === account.id}
                    className="text-zinc-500 hover:text-yellow-500"
                  >
                    {analyzingAccount === account.id ? (
                      <ArrowClockwise size={16} className="animate-spin" />
                    ) : (
                      <MagnifyingGlass size={16} />
                    )}
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      deleteAccount(account.id);
                    }}
                    className="text-zinc-500 hover:text-red-500"
                  >
                    <Trash size={16} />
                  </Button>
                </div>
              </div>
              
              <div className="flex items-center gap-3 mb-3">
                <Badge variant="secondary" className="text-xs">
                  {account.total_videos_analyzed} analyzed
                </Badge>
                <Badge variant="secondary" className="text-xs capitalize">
                  {account.check_frequency}
                </Badge>
              </div>
              
              {account.common_hook_styles?.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {account.common_hook_styles.slice(0, 3).map((style, i) => (
                    <Badge key={i} className="text-xs bg-yellow-500/10 text-yellow-500 capitalize">
                      {style}
                    </Badge>
                  ))}
                </div>
              )}
              
              {account.last_analysis_at && (
                <p className="text-xs text-zinc-500 mt-3">
                  Last analyzed: {new Date(account.last_analysis_at).toLocaleDateString()}
                </p>
              )}
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-16 bg-[#18181b] border border-[#27272a] rounded-xl">
          <Eye size={48} className="mx-auto text-zinc-600 mb-4" />
          <p className="text-zinc-500 mb-4">No tracked accounts yet</p>
          <p className="text-sm text-zinc-600 max-w-md mx-auto">
            Add TikTok, Instagram, or YouTube accounts to automatically analyze 
            their top-performing content and learn winning script patterns.
          </p>
        </div>
      )}
    </div>
  );
};

// ============================================================================
// NEW PROJECT DIALOG
// ============================================================================

const NewProjectDialog = ({ isOpen, onClose, brands, currentProfile, onCreate }) => {
  const [formData, setFormData] = useState({
    name: "",
    brand_id: "",
    is_ad: false,
    key_features: "",
  });

  const profileBrands = brands.filter(b => b.profile_id === currentProfile?.id);

  const handleSubmit = () => {
    const data = {
      ...formData,
      profile_id: currentProfile.id,
      brand_id: formData.brand_id === "none" ? null : formData.brand_id || null,
      key_features: formData.key_features.split(",").map((f) => f.trim()).filter(Boolean),
    };
    onCreate(data);
    onClose();
    setFormData({ name: "", brand_id: "", is_ad: false, key_features: "" });
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="bg-[#18181b] border-[#27272a] text-white">
        <DialogHeader>
          <DialogTitle className="font-['Outfit']">New Script Project</DialogTitle>
        </DialogHeader>
        <div className="space-y-4 mt-4">
          <Input
            data-testid="project-name-input"
            placeholder="Project Name"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            className="bg-[#09090b] border-[#27272a]"
          />
          
          <Select
            value={formData.brand_id || "none"}
            onValueChange={(v) => setFormData({ ...formData, brand_id: v })}
          >
            <SelectTrigger className="bg-[#09090b] border-[#27272a]">
              <SelectValue placeholder="Select Brand (Optional)" />
            </SelectTrigger>
            <SelectContent className="bg-[#18181b] border-[#27272a]">
              <SelectItem value="none">No Brand</SelectItem>
              {profileBrands.map((brand) => (
                <SelectItem key={brand.id} value={brand.id}>
                  {brand.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          
          <div className="flex items-center gap-3">
            <input
              type="checkbox"
              id="is_ad"
              checked={formData.is_ad}
              onChange={(e) => setFormData({ ...formData, is_ad: e.target.checked })}
              className="w-4 h-4 rounded border-zinc-600 bg-zinc-800 accent-yellow-500"
            />
            <label htmlFor="is_ad" className="text-sm text-zinc-300">
              This is an AD script
            </label>
          </div>
          
          <Input
            placeholder="Key Features (comma separated, optional)"
            value={formData.key_features}
            onChange={(e) => setFormData({ ...formData, key_features: e.target.value })}
            className="bg-[#09090b] border-[#27272a]"
          />
        </div>
        <DialogFooter className="mt-6">
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button
            data-testid="create-project-btn"
            onClick={handleSubmit}
            disabled={!formData.name.trim()}
            className="bg-yellow-500 hover:bg-yellow-400 text-black"
          >
            Create Project
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

// ============================================================================
// PROJECT EDITOR
// ============================================================================

const ProjectEditor = ({ project, brands, currentProfile, onUpdate, onBack }) => {
  const [isLoading, setIsLoading] = useState({});
  const [localProject, setLocalProject] = useState(project);

  const refreshProject = async () => {
    try {
      const res = await axios.get(`${API}/projects/${project.id}`);
      setLocalProject(res.data);
    } catch (e) {
      console.error("Failed to refresh project", e);
    }
  };

  const addVideo = async (url, language) => {
    setIsLoading({ ...isLoading, video: true });
    try {
      const res = await axios.post(`${API}/projects/${project.id}/add-video`, {
        video_url: url,
        target_language: language,
      });
      setLocalProject(res.data);
      toast.success("Video transcribed!");
    } catch (e) {
      toast.error(e.response?.data?.detail || "Failed to transcribe");
    } finally {
      setIsLoading({ ...isLoading, video: false });
    }
  };

  const addManualTranscript = async (text, language, sourceUrl) => {
    setIsLoading({ ...isLoading, video: true });
    try {
      const res = await axios.post(`${API}/projects/${project.id}/add-transcript-manual`, {
        transcript: text,
        language,
        source_url: sourceUrl
      });
      setLocalProject(res.data);
      toast.success("Transcript added!");
    } catch (e) {
      toast.error(e.response?.data?.detail || "Failed to add transcript");
    } finally {
      setIsLoading({ ...isLoading, video: false });
    }
  };

  const mixScripts = async () => {
    setIsLoading({ ...isLoading, mix: true });
    try {
      const res = await axios.post(`${API}/projects/${project.id}/mix-scripts`, {
        project_id: project.id,
        focus_areas: []
      });
      await refreshProject();
      toast.success("Scripts mixed!");
    } catch (e) {
      toast.error(e.response?.data?.detail || "Failed to mix scripts");
    } finally {
      setIsLoading({ ...isLoading, mix: false });
    }
  };

  const generateHooks = async () => {
    setIsLoading({ ...isLoading, hooks: true });
    try {
      await axios.post(`${API}/projects/${project.id}/generate-hooks`, {
        project_id: project.id,
        count: 5,
      });
      await refreshProject();
      toast.success("Hooks generated!");
    } catch (e) {
      toast.error("Failed to generate hooks");
    } finally {
      setIsLoading({ ...isLoading, hooks: false });
    }
  };

  const selectHooks = async (indices) => {
    try {
      await axios.post(`${API}/projects/${project.id}/select-hooks`, indices);
      setLocalProject({ ...localProject, selected_hook_indices: indices });
    } catch (e) {
      toast.error("Failed to select hooks");
    }
  };

  const generateBody = async () => {
    setIsLoading({ ...isLoading, body: true });
    try {
      const res = await axios.post(`${API}/projects/${project.id}/generate-body`);
      setLocalProject({ ...localProject, body_content: res.data.body_content });
      toast.success("Body generated!");
    } catch (e) {
      toast.error(e.response?.data?.detail || "Failed to generate body");
    } finally {
      setIsLoading({ ...isLoading, body: false });
    }
  };

  const generateCTA = async () => {
    setIsLoading({ ...isLoading, cta: true });
    try {
      const res = await axios.post(`${API}/projects/${project.id}/generate-cta`);
      setLocalProject({ ...localProject, cta_content: res.data.cta_content });
      toast.success("CTA generated!");
    } catch (e) {
      toast.error("Failed to generate CTA");
    } finally {
      setIsLoading({ ...isLoading, cta: false });
    }
  };

  const finalizeScript = async () => {
    setIsLoading({ ...isLoading, finalize: true });
    try {
      const res = await axios.post(`${API}/projects/${project.id}/finalize-script`);
      setLocalProject({ 
        ...localProject, 
        final_script: res.data.final_script, 
        actual_word_count: res.data.word_count,
        estimated_duration_seconds: res.data.duration_seconds,
        status: "completed" 
      });
      toast.success(`Script finalized! ${res.data.word_count} words • ${res.data.estimated_duration}`);
    } catch (e) {
      toast.error("Failed to finalize");
    } finally {
      setIsLoading({ ...isLoading, finalize: false });
    }
  };

  const generateCaption = async (platform = "tiktok", tone = "auto") => {
    setIsLoading({ ...isLoading, caption: true });
    try {
      const res = await axios.post(`${API}/projects/${project.id}/generate-caption`, {
        platform,
        tone,
        hashtag_count: 10
      });
      setLocalProject({ 
        ...localProject, 
        caption: res.data.captions?.[0] || "",
        caption_variations: res.data.captions || [],
        hashtags: res.data.hashtags,
        hashtags_categorized: res.data.hashtags_categorized,
        caption_tips: res.data.caption_tips,
        caption_platform: res.data.platform
      });
      toast.success("Caption generated!");
    } catch (e) {
      toast.error("Failed to generate caption");
    } finally {
      setIsLoading({ ...isLoading, caption: false });
    }
  };

  const generateVoiceover = async () => {
    setIsLoading({ ...isLoading, voiceover: true });
    try {
      const res = await axios.post(`${API}/projects/${project.id}/generate-voiceover`, {
        project_id: project.id,
        voice_id: "pNInz6obpgDQGcFmaJgB",
      });
      if (res.data.demo) {
        toast.info("Demo mode - ElevenLabs not configured");
      } else {
        setLocalProject({ ...localProject, voiceover_url: res.data.voiceover_url });
        toast.success("Voiceover generated!");
      }
    } catch (e) {
      toast.error("Failed to generate voiceover");
    } finally {
      setIsLoading({ ...isLoading, voiceover: false });
    }
  };

  const updateSection = async (section, content) => {
    try {
      const update = {};
      if (section === "body") update.body_content = content;
      else if (section === "cta") update.cta_content = content;
      
      await axios.put(`${API}/projects/${project.id}`, update);
      setLocalProject({ ...localProject, ...update });
      toast.success("Updated!");
    } catch (e) {
      toast.error("Failed to update");
    }
  };

  // Regenerate script with different word count
  const regenerateWithWordCount = async (targetWords) => {
    setIsLoading({ ...isLoading, regenerate: true });
    try {
      // Update project with new target
      await axios.put(`${API}/projects/${project.id}`, { 
        target_word_count: targetWords 
      });
      
      // Regenerate body with new word count
      const bodyRes = await axios.post(`${API}/projects/${project.id}/generate-body`);
      
      // Regenerate CTA
      const ctaRes = await axios.post(`${API}/projects/${project.id}/generate-cta`);
      
      // Finalize
      const finalRes = await axios.post(`${API}/projects/${project.id}/finalize-script`);
      
      setLocalProject({ 
        ...localProject, 
        body_content: bodyRes.data.body_content,
        cta_content: ctaRes.data.cta_content,
        final_script: finalRes.data.final_script,
        actual_word_count: finalRes.data.word_count,
        estimated_duration_seconds: finalRes.data.duration_seconds,
        target_word_count: targetWords
      });
      
      toast.success(`Script updated! ${finalRes.data.word_count} words`);
    } catch (e) {
      toast.error("Failed to regenerate");
    } finally {
      setIsLoading({ ...isLoading, regenerate: false });
    }
  };

  const selectedIndices = localProject.selected_hook_indices || [];
  const selectedHook = localProject.hooks?.[selectedIndices[0]];

  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-[#27272a] bg-[#09090b]">
        <div className="flex items-center gap-4">
          <Button variant="ghost" onClick={onBack} className="text-zinc-400 hover:text-white">
            <CaretRight size={18} className="rotate-180 mr-1" />
            Back
          </Button>
          <Separator orientation="vertical" className="h-6" />
          <div>
            <h1 className="text-lg font-semibold text-white">{localProject.name}</h1>
            <div className="flex items-center gap-2">
              {localProject.is_ad && (
                <Badge className="text-xs bg-yellow-500/10 text-yellow-500">AD</Badge>
              )}
              <Badge variant="secondary" className="text-xs">
                {currentProfile?.language === "ar" ? "🇪🇬 Arabic" : "🇺🇸 English"}
              </Badge>
            </div>
          </div>
        </div>
        
        <div className="flex items-center gap-3">
          <Badge className={localProject.status === "completed" ? "bg-green-500/10 text-green-500" : "bg-zinc-500/10 text-zinc-500"}>
            {localProject.status}
          </Badge>
          <Button
            data-testid="finalize-btn"
            onClick={finalizeScript}
            disabled={isLoading.finalize || !selectedHook || !localProject.body_content}
            className="bg-yellow-500 hover:bg-yellow-400 text-black font-semibold"
          >
            {isLoading.finalize ? (
              <ArrowClockwise size={18} className="animate-spin mr-2" />
            ) : (
              <Check size={18} className="mr-2" />
            )}
            Finalize Script
          </Button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Panel */}
        <div className="w-80 border-r border-[#27272a] bg-[#18181b] flex flex-col">
          <div className="p-4 border-b border-[#27272a]">
            <VideoInput 
              onAddVideo={addVideo}
              onAddManualTranscript={addManualTranscript}
              isLoading={isLoading.video}
              profileLanguage={currentProfile?.language}
            />
          </div>
          
          <ScrollArea className="flex-1 p-4">
            <div className="space-y-3">
              {localProject.transcripts?.length > 1 && (
                <Button
                  data-testid="mix-scripts-btn"
                  onClick={mixScripts}
                  disabled={isLoading.mix}
                  variant="secondary"
                  className="w-full mb-4"
                >
                  {isLoading.mix ? (
                    <ArrowClockwise size={16} className="animate-spin mr-2" />
                  ) : (
                    <Shuffle size={16} className="mr-2" />
                  )}
                  Mix {localProject.transcripts.length} Videos
                </Button>
              )}
              
              {localProject.transcripts?.map((t, i) => (
                <div key={i} className="p-4 bg-[#09090b] border border-[#27272a] rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    {t.manual ? (
                      <PencilSimple size={14} className="text-yellow-500" />
                    ) : (
                      <PlatformIcon platform={detectPlatform(t.url || "")} size={14} />
                    )}
                    <span className="text-xs text-zinc-500 truncate flex-1">
                      {t.manual ? "Manual transcript" : t.url}
                    </span>
                  </div>
                  <p className="text-sm text-zinc-300 line-clamp-4">{t.text}</p>
                  <div className="flex items-center gap-2 mt-2">
                    <Badge variant="secondary" className="text-xs">
                      {t.language === "ar" ? "Arabic" : "English"}
                    </Badge>
                    {t.manual && (
                      <Badge variant="secondary" className="text-xs bg-yellow-500/10 text-yellow-500 border-yellow-500/20">
                        Manual
                      </Badge>
                    )}
                  </div>
                </div>
              ))}
              
              {localProject.mixed_transcript && (
                <div className="p-4 bg-yellow-500/5 border border-yellow-500/20 rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <Shuffle size={14} className="text-yellow-500" />
                    <span className="text-xs text-yellow-500 font-medium">Mixed Script</span>
                  </div>
                  <p className="text-sm text-zinc-300 line-clamp-6">{localProject.mixed_transcript}</p>
                </div>
              )}
              
              {(!localProject.transcripts || localProject.transcripts.length === 0) && (
                <div className="text-center py-8 text-zinc-500">
                  <VideoCamera size={32} className="mx-auto mb-2 opacity-50" />
                  <p className="text-sm">Add videos to get started</p>
                </div>
              )}
            </div>
          </ScrollArea>
        </div>

        {/* Center Panel */}
        <div className="flex-1 flex flex-col overflow-hidden">
          <Tabs defaultValue="hooks" className="flex-1 flex flex-col">
            <TabsList className="mx-4 mt-4 bg-[#18181b] border border-[#27272a]">
              <TabsTrigger value="hooks" className="data-[state=active]:bg-yellow-500 data-[state=active]:text-black">
                <Lightning size={16} className="mr-2" />
                Hooks
              </TabsTrigger>
              <TabsTrigger value="body" className="data-[state=active]:bg-yellow-500 data-[state=active]:text-black">
                <Article size={16} className="mr-2" />
                Body
              </TabsTrigger>
              <TabsTrigger value="cta" className="data-[state=active]:bg-yellow-500 data-[state=active]:text-black">
                <Sparkle size={16} className="mr-2" />
                CTA
              </TabsTrigger>
              <TabsTrigger value="final" className="data-[state=active]:bg-yellow-500 data-[state=active]:text-black">
                <Check size={16} className="mr-2" />
                Final
              </TabsTrigger>
            </TabsList>

            <ScrollArea className="flex-1 p-4">
              <TabsContent value="hooks" className="mt-0 space-y-4">
                {(!localProject.transcripts || localProject.transcripts.length === 0) ? (
                  <div className="text-center py-16 text-zinc-500">
                    <p>Add at least one video first</p>
                  </div>
                ) : (
                  <>
                    <Button
                      data-testid="generate-hooks-btn"
                      onClick={generateHooks}
                      disabled={isLoading.hooks}
                      className="w-full bg-yellow-500 hover:bg-yellow-400 text-black font-semibold"
                    >
                      {isLoading.hooks ? (
                        <ArrowClockwise size={18} className="animate-spin mr-2" />
                      ) : (
                        <Sparkle size={18} className="mr-2" />
                      )}
                      Generate Hooks
                    </Button>
                    
                    <HookSelector
                      hooks={localProject.hooks}
                      selectedIndices={selectedIndices}
                      onSelect={selectHooks}
                      onRegenerate={generateHooks}
                      isLoading={isLoading.hooks}
                    />
                  </>
                )}
              </TabsContent>

              <TabsContent value="body" className="mt-0 space-y-4">
                {selectedHook ? (
                  <>
                    <div className="p-4 bg-yellow-500/10 border border-yellow-500/20 rounded-xl">
                      <div className="flex items-center gap-2 mb-2">
                        <Lightning size={16} className="text-yellow-500" />
                        <span className="text-xs font-semibold text-yellow-500">Selected Hook</span>
                      </div>
                      <p className="text-sm text-zinc-300">{selectedHook.text}</p>
                    </div>
                    
                    <Button
                      data-testid="generate-body-btn"
                      onClick={generateBody}
                      disabled={isLoading.body}
                      className="w-full bg-zinc-800 hover:bg-zinc-700 text-white border border-zinc-700"
                    >
                      {isLoading.body ? (
                        <ArrowClockwise size={18} className="animate-spin mr-2" />
                      ) : (
                        <Article size={18} className="mr-2" />
                      )}
                      Generate Body
                    </Button>
                    
                    <ScriptBlock
                      title="Body Content"
                      content={localProject.body_content}
                      onEdit={(c) => updateSection("body", c)}
                      icon={Article}
                    />
                  </>
                ) : (
                  <div className="text-center py-16 text-zinc-500">
                    <p>Select a hook first</p>
                  </div>
                )}
              </TabsContent>

              <TabsContent value="cta" className="mt-0 space-y-4">
                {localProject.body_content ? (
                  <>
                    <Button
                      data-testid="generate-cta-btn"
                      onClick={generateCTA}
                      disabled={isLoading.cta}
                      className="w-full bg-zinc-800 hover:bg-zinc-700 text-white border border-zinc-700"
                    >
                      {isLoading.cta ? (
                        <ArrowClockwise size={18} className="animate-spin mr-2" />
                      ) : (
                        <Sparkle size={18} className="mr-2" />
                      )}
                      Generate CTA
                    </Button>
                    
                    <ScriptBlock
                      title="Call To Action"
                      content={localProject.cta_content}
                      onEdit={(c) => updateSection("cta", c)}
                      icon={Sparkle}
                      color="green"
                    />
                  </>
                ) : (
                  <div className="text-center py-16 text-zinc-500">
                    <p>Generate body content first</p>
                  </div>
                )}
              </TabsContent>

              <TabsContent value="final" className="mt-0 space-y-4">
                {localProject.final_script ? (
                  <div className="space-y-4">
                    {/* Word Count Controller */}
                    <div className="p-4 bg-[#18181b] border border-[#27272a] rounded-xl">
                      <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center gap-3">
                          <div className="p-2 bg-yellow-500/10 rounded-lg">
                            <Article size={20} className="text-yellow-500" />
                          </div>
                          <div>
                            <p className="text-white font-semibold">Script Stats</p>
                            <p className="text-sm text-zinc-500">Adjust length as needed</p>
                          </div>
                        </div>
                      </div>
                      
                      <div className="grid grid-cols-3 gap-4 mb-4">
                        <div className="p-3 bg-[#09090b] border border-[#27272a] rounded-lg text-center">
                          <p className="text-2xl font-mono font-bold text-white">
                            {localProject.actual_word_count || 0}
                          </p>
                          <p className="text-xs text-zinc-500">Words</p>
                        </div>
                        <div className="p-3 bg-[#09090b] border border-[#27272a] rounded-lg text-center">
                          <p className="text-2xl font-mono font-bold text-yellow-500">
                            {Math.floor((localProject.estimated_duration_seconds || 0) / 60)}:{((localProject.estimated_duration_seconds || 0) % 60).toString().padStart(2, '0')}
                          </p>
                          <p className="text-xs text-zinc-500">Est. Time</p>
                        </div>
                        <div className="p-3 bg-[#09090b] border border-[#27272a] rounded-lg text-center">
                          <p className="text-2xl font-mono font-bold text-zinc-400">
                            {currentProfile?.language === "ar" ? "~130" : "~150"}
                          </p>
                          <p className="text-xs text-zinc-500">Words/Min</p>
                        </div>
                      </div>
                      
                      {/* Word Count Slider */}
                      <div className="space-y-3">
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-zinc-400">Adjust Word Count</span>
                          <span className="text-sm font-mono text-yellow-500">
                            {localProject.target_word_count || localProject.actual_word_count || 150} words
                          </span>
                        </div>
                        <Slider
                          value={[localProject.target_word_count || localProject.actual_word_count || 150]}
                          onValueChange={(val) => {
                            setLocalProject({ ...localProject, target_word_count: val[0] });
                          }}
                          min={50}
                          max={400}
                          step={10}
                          className="w-full"
                        />
                        <div className="flex justify-between text-xs text-zinc-600">
                          <span>Short (50)</span>
                          <span>Medium (150)</span>
                          <span>Long (400)</span>
                        </div>
                        
                        {(localProject.target_word_count && localProject.target_word_count !== localProject.actual_word_count) && (
                          <Button
                            onClick={() => regenerateWithWordCount(localProject.target_word_count)}
                            disabled={isLoading.regenerate}
                            className="w-full bg-yellow-500 hover:bg-yellow-400 text-black font-semibold mt-2"
                          >
                            {isLoading.regenerate ? (
                              <ArrowClockwise size={18} className="animate-spin mr-2" />
                            ) : (
                              <ArrowClockwise size={18} className="mr-2" />
                            )}
                            Regenerate with {localProject.target_word_count} words
                          </Button>
                        )}
                      </div>
                    </div>
                    
                    {/* Final Script */}
                    <div className="p-6 bg-[#09090b] border border-[#27272a] rounded-xl">
                      <div className="flex items-center justify-between mb-4">
                        <h3 className="font-semibold text-white">Final Script</h3>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            navigator.clipboard.writeText(localProject.final_script);
                            toast.success("Copied!");
                          }}
                          className="text-zinc-400 hover:text-white"
                        >
                          <Copy size={16} />
                        </Button>
                      </div>
                      <p className="text-zinc-300 whitespace-pre-wrap">{localProject.final_script}</p>
                    </div>
                    
                    <CaptionPanel
                      captions={localProject.caption_variations || (localProject.caption ? [localProject.caption] : [])}
                      hashtags={localProject.hashtags}
                      hashtagsCategorized={localProject.hashtags_categorized}
                      captionTips={localProject.caption_tips}
                      activePlatform={localProject.caption_platform}
                      onGenerate={generateCaption}
                      isLoading={isLoading.caption}
                    />
                    
                    <VoiceoverPanel
                      projectId={project.id}
                      voiceoverUrl={localProject.voiceover_url}
                      onGenerate={generateVoiceover}
                      isLoading={isLoading.voiceover}
                    />
                  </div>
                ) : (
                  <div className="text-center py-16 text-zinc-500">
                    <p>Complete all sections and click "Finalize Script"</p>
                  </div>
                )}
              </TabsContent>
            </ScrollArea>
          </Tabs>
        </div>

        {/* Right Panel - Chat */}
        <div className="w-96 border-l border-[#27272a]">
          <ChatInterface 
            projectId={project.id} 
            profileId={currentProfile?.id}
            onScriptUpdate={refreshProject} 
          />
        </div>
      </div>
    </div>
  );
};

// ============================================================================
// MAIN APP
// ============================================================================

function App() {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [profiles, setProfiles] = useState([]);
  const [currentProfile, setCurrentProfile] = useState(null);
  const [projects, setProjects] = useState([]);
  const [brands, setBrands] = useState([]);
  const [selectedProject, setSelectedProject] = useState(null);
  const [isNewProjectOpen, setIsNewProjectOpen] = useState(false);

  useEffect(() => {
    loadProfiles();
    loadData();
  }, []);

  const loadProfiles = async () => {
    try {
      const res = await axios.get(`${API}/profiles`);
      setProfiles(res.data);
      if (res.data.length > 0 && !currentProfile) {
        setCurrentProfile(res.data[0]);
      }
    } catch (e) {
      console.error("Failed to load profiles", e);
    }
  };

  const loadData = async () => {
    try {
      const [projectsRes, brandsRes] = await Promise.all([
        axios.get(`${API}/projects`),
        axios.get(`${API}/brands`),
      ]);
      setProjects(projectsRes.data);
      setBrands(brandsRes.data);
    } catch (e) {
      console.error("Failed to load data", e);
    }
  };

  const seedProfiles = async () => {
    try {
      await axios.post(`${API}/profiles/seed`);
      await loadProfiles();
      toast.success("Profiles created!");
    } catch (e) {
      toast.error("Failed to create profiles");
    }
  };

  const createProject = async (data) => {
    try {
      const res = await axios.post(`${API}/projects`, data);
      setProjects([res.data, ...projects]);
      setSelectedProject(res.data);
      toast.success("Project created!");
    } catch (e) {
      toast.error("Failed to create project");
    }
  };

  const deleteProject = async (id) => {
    try {
      await axios.delete(`${API}/projects/${id}`);
      setProjects(projects.filter((p) => p.id !== id));
      toast.success("Project deleted!");
    } catch (e) {
      toast.error("Failed to delete project");
    }
  };

  const saveBrand = async (data, id) => {
    try {
      if (id) {
        const res = await axios.put(`${API}/brands/${id}`, data);
        setBrands(brands.map((b) => (b.id === id ? res.data : b)));
      } else {
        const res = await axios.post(`${API}/brands`, data);
        setBrands([res.data, ...brands]);
      }
      toast.success("Brand saved!");
    } catch (e) {
      toast.error("Failed to save brand");
    }
  };

  const deleteBrand = async (id) => {
    try {
      await axios.delete(`${API}/brands/${id}`);
      setBrands(brands.filter((b) => b.id !== id));
      toast.success("Brand deleted!");
    } catch (e) {
      toast.error("Failed to delete brand");
    }
  };

  if (selectedProject) {
    return (
      <div className="app-container">
        <Toaster position="top-right" theme="dark" />
        <ProjectEditor
          project={selectedProject}
          brands={brands}
          currentProfile={currentProfile}
          onUpdate={(p) => {
            setProjects(projects.map((proj) => (proj.id === p.id ? p : proj)));
            setSelectedProject(p);
          }}
          onBack={() => {
            setSelectedProject(null);
            loadData();
          }}
        />
      </div>
    );
  }

  return (
    <div className="app-container flex">
      <Toaster position="top-right" theme="dark" />
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} currentProfile={currentProfile} />
      
      <main className="flex-1 overflow-auto">
        <div className="p-4 border-b border-[#27272a] bg-[#09090b]/50 backdrop-blur">
          <ProfileSelector
            profiles={profiles}
            currentProfile={currentProfile}
            onSelect={setCurrentProfile}
            onSeedProfiles={seedProfiles}
          />
        </div>
        
        {activeTab === "dashboard" && (
          <Dashboard
            projects={projects}
            brands={brands}
            currentProfile={currentProfile}
            onNewProject={() => setIsNewProjectOpen(true)}
          />
        )}
        
        {activeTab === "projects" && (
          <ProjectsList
            projects={projects}
            currentProfile={currentProfile}
            onSelect={setSelectedProject}
            onDelete={deleteProject}
            onNew={() => setIsNewProjectOpen(true)}
          />
        )}
        
        {activeTab === "brands" && (
          <BrandsPage
            brands={brands}
            currentProfile={currentProfile}
            onSave={saveBrand}
            onDelete={deleteBrand}
          />
        )}
        
        {activeTab === "tracked" && (
          <TrackedAccountsPage currentProfile={currentProfile} />
        )}
        
        {activeTab === "analytics" && (
          <AnalyticsPage currentProfile={currentProfile} />
        )}
      </main>

      <NewProjectDialog
        isOpen={isNewProjectOpen}
        onClose={() => setIsNewProjectOpen(false)}
        brands={brands}
        currentProfile={currentProfile}
        onCreate={createProject}
      />
    </div>
  );
}

export default App;
