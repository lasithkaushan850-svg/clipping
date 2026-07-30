"""ClipForge backend.

A unified FastAPI app that combines three vendored open-source projects:

  • vendor/AI-Youtube-Shorts-Generator   — viral-moment LLM scoring
  • vendor/ViralCutter                   — face-tracking vertical reframe
  • vendor/ai-video-captions             — Hormozi/MrBeast animated captions

Public surface lives in `app.main`.
"""
__version__ = "0.1.0"
