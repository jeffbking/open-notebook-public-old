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

    # langchain-openai silently switches ChatOpenAI to the Responses API
    # (POST /v1/responses) for any model name containing "codex" (e.g.
    # "codex/gpt-6-luna" on the Oneshot gateway). OpenAI-compatible endpoints
    # generally implement only /v1/chat/completions, so those calls 404.
    # Pin OpenAI-compatible providers to chat completions; the native OpenAI
    # provider keeps LangChain's default.
    try:
        from esperanto.providers.llm.openai_compatible import (
            OpenAICompatibleLanguageModel,
        )

        _orig_to_langchain = OpenAICompatibleLanguageModel.to_langchain

        def _patched_to_langchain(self):  # type: ignore[no-untyped-def]
            model = _orig_to_langchain(self)
            if hasattr(model, "use_responses_api"):
                model.use_responses_api = False
            return model

        OpenAICompatibleLanguageModel.to_langchain = _patched_to_langchain  # type: ignore[method-assign]
    except ImportError:
        pass


_apply_esperanto_patches()
