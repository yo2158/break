"""
AI Factory for MAGIN v1.3 - Unified AI Engine Interface

This module provides a unified interface for calling multiple AI engines:
- MCP CLI engines (Claude, Gemini, ChatGPT)
- Gemini API (google-generativeai SDK)
- OpenRouter API (requests HTTP client)
- Ollama API (requests HTTP client)

Functions:
    call_ai(engine, model, prompt, timeout) -> Dict[str, Any]
        Main entry point for AI calls, routes to appropriate engine handler.

Engine-specific handlers (internal):
    _call_mcp(engine, model, prompt, timeout) -> Dict[str, Any]
    _call_gemini_api(model, prompt, timeout) -> Dict[str, Any]
    _call_openrouter(model, prompt, timeout) -> Dict[str, Any]
    _call_ollama(model, prompt, timeout) -> Dict[str, Any]

Response Format:
    {
        "success": bool,
        "response": Dict | None,  # Validated AI response (if success)
        "raw_output": str,
        "error": str | None,
        "elapsed_seconds": float
    }

Requirements Coverage:
    - Task 1.2: MCP CLI integration
    - Task 1.3: Gemini API integration
    - Task 1.4: OpenRouter API integration
    - Task 1.5: Ollama API integration
"""

import asyncio
import json
import logging
import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

# Helper functions for JSON extraction (simplified for BREAK)
def extract_json_from_markdown(text: str) -> Optional[Dict]:
    """Extract JSON from markdown code blocks or plain text."""
    if not text:
        return None

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to extract from markdown code block
    import re
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # Try to find JSON object
    json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass

    return None


def validate_ai_response(data: Dict) -> tuple:
    """Validate AI response (simplified for BREAK - accepts all valid JSON)."""
    if not isinstance(data, dict):
        return False, "Response is not a dictionary", None
    return True, "", data


def extract_codex_response(text: str) -> str:
    """Extract response from Codex output (remove prompt echo and metadata)."""
    # Codex output format:
    # Line 1-N: Header (OpenAI Codex v0.44.0..., --------, metadata)
    # user
    # <prompt>
    # thinking
    # <thinking text>
    # codex
    # <actual response with JSON>
    # tokens used
    # <token count>

    # Find "codex" marker (response section starts after this)
    codex_marker = "\ncodex\n"
    if codex_marker in text:
        # Extract everything after "codex" marker
        response_start = text.find(codex_marker) + len(codex_marker)
        response_section = text[response_start:]

        # Remove "tokens used" footer if present
        if "\ntokens used\n" in response_section:
            response_section = response_section.split("\ntokens used\n")[0]

        return response_section.strip()

    # Fallback: return as-is if format is unexpected
    return text

# Configure logging
logger = logging.getLogger(__name__)


# ============================================================
# Task 1.2.1: Main Entry Point
# ============================================================

async def call_ai(
    engine: str,
    model: Optional[str],
    prompt: str,
    timeout: int = 300
) -> Dict[str, Any]:
    """
    Call AI engine with unified interface.

    Routes request to appropriate engine handler based on engine type.
    Supports MCP CLI, Gemini API, OpenRouter API, and Ollama API.

    Args:
        engine: Engine type identifier
            - Claude: Claude CLI
            - Gemini: Gemini CLI
            - ChatGPT: ChatGPT CLI (via Codex)
            - API_Gemini: Gemini API (google-generativeai SDK)
            - API_OpenRouter: OpenRouter API (requests)
            - API_Ollama: Ollama API (requests)
        model: Model name (optional, uses default if None)
        prompt: Prompt text to send to AI
        timeout: Timeout in seconds (default: 300, increased for heavy local models)

    Returns:
        Dict[str, Any]: Response dictionary with structure:
            {
                "success": bool,
                "response": Dict | None,
                "raw_output": str,
                "error": str | None,
                "elapsed_seconds": float
            }

    Raises:
        ValueError: If engine is unknown

    Example:
        >>> result = await call_ai("Claude", None, "Test prompt", 300)
        >>> result["success"]
        True
    """
    logger.info(f"call_ai: engine={engine}, model={model}, timeout={timeout}")

    # Route to appropriate handler
    if engine in ["Claude", "Gemini", "ChatGPT"]:
        return await _call_cli(engine, model, prompt, timeout)
    elif engine == "API_Gemini":
        return await _call_gemini_api(model, prompt, timeout)
    elif engine == "API_OpenRouter":
        return await _call_openrouter(model, prompt, timeout)
    elif engine == "API_Ollama":
        return await _call_ollama(model, prompt, timeout)
    else:
        raise ValueError(f"Unknown engine: {engine}")


# ============================================================
# Task 1.2.2: CLI Handler (Claude, Gemini, ChatGPT)
# ============================================================

async def _call_cli(
    engine: str,
    model: Optional[str],
    prompt: str,
    timeout: int
) -> Dict[str, Any]:
    """
    Call CLI engines (Claude, Gemini, ChatGPT).

    Leverages existing logic from magi_orchestrator.py::call_ai_async().

    Args:
        engine: Claude | Gemini | ChatGPT
        model: Model name (ignored for CLI, uses default)
        prompt: Prompt text
        timeout: Timeout in seconds

    Returns:
        Response dictionary (see call_ai() docstring)

    Example:
        >>> result = await _call_cli("Claude", None, "Test", 30)
        >>> result["success"]
        True
    """
    start_time = datetime.now()

    # Map engine to command (non-interactive mode)
    command_map = {
        "Claude": ["claude", "-p"],
        "Gemini": ["gemini", "-p"],
        "ChatGPT": ["codex", "exec", "--skip-git-repo-check"]
    }

    if engine not in command_map:
        return {
            "success": False,
            "response": None,
            "raw_output": "",
            "error": f"Unknown CLI engine: {engine}",
            "elapsed_seconds": 0.0
        }

    command = command_map[engine]
    ai_name = engine

    try:
        logger.info(f"Starting CLI execution: {ai_name}")

        # Add prompt as command argument for non-interactive mode
        full_command = command + [prompt]

        # Create subprocess
        process = await asyncio.create_subprocess_exec(
            *full_command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        # Wait for completion with timeout
        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=timeout
        )

        stdout_text = stdout.decode('utf-8').strip()
        stderr_text = stderr.decode('utf-8').strip()

        elapsed = (datetime.now() - start_time).total_seconds()

        # Extract response (ChatGPT requires special handling)
        if 'chatgpt' in ai_name.lower():
            clean_output = extract_codex_response(stdout_text)
        else:
            clean_output = stdout_text

        # Extract JSON (ChatGPT: prioritize judgment JSON, fallback to last valid JSON)
        if 'chatgpt' in ai_name.lower():
            all_jsons = []
            search_pos = 0

            while search_pos < len(clean_output):
                brace_pos = clean_output.find('{', search_pos)
                if brace_pos == -1:
                    break

                test_json = extract_json_from_markdown(clean_output[brace_pos:])
                if test_json:
                    # Filter out persona JSON and incomplete responses
                    is_persona = 'persona_name' in test_json
                    is_not_applicable = test_json.get('decision') == 'NOT_APPLICABLE'
                    is_incomplete = 'scores' not in test_json and 'validity' in test_json

                    if not is_persona and not is_not_applicable and not is_incomplete:
                        all_jsons.append(test_json)

                    json_str = json.dumps(test_json, ensure_ascii=False)
                    search_pos = brace_pos + len(json_str)
                else:
                    search_pos = brace_pos + 1

            # Prioritize judgment JSON (has winner, scores, break_shot keys)
            judgment_jsons = [j for j in all_jsons if 'winner' in j and 'scores' in j and 'break_shot' in j]
            if judgment_jsons:
                json_data = judgment_jsons[-1]  # Take last judgment JSON
            else:
                json_data = all_jsons[-1] if all_jsons else None
        else:
            json_data = extract_json_from_markdown(clean_output)

        # Validate response
        if json_data:
            is_valid, error_msg, sanitized = validate_ai_response(json_data)
            if not is_valid:
                logger.error(f"{ai_name} validation failed: {error_msg}")
                logger.error(f"{ai_name} invalid JSON keys: {list(json_data.keys())}")
                logger.error(f"{ai_name} invalid JSON (first 200 chars): {str(json_data)[:200]}")
                return {
                    "success": False,
                    "response": None,
                    "raw_output": clean_output[:500],
                    "full_output": clean_output,
                    "error": f"Validation error: {error_msg}",
                    "elapsed_seconds": elapsed
                }
            json_data = sanitized

        logger.info(f"{ai_name} execution completed in {elapsed:.2f}s")

        # Success if we got valid JSON, regardless of stderr
        success = json_data is not None
        error = None if json_data else stderr_text

        return {
            "success": success,
            "response": json_data,
            "raw_output": clean_output[:500],  # Truncated for logging
            "full_output": clean_output,  # Full output for JSON parsing
            "error": error,  # Only report error if no JSON
            "elapsed_seconds": elapsed
        }

    except asyncio.TimeoutError:
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.warning(f"{ai_name} timed out after {timeout}s")

        # プロセスを強制終了してstderrを取得（429エラー等の詳細情報）
        process.kill()
        error_msg = f"タイムアウト ({timeout}秒)"

        # Try to capture stderr without blocking (non-blocking read attempt)
        try:
            # Short timeout to avoid long wait - if CLI is still writing, we skip it
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=2)
            stderr_text = stderr.decode('utf-8', errors='ignore').strip()

            # Log full stderr for debugging (even if we don't show it to user)
            if stderr_text:
                logger.info(f"{ai_name} stderr after timeout: {stderr_text[:500]}")

            # Check if it's a 429 error and update message
            if '429' in stderr_text or 'quota' in stderr_text.lower() or 'rate limit' in stderr_text.lower():
                # Extract just the key info for user
                if 'quota exceeded' in stderr_text.lower():
                    error_msg = "API quota exceeded (429). リクエスト制限に達しました。"
                elif 'rate limit' in stderr_text.lower():
                    error_msg = "API rate limit exceeded (429). レート制限に達しました。"
                else:
                    error_msg = "API quota/rate limit error (429)"
        except asyncio.TimeoutError:
            # stderr capture timed out (process still writing or hung)
            logger.warning(f"{ai_name} stderr capture timed out after 2s")
            error_msg = f"タイムアウト ({timeout}秒) - プロセス応答なし"
        except Exception as e:
            logger.error(f"Failed to capture stderr after timeout: {e}")

        # Ensure zombie process cleanup (wait for process to fully terminate)
        try:
            await asyncio.wait_for(process.wait(), timeout=1)
        except asyncio.TimeoutError:
            logger.warning(f"{ai_name} wait() timed out after process.kill()")
        except Exception as e:
            logger.error(f"Failed to wait for process termination: {e}")

        return {
            "success": False,
            "response": None,
            "raw_output": "",
            "error": error_msg,
            "elapsed_seconds": elapsed
        }

    except Exception as e:
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.error(f"{ai_name} execution error: {e}", exc_info=True)

        # Clean up process if it was created
        try:
            if 'process' in locals():
                process.kill()
                await asyncio.wait_for(process.wait(), timeout=1)
        except Exception as cleanup_error:
            logger.error(f"Failed to cleanup process after error: {cleanup_error}")

        return {
            "success": False,
            "response": None,
            "raw_output": "",
            "error": str(e),
            "elapsed_seconds": elapsed
        }


# ============================================================
# Task 1.3.1: Gemini API Handler
# ============================================================

async def _call_gemini_api(
    model: Optional[str],
    prompt: str,
    timeout: int
) -> Dict[str, Any]:
    """
    Call Gemini API using google-generativeai SDK.

    Supported models:
    - gemini-2.5-flash (default)
    - gemini-2.5-flash-lite
    - gemini-2.5-pro

    Args:
        model: Model name (optional, defaults to gemini-2.5-flash)
        prompt: Prompt text
        timeout: Timeout in seconds

    Returns:
        Response dictionary (see call_ai() docstring)

    Raises:
        None (all errors are captured in response)

    Example:
        >>> result = await _call_gemini_api("gemini-2.5-flash", "Test", 30)
        >>> result["success"]
        True
    """
    start_time = datetime.now()

    # Load environment variables from .env file
    from backend.config_manager import load_env
    env = load_env()

    # Check API key
    api_key = env.get("GEMINI_API_KEY")
    if not api_key:
        return {
            "success": False,
            "response": None,
            "raw_output": "",
            "error": "GEMINI_API_KEY not set",
            "elapsed_seconds": 0.0
        }

    # Default model
    if not model:
        model = "gemini-2.5-flash"

    try:
        import google.generativeai as genai

        # Configure API
        genai.configure(api_key=api_key)

        # Create model instance with generation config
        generation_config = {
            "max_output_tokens": 8000,  # Increase from default (~2048) to allow longer responses
            "temperature": 1.0,
        }
        model_instance = genai.GenerativeModel(
            model,
            generation_config=generation_config
        )

        # Generate content with timeout
        response = await asyncio.wait_for(
            asyncio.to_thread(model_instance.generate_content, prompt),
            timeout=timeout
        )

        elapsed = (datetime.now() - start_time).total_seconds()

        # Extract text
        raw_output = response.text

        # Extract JSON
        json_data = extract_json_from_markdown(raw_output)

        # Validate response
        if json_data:
            is_valid, error_msg, sanitized = validate_ai_response(json_data)
            if not is_valid:
                logger.error(f"Gemini API validation failed: {error_msg}")
                return {
                    "success": False,
                    "response": None,
                    "raw_output": raw_output[:500],
                    "full_output": raw_output,
                    "error": f"Validation error: {error_msg}",
                    "elapsed_seconds": elapsed
                }
            json_data = sanitized

        logger.info(f"Gemini API execution completed in {elapsed:.2f}s")

        return {
            "success": json_data is not None,
            "response": json_data,
            "raw_output": raw_output[:500],  # Truncated for logging
            "full_output": raw_output,  # Full output for JSON parsing
            "error": None if json_data else "Failed to extract JSON",
            "elapsed_seconds": elapsed
        }

    except asyncio.TimeoutError:
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.warning(f"Gemini API timed out after {timeout}s")
        return {
            "success": False,
            "response": None,
            "raw_output": "",
            "error": f"タイムアウト ({timeout}秒)",
            "elapsed_seconds": elapsed
        }

    except Exception as e:
        elapsed = (datetime.now() - start_time).total_seconds()
        error_msg = str(e)

        # Handle rate limit errors (429)
        if "429" in error_msg or "quota" in error_msg.lower() or "rate limit" in error_msg.lower():
            # Try to extract Retry-After header
            retry_after = "unknown"
            if hasattr(e, 'response') and hasattr(e.response, 'headers'):
                retry_after = e.response.headers.get('Retry-After', 'unknown')
            error_msg = f"Rate limit exceeded. Retry after: {retry_after} seconds"

        logger.error(f"Gemini API execution error: {error_msg}", exc_info=True)
        return {
            "success": False,
            "response": None,
            "raw_output": "",
            "error": error_msg,
            "elapsed_seconds": elapsed
        }


# ============================================================
# Task 1.4.1: OpenRouter API Handler
# ============================================================

async def _call_openrouter(
    model: Optional[str],
    prompt: str,
    timeout: int
) -> Dict[str, Any]:
    """
    Call OpenRouter API using requests library.

    Supported models:
    - x-ai/grok-code-fast-1 (default)
    - anthropic/claude-sonnet-4.5
    - openai/gpt-oss-20b:free
    - google/gemma-3-27b-it:free

    Args:
        model: Model name (optional, defaults to x-ai/grok-code-fast-1)
        prompt: Prompt text
        timeout: Timeout in seconds

    Returns:
        Response dictionary (see call_ai() docstring)

    Example:
        >>> result = await _call_openrouter("x-ai/grok-code-fast-1", "Test", 30)
        >>> result["success"]
        True
    """
    start_time = datetime.now()

    # Load environment variables from .env file
    from backend.config_manager import load_env
    env = load_env()

    # Check API key
    api_key = env.get("OPENROUTER_API_KEY")
    if not api_key:
        return {
            "success": False,
            "response": None,
            "raw_output": "",
            "error": "OPENROUTER_API_KEY not set",
            "elapsed_seconds": 0.0
        }

    # Default model
    if not model:
        model = "x-ai/grok-code-fast-1"

    try:
        import requests

        # Prepare request
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://github.com/yo2158/break",
            "X-Title": "BREAK"
        }
        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }

        # Make request with timeout
        response = await asyncio.wait_for(
            asyncio.to_thread(
                requests.post,
                url,
                headers=headers,
                json=payload,
                timeout=timeout
            ),
            timeout=timeout + 5  # Add buffer for network overhead
        )

        elapsed = (datetime.now() - start_time).total_seconds()

        # Handle HTTP errors
        if response.status_code == 404:
            return {
                "success": False,
                "response": None,
                "raw_output": "",
                "error": "Selected model is not available on OpenRouter.",
                "elapsed_seconds": elapsed
            }

        if response.status_code != 200:
            error_text = response.text[:500]
            return {
                "success": False,
                "response": None,
                "raw_output": error_text,
                "error": f"HTTP {response.status_code}: {error_text}",
                "elapsed_seconds": elapsed
            }

        # Parse response
        response_data = response.json()
        raw_output = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")

        # Extract JSON
        json_data = extract_json_from_markdown(raw_output)

        # Validate response
        if json_data:
            is_valid, error_msg, sanitized = validate_ai_response(json_data)
            if not is_valid:
                logger.error(f"OpenRouter validation failed: {error_msg}")
                return {
                    "success": False,
                    "response": None,
                    "raw_output": raw_output[:500],
                    "full_output": raw_output,
                    "error": f"Validation error: {error_msg}",
                    "elapsed_seconds": elapsed
                }
            json_data = sanitized

        logger.info(f"OpenRouter execution completed in {elapsed:.2f}s")

        return {
            "success": json_data is not None,
            "response": json_data,
            "raw_output": raw_output[:500],
            "full_output": raw_output,
            "error": None if json_data else "Failed to extract JSON",
            "elapsed_seconds": elapsed
        }

    except asyncio.TimeoutError:
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.warning(f"OpenRouter timed out after {timeout}s")
        return {
            "success": False,
            "response": None,
            "raw_output": "",
            "error": f"タイムアウト ({timeout}秒)",
            "elapsed_seconds": elapsed
        }

    except Exception as e:
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.error(f"OpenRouter execution error: {e}", exc_info=True)
        return {
            "success": False,
            "response": None,
            "raw_output": "",
            "error": str(e),
            "elapsed_seconds": elapsed
        }


# ============================================================
# Task 1.5.1: Ollama API Handler
# ============================================================

async def _call_ollama(
    model: Optional[str],
    prompt: str,
    timeout: int
) -> Dict[str, Any]:
    """
    Call Ollama API using requests library.

    Supported models:
    - gemma3:12b (default)
    - gemma3:27b
    - gpt-oss:latest

    Args:
        model: Model name (optional, defaults to gemma3:12b)
        prompt: Prompt text
        timeout: Timeout in seconds (default: 300 for heavy local LLM models)

    Returns:
        Response dictionary (see call_ai() docstring)

    Example:
        >>> result = await _call_ollama("gemma3:12b", "Test", 60)
        >>> result["success"]
        True
    """
    start_time = datetime.now()

    # Load environment variables from .env file
    from backend.config_manager import load_env
    env = load_env()

    # Get Ollama URL (default: http://localhost:11434)
    ollama_url = env.get("OLLAMA_URL", "http://localhost:11434")

    # Default model
    if not model:
        model = "gemma3:12b"

    try:
        import requests

        # Prepare request
        url = f"{ollama_url}/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False
        }

        # Make request with timeout (default: 300s for heavy local LLM)
        response = await asyncio.wait_for(
            asyncio.to_thread(
                requests.post,
                url,
                json=payload,
                timeout=timeout
            ),
            timeout=timeout + 5  # Add buffer
        )

        elapsed = (datetime.now() - start_time).total_seconds()

        # Handle HTTP 404 (model not found)
        if response.status_code == 404:
            return {
                "success": False,
                "response": None,
                "raw_output": "",
                "error": f"Model not found. Please run: ollama pull {model}",
                "elapsed_seconds": elapsed
            }

        if response.status_code != 200:
            error_text = response.text[:500]
            return {
                "success": False,
                "response": None,
                "raw_output": error_text,
                "error": f"HTTP {response.status_code}: {error_text}",
                "elapsed_seconds": elapsed
            }

        # Parse response
        response_data = response.json()
        raw_output = response_data.get("response", "")

        # Extract JSON
        json_data = extract_json_from_markdown(raw_output)

        # Validate response
        if json_data:
            is_valid, error_msg, sanitized = validate_ai_response(json_data)
            if not is_valid:
                logger.error(f"Ollama validation failed: {error_msg}")
                return {
                    "success": False,
                    "response": None,
                    "raw_output": raw_output[:500],
                    "full_output": raw_output,
                    "error": f"Validation error: {error_msg}",
                    "elapsed_seconds": elapsed
                }
            json_data = sanitized

        logger.info(f"Ollama execution completed in {elapsed:.2f}s")

        return {
            "success": json_data is not None,
            "response": json_data,
            "raw_output": raw_output[:500],
            "full_output": raw_output,
            "error": None if json_data else "Failed to extract JSON",
            "elapsed_seconds": elapsed
        }

    except asyncio.TimeoutError:
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.warning(f"Ollama timed out after {timeout}s")
        return {
            "success": False,
            "response": None,
            "raw_output": "",
            "error": f"タイムアウト ({timeout}秒)",
            "elapsed_seconds": elapsed
        }

    except requests.exceptions.ConnectionError:
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.error(f"Ollama connection refused at {ollama_url}")
        return {
            "success": False,
            "response": None,
            "raw_output": "",
            "error": "Ollama is not running.",
            "elapsed_seconds": elapsed
        }

    except Exception as e:
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.error(f"Ollama execution error: {e}", exc_info=True)
        return {
            "success": False,
            "response": None,
            "raw_output": "",
            "error": str(e),
            "elapsed_seconds": elapsed
        }
