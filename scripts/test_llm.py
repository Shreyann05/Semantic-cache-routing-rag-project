"""Make one small Groq request through the project's LiteLLM adapter."""
import sys
from pathlib import Path
from time import perf_counter

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import SETTINGS
from app.rag import LiteLLM


def main():
    model = SETTINGS.small_model
    started = perf_counter()
    try:
        answer, input_tokens, output_tokens = LiteLLM(SETTINGS.groq_api_key).answer(
            "Reply with the single word: connected", [], model
        )
    except Exception as exc:
        elapsed_ms = round((perf_counter() - started) * 1000, 2)
        print(f"provider: groq\nmodel: {model}\nsuccess: false")
        print(f"error: {type(exc).__name__}: {exc}")
        print(f"latency_ms: {elapsed_ms}")
        raise SystemExit(1)

    elapsed_ms = round((perf_counter() - started) * 1000, 2)
    print(f"provider: groq\nmodel: {model}\nsuccess: true")
    print(f"response: {answer}")
    print(f"input_tokens: {input_tokens}\noutput_tokens: {output_tokens}")
    print(f"total_tokens: {input_tokens + output_tokens}\nlatency_ms: {elapsed_ms}")


if __name__ == "__main__":
    main()
