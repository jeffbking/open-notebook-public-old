"""Open Notebook package initialization."""

from typing import Any, Dict


def _apply_esperanto_patches() -> None:
    """Patch esperanto's GoogleSpeechToTextModel to support Gemini dedicated
    transcription models (e.g. gemini-3.5-transcribe) which return
    part['audioTranscription']['text'] instead of part['text'].
    """
    try:
        from esperanto.providers.stt.google import GoogleSpeechToTextModel

        _orig_parse = GoogleSpeechToTextModel._parse_response

        def _patched_parse_response(self, response_data: Dict[str, Any]) -> str:
            try:
                candidates = response_data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        first_part = parts[0]
                        if "text" in first_part:
                            return first_part["text"]
                        if (
                            "audioTranscription" in first_part
                            and "text" in first_part["audioTranscription"]
                        ):
                            return first_part["audioTranscription"]["text"]
            except Exception:
                pass
            return _orig_parse(self, response_data)

        GoogleSpeechToTextModel._parse_response = _patched_parse_response
    except ImportError:
        pass


_apply_esperanto_patches()
