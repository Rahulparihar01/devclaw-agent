"""Model Provider layer for DevClaw.

OpenClaw is model-agnostic: users bring their own model (Gemini, Claude, GPT, or local Ollama).
This module provides:
1. BaseLLMProvider: Abstract contract.
2. IntelligentMockLLM: High-fidelity offline engine that demonstrates full ReAct tool-calling
   without requiring API keys or incurring costs.
3. OpenAICompatibleLLM: Works with OpenAI, Ollama, Groq, vLLM via pure stdlib HTTP.
"""

import json
import os
import re
import urllib.request
import urllib.error
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from core.models import AgentTurn, ToolCall


class BaseLLMProvider(ABC):
    """Abstract interface for LLM backends."""

    @abstractmethod
    def plan_turn(
        self,
        user_message: str,
        skills_schema: List[Dict[str, Any]],
        history: List[Dict[str, str]],
    ) -> AgentTurn:
        """Determines the next thought, tool calls, or final reply."""
        pass


class IntelligentMockLLM(BaseLLMProvider):
    """High-fidelity local reasoning engine for demos and testing without external API keys.

    Analyzes intent, decomposes multi-step goals, and generates thoughts and tool calls
    matching the OpenClaw execution style.
    """

    def plan_turn(
        self,
        user_message: str,
        skills_schema: List[Dict[str, Any]],
        history: List[Dict[str, str]],
    ) -> AgentTurn:
        text = user_message.lower()

        # Flight details or Check-in
        if any(w in text for w in ("flight", "airline", "boarding", "ticket", "sfo", "jfk")):
            if "other" in text or "another" in text or "more flight" in text:
                return AgentTurn(
                    thought="User asked for other flights.",
                    final_reply="✈️ I checked your inbox and calendar: you currently have only 1 scheduled flight:\n• United Airlines UA 442 (SFO ➔ JFK, Departure 08:30 AM tomorrow).\nNo other flight confirmations exist in your local records.",
                )
            return AgentTurn(
                thought="The user is asking about their flight. Searching inbox for flight-related confirmation emails.",
                tool_calls=[
                    ToolCall(
                        skill_name="search_emails",
                        arguments={"query": "Flight", "unread_only": False},
                        thought="Searching inbox for flight-related confirmation emails.",
                    )
                ],
            )

        # Email triage / reading / sending
        if "email" in text or "mail" in text or "inbox" in text or "unread" in text or "open all" in text or "read all" in text:
            # 1. Triage & Importance analysis
            if any(w in text for w in ("important", "triage", "priorit", "which email", "assist")):
                return AgentTurn(
                    thought="User requested inbox triage to identify high-priority emails.",
                    tool_calls=[
                        ToolCall(
                            skill_name="triage_inbox",
                            arguments={},
                            thought="Running OpenClaw TaskFlow inbox triage.",
                        )
                    ],
                )

            # 2. Read full content of email (all vs specific vs latest)
            if "read" in text or "open" in text or "show content" in text or "show body" in text or "view" in text:
                if "all" in text or "every" in text:
                    unread_only = "unread" in text
                    return AgentTurn(
                        thought="User requested opening all emails with full body content.",
                        tool_calls=[
                            ToolCall(
                                skill_name="read_all_emails",
                                arguments={"unread_only": unread_only},
                                thought="Opening all emails from inbox.",
                            )
                        ],
                    )

                id_match = re.search(r"(?:email|mail|id)\s*#?\s*(\d+)", text)
                if id_match:
                    email_id = int(id_match.group(1))
                    return AgentTurn(
                        thought=f"User requested reading email ID #{email_id}.",
                        tool_calls=[
                            ToolCall(
                                skill_name="read_email_full",
                                arguments={"email_id": email_id},
                                thought=f"Reading full email ID #{email_id}.",
                            )
                        ],
                    )

                return AgentTurn(
                    thought="User requested reading the body of an email.",
                    tool_calls=[
                        ToolCall(
                            skill_name="read_latest_email",
                            arguments={},
                            thought="Reading full email content.",
                        )
                    ],
                )

            # 3. Send or reply
            if "reply" in text or "send" in text or "draft" in text:
                match_email = re.search(r"to\s+([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)", user_message)
                recipient = match_email.group(1) if match_email else "alex@company.com"
                return AgentTurn(
                    thought=f"User requested to draft/send an email to {recipient}.",
                    tool_calls=[
                        ToolCall(
                            skill_name="send_email",
                            arguments={
                                "to": recipient,
                                "subject": "Re: Project Sync & Update",
                                "body": "Hi Alex,\n\nThanks for reaching out. Friday at 3:00 PM works great for the sync.\n\nBest,\nVinayak",
                            },
                            thought=f"Sending email response to {recipient}.",
                        )
                    ],
                )

            # 4. General search/list
            unread_only = "unread" in text
            return AgentTurn(
                thought="User requested an email inbox check. I will query the local email skill.",
                tool_calls=[
                    ToolCall(
                        skill_name="search_emails",
                        arguments={"query": "", "unread_only": unread_only},
                        thought="Querying local inbox.",
                    )
                ],
            )

        # Calendar operations
        if any(w in text for w in ("calendar", "event", "events", "schedule", "meeting", "agenda")):
            is_create = any(w in text for w in ("add event", "book a", "book meeting", "new event", "schedule a meeting", "schedule a sync", "create meeting", "create event"))
            if is_create:
                return AgentTurn(
                    thought="User wants to schedule a new event on their calendar.",
                    tool_calls=[
                        ToolCall(
                            skill_name="add_calendar_event",
                            arguments={
                                "title": "DevClaw Architecture Review with Alex",
                                "start_time": "2026-10-03 15:00:00",
                                "end_time": "2026-10-03 15:30:00",
                                "location": "Google Meet",
                                "description": "Review agent skills roadmap and integrations.",
                            },
                            thought="Adding calendar event into local SQLite database.",
                        )
                    ],
                )
            return AgentTurn(
                thought="User wants to view their calendar agenda / schedule.",
                tool_calls=[
                    ToolCall(
                        skill_name="list_calendar_events",
                        arguments={},
                        thought="Listing upcoming events.",
                    )
                ],
            )

        # Recalling facts / preferences
        if any(w in text for w in ("what", "show", "tell", "list")) and any(
            w in text for w in ("preference", "remember", "know about", "seat", "diet", "memory", "memories")
        ):
            return AgentTurn(
                thought="Recalling stored personal facts from local memory.",
                tool_calls=[
                    ToolCall(
                        skill_name="recall_facts",
                        arguments={"query": ""},
                        thought="Reading local memory facts.",
                    )
                ],
            )

        # Remembering facts
        if text.startswith("remember") or "note that" in text or "save preference" in text or ("remember" in text and not any(w in text for w in ("do you", "can you", "what"))):
            # Simple extractor
            key = "user_preference"
            category = "preference"
            val = user_message
            for prefix in ("remember that", "remember", "note that", "save preference"):
                if val.lower().startswith(prefix):
                    val = val[len(prefix):].strip()
                    break

            if "seat" in text:
                key = "seat_preference"
            elif "diet" in text or "food" in text or "vegetarian" in text or "gluten" in text:
                key = "dietary_preference"
            elif "airline" in text or "flight" in text:
                key = "favorite_airline"
            elif "contact" in text or "manager" in text:
                category = "contact"
                key = "contact_info"

            return AgentTurn(
                thought="Storing user fact into persistent local memory.",
                tool_calls=[
                    ToolCall(
                        skill_name="remember_fact",
                        arguments={"category": category, "key": key, "value": val},
                        thought=f"Saving {key} to local memory database.",
                    )
                ],
            )

        # Weather skill invocation
        if any(w in text for w in ("weather", "temperature", "forecast", "rain", "sunny", "climate")):
            # Extract city if provided
            loc_match = re.search(r"in\s+([a-zA-Z\s]+)", text)
            location = loc_match.group(1).strip() if loc_match else ""
            return AgentTurn(
                thought="User requested weather information. Invoking get_weather skill.",
                tool_calls=[
                    ToolCall(
                        skill_name="get_weather",
                        arguments={"location": location},
                        thought=f"Fetching live weather for {location or 'current location'}.",
                    )
                ],
            )

        # Conversational Greetings & Chit-Chat
        if any(re.search(r"\b" + g + r"\b", text) for g in ["hi", "hello", "hey", "howdy", "sup", "greetings"]):
            return AgentTurn(
                thought="User sent a greeting.",
                final_reply=(
                    "Hey there! 🦞 I'm your local assistant. "
                    "I can organize your emails, manage your calendar, check in for flights, "
                    "check the weather, or remember personal preferences. What can I do for you today?"
                ),
            )

        if "how are you" in text or "how's it going" in text:
            return AgentTurn(
                thought="User asked how the agent is doing.",
                final_reply=(
                    "Running great! 🦞 All local gateway services, database connections, and skills "
                    "are operating smoothly on your machine. How can I help you right now?"
                ),
            )

        if "who are you" in text or "what are you" in text:
            return AgentTurn(
                thought="User asked about identity.",
                final_reply=(
                    "I am DevClaw, an autonomous, local-first agent inspired by OpenClaw 🦞. "
                    "I run directly on your hardware and take real actions (emails, calendar, weather, "
                    "flights, preferences) across messaging platforms without cloud lock-in."
                ),
            )

        # Questions about OpenClaw
        if "who created" in text or "who made" in text or "founder" in text or "peter" in text:
            return AgentTurn(
                thought="User asked about the creator of OpenClaw.",
                final_reply=(
                    "OpenClaw was created by Peter Steinberger (founder of PSPDFKit) in late 2025. "
                    "It started under the name Warelay, briefly became Moltbot, and evolved into OpenClaw. "
                    "Today, it is stewarded as an independent 501(c)(3) non-profit (the OpenClaw Foundation) "
                    "with zero subscriptions or tokens."
                ),
            )

        if "what is openclaw" in text or "explain openclaw" in text or "tell me about openclaw" in text:
            return AgentTurn(
                thought="User asked for an explanation of OpenClaw.",
                final_reply=(
                    "OpenClaw is an open-source, self-hosted autonomous AI assistant that runs on your computer. "
                    "Instead of keeping you stuck in a browser chat tab, it connects into 20+ messaging apps "
                    "(WhatsApp, Telegram, Discord, Slack) and executes real-world actions: organizing your inbox, "
                    "booking calendar events, checking in for flights, and automating tasks with local privacy."
                ),
            )

        if "channel" in text or "whatsapp" in text or "telegram" in text or "discord" in text:
            return AgentTurn(
                thought="User asked about channel connectivity.",
                final_reply=(
                    "OpenClaw connects to over 20+ channels including WhatsApp, Telegram, Discord, Slack, "
                    "and iMessage. Messages sent from your phone are forwarded to your local gateway, "
                    "which executes skills and texts you back the results in real time."
                ),
            )

        if "free" in text or "cost" in text or "pricing" in text or "subscription" in text:
            return AgentTurn(
                thought="User asked about pricing.",
                final_reply=(
                    "OpenClaw is 100% free and open-source under an independent 501(c)(3) foundation. "
                    "There are no subscriptions, no hosted paywalls, and no proprietary tokens. "
                    "You own your memories, your tools, and your data."
                ),
            )

        # Conversational memory of history
        if "last message" in text or "what did i just ask" in text or "previous" in text:
            if history:
                last_user = [h["content"] for h in history if h.get("role") == "user"]
                if last_user:
                    return AgentTurn(
                        thought="Recalling previous conversation turn.",
                        final_reply=f"Earlier, you said: \"{last_user[-1]}\"",
                    )
            return AgentTurn(
                thought="No previous history found.",
                final_reply="This is the start of our current session!",
            )

        # Dynamic answer for general or help questions
        if any(w in text for w in ("how", "what", "why", "where", "can you", "help", "do you")):
            return AgentTurn(
                thought=f"Handling conversational question about: {user_message}",
                final_reply=(
                    f"Regarding '{user_message}':\n"
                    "I'm ready to handle this! You can ask me to execute actions like:\n"
                    "• 'What's the weather in Tokyo?' (Live weather skill)\n"
                    "• 'Show unread emails' or 'Send email to alex@company.com'\n"
                    "• 'Check in for flight UA 442 and add it to my calendar'\n"
                    "• 'Remember that my favorite airline is Delta'\n"
                    "• '/real status' to query the real installed OpenClaw engine.\n\n"
                    "💡 Tip: If you want full open-ended general intelligence (coding, creative writing, essays), "
                    "set `export OPENAI_API_KEY=...` or run Ollama, and I'll route any general question to the LLM!"
                ),
            )

        # Dynamic fallback that never repeats the exact same answer
        turn_count = len(history) // 2 + 1
        return AgentTurn(
            thought="General interaction without specific tool trigger.",
            final_reply=(
                f"Got it (Turn {turn_count}). I received: \"{user_message}\".\n"
                "I'm listening for your next command! You can ask me to check emails, manage calendar events, "
                "look up live weather, check flight status, or manage your local memory."
            ),
        )


class OllamaLLM(BaseLLMProvider):
    """Direct provider for local Ollama models with OpenClaw tool routing."""

    def __init__(
        self,
        host: str = "http://localhost:11434",
        model: str = "qwen2.5:1.5b",
    ):
        self.host = host.rstrip("/")
        self.model = model
        self.router = IntelligentMockLLM()

    def plan_turn(
        self,
        user_message: str,
        skills_schema: List[Dict[str, Any]],
        history: List[Dict[str, str]],
    ) -> AgentTurn:
        # Check if user message targets local tools (flight, emails, calendar, weather, memories, system)
        tool_turn = self.router.plan_turn(user_message, skills_schema, history)
        if tool_turn.tool_calls:
            return tool_turn

        # General questions, coding, chat -> pass directly to local Ollama!
        url = f"{self.host}/api/chat"
        system_prompt = (
            "You are DevClaw, an autonomous local AI personal assistant inspired by OpenClaw. "
            "You run directly on the user's local machine. "
            "Answer questions clearly, helpfully, and concisely."
        )

        messages = [{"role": "system", "content": system_prompt}]
        for h in history[-6:]:
            messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
        messages.append({"role": "user", "content": user_message})

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": 0.3},
        }

        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                reply_text = data.get("message", {}).get("content", "").strip()
                return AgentTurn(
                    thought=f"Ollama ({self.model}) generated response.",
                    final_reply=reply_text,
                )
        except Exception as e:
            # Fallback to intelligent offline heuristic if Ollama is unreachable
            mock = IntelligentMockLLM()
            fallback_turn = mock.plan_turn(user_message, skills_schema, history)
            fallback_turn.thought += f" (Ollama unavailable: {str(e)})"
            return fallback_turn


class OpenAICompatibleLLM(BaseLLMProvider):
    """Connects to any OpenAI-compatible API endpoint (OpenAI, Groq, vLLM)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.openai.com/v1",
        model: str = "gpt-4o-mini",
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.base_url = base_url.rstrip("/")
        self.model = model

    def plan_turn(
        self,
        user_message: str,
        skills_schema: List[Dict[str, Any]],
        history: List[Dict[str, str]],
    ) -> AgentTurn:
        if not self.api_key:
            fallback = IntelligentMockLLM()
            return fallback.plan_turn(user_message, skills_schema, history)

        url = f"{self.base_url}/chat/completions"
        system_prompt = (
            "You are DevClaw, an autonomous local assistant inspired by OpenClaw. "
            "You run directly on the user's machine. "
            "Decide whether to call tools or respond directly. "
            f"Available tools: {json.dumps(skills_schema)}"
        )

        messages = [{"role": "system", "content": system_prompt}] + history[-6:]
        messages.append({"role": "user", "content": user_message})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.2,
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                choice = data["choices"][0]["message"]
                content = choice.get("content", "")
                return AgentTurn(thought="API Response received", final_reply=content)
        except Exception:
            return IntelligentMockLLM().plan_turn(user_message, skills_schema, history)
