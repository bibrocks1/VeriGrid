import os

from langchain_openai import ChatOpenAI


def get_llm():
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not configured"
        )

    model = os.getenv(
        "OPENAI_MODEL",
        "gpt-4o-mini"
    )

    return ChatOpenAI(
        model=model,
        api_key=api_key,
        temperature=0.1,
    )