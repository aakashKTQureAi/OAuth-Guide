"""Model providers a visitor can connect with their own key. One connection per session."""
import anthropic, openai

PROVIDERS = ("anthropic", "openai", "portkey")
DEFAULT_MODELS = {"anthropic": "claude-opus-5-5", "portkey": "claude-opus-5-5"}
PORTKEY_BASE_URL = "https://api.portkey.ai"  # shortcut: unverified for Claude server tools until the Portkey test passes


class ConnectionFailed(Exception):
    """Safe-to-show reason; never contains the key."""


def anthropic_client(conn):
    if conn["provider"] == "portkey":
        # Portkey authenticates with its own header; the Anthropic key slot is unused.
        return anthropic.Anthropic(api_key="portkey", base_url=PORTKEY_BASE_URL, max_retries=1, timeout=60.0,
                                   default_headers={"x-portkey-api-key": conn["api_key"],
                                                    "x-portkey-provider": conn.get("portkey_provider") or "anthropic"})
    return anthropic.Anthropic(api_key=conn["api_key"], max_retries=1, timeout=60.0)


def check(conn):
    """Make the cheapest call that proves the key works; raise ConnectionFailed otherwise."""
    try:
        if conn["provider"] == "openai":
            openai.OpenAI(api_key=conn["api_key"], max_retries=1, timeout=30.0).models.retrieve(conn["model"])
        elif conn["provider"] == "anthropic":
            anthropic_client(conn).models.retrieve(conn["model"])
        else:
            anthropic_client(conn).messages.create(model=conn["model"], max_tokens=16,
                                                   messages=[{"role": "user", "content": "Reply with OK."}])
    except (anthropic.AuthenticationError, openai.AuthenticationError):
        raise ConnectionFailed("The key was rejected.") from None
    except (anthropic.NotFoundError, openai.NotFoundError):
        raise ConnectionFailed("The key works, but that model was not found for it.") from None
    except (anthropic.APIStatusError, openai.APIStatusError) as exc:
        raise ConnectionFailed(f"The provider returned HTTP {exc.status_code}.") from None
    except (anthropic.APIConnectionError, openai.APIConnectionError):
        raise ConnectionFailed("Could not reach the provider.") from None
