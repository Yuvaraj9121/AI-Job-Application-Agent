"""Manual Ollama connectivity check.

Run with: python -m app.test_ai_connection
"""

from .ai import ask_ai


def main():
    response = ask_ai("Reply with exactly: Ollama connection OK")
    print(response)


if __name__ == "__main__":
    main()
