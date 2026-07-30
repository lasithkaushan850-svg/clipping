"""Tests for caption style configuration loading and conversion."""

import pytest


def test_all_six_styles_loaded():
    """All 6 caption styles should be loaded from config."""
    from caption_styles import CAPTION_STYLES

    expected = {"hormozi", "mrbeast", "karaoke", "minimal", "bounce", "classic"}
    assert set(CAPTION_STYLES.keys()) == expected


def test_get_caption_style_returns_config():
    """get_caption_style should return a CaptionStyleConfig for valid ID."""
    from caption_styles import get_caption_style

    style = get_caption_style("hormozi")
    assert style.id == "hormozi"
    assert style.name == "Hormozi"
    assert style.font_name == "Montserrat"
    assert style.font_name_fallback == "IBM Plex Sans"
    assert style.bold is True
    assert style.animation_type == "highlight"


def test_get_caption_style_invalid_raises():
    """get_caption_style should raise ValueError for invalid style ID."""
    from caption_styles import get_caption_style

    with pytest.raises(ValueError, match="Invalid caption style"):
        get_caption_style("nonexistent")


def test_is_valid_caption_style():
    """is_valid_caption_style should return True/False correctly."""
    from caption_styles import is_valid_caption_style

    assert is_valid_caption_style("hormozi") is True
    assert is_valid_caption_style("mrbeast") is True
    assert is_valid_caption_style("nonexistent") is False


def test_hex_to_rgb():
    """hex_to_rgb should convert hex colors to RGB tuples."""
    from caption_styles import hex_to_rgb

    assert hex_to_rgb("#FFFFFF") == (255, 255, 255)
    assert hex_to_rgb("#000000") == (0, 0, 0)
    assert hex_to_rgb("#00FFFF") == (0, 255, 255)
    assert hex_to_rgb("FF6600") == (255, 102, 0)  # Without #


def test_hex_to_rgb_invalid():
    """hex_to_rgb should raise ValueError for invalid hex."""
    from caption_styles import hex_to_rgb

    with pytest.raises(ValueError, match="Invalid hex color"):
        hex_to_rgb("#GGG")
    with pytest.raises(ValueError, match="Invalid hex color"):
        hex_to_rgb("12345")


def test_rgb_to_ass():
    """rgb_to_ass should convert RGB to ASS BGR format."""
    from caption_styles import rgb_to_ass

    # White: R=255, G=255, B=255, Alpha=0 → &H00FFFFFF
    assert rgb_to_ass(255, 255, 255) == "&H00FFFFFF"
    # Black: R=0, G=0, B=0, Alpha=0 → &H00000000
    assert rgb_to_ass(0, 0, 0) == "&H00000000"
    # Cyan: R=0, G=255, B=255, Alpha=0 → &H00FFFF00
    assert rgb_to_ass(0, 255, 255) == "&H00FFFF00"
    # With alpha: &H80000000
    assert rgb_to_ass(0, 0, 0, alpha=128) == "&H80000000"


def test_rgb_to_ass_clamps():
    """rgb_to_ass should clamp values to 0-255."""
    from caption_styles import rgb_to_ass

    # r=300→255, g=-10→0, b=128
    result = rgb_to_ass(300, -10, 128)
    assert result == "&H008000FF"


def test_ass_colors_in_styles():
    """Caption style colors should be in ASS format (start with &H)."""
    from caption_styles import CAPTION_STYLES

    for style_id, style in CAPTION_STYLES.items():
        assert style.primary_color.startswith("&H"), f"{style_id} primary_color bad format"
        assert style.highlight_color.startswith("&H"), f"{style_id} highlight_color bad format"
        assert style.outline_color.startswith("&H"), f"{style_id} outline_color bad format"
        assert style.shadow_color.startswith("&H"), f"{style_id} shadow_color bad format"


def test_output_formats():
    """Output format configs should be loaded."""
    from caption_styles import get_output_format, is_valid_output_format

    assert is_valid_output_format("vertical") is True
    assert is_valid_output_format("square") is True
    assert is_valid_output_format("landscape") is True
    assert is_valid_output_format("nonexistent") is False

    vertical = get_output_format("vertical")
    assert vertical.width == 1080
    assert vertical.height == 1920
    assert vertical.aspect_ratio == "9:16"


def test_output_format_invalid_raises():
    """get_output_format should raise ValueError for invalid format."""
    from caption_styles import get_output_format

    with pytest.raises(ValueError, match="Invalid output format"):
        get_output_format("nonexistent")
