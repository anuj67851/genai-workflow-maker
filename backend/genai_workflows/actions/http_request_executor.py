import httpx
import json
import logging
from typing import Dict, Any

from .base_executor import BaseActionExecutor
from ..workflow import WorkflowStep

logger = logging.getLogger(__name__)

class HttpRequestAction(BaseActionExecutor):
    """Executes a direct, deterministic HTTP request to an external API."""

    async def execute(self, step: WorkflowStep, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Performs the HTTP request and handles success and failure cases.
        This executor is async-native.
        """
        # --- 1. Configuration Validation ---
        if not step.http_method or not step.url_template:
            return {"step_id": step.step_id, "success": False, "error": "HTTP Request node is missing 'http_method' or 'url_template'."}

        # --- 2. Fill Templates with Workflow State ---
        # The base `_fill_prompt_template` is perfect for simple string replacement.
        try:
            url = self._fill_prompt_template(step.url_template, state)
            headers_str = self._fill_prompt_template(step.headers_template, state)
            body_str = self._fill_prompt_template(step.body_template, state)
        except Exception as e:
            # Catch errors during template filling itself
            error_msg = f"Failed to fill templates for HTTP request: {e}"
            logger.error(f"Step '{step.step_id}': {error_msg}", exc_info=True)
            return {"step_id": step.step_id, "success": False, "error": error_msg}


        # --- 3. Parse JSON and Prepare Request ---
        try:
            headers = json.loads(headers_str) if headers_str else {}
            # Ensure headers are strings
            headers = {str(k): str(v) for k, v in headers.items()}

            body = json.loads(body_str) if body_str else None

            # Ensure content-type is set for POST/PUT if body exists
            if body and 'content-type' not in (h.lower() for h in headers.keys()):
                headers['Content-Type'] = 'application/json'

        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse Headers or Body as JSON: {e}"
            logger.error(f"Step '{step.step_id}': {error_msg}")
            return {"step_id": step.step_id, "success": False, "error": error_msg}

        logger.info(f"Executing HTTP {step.http_method.upper()} request to {url}")

        # --- 4. Execute the Request and Handle Errors ---
        try:
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method=step.http_method.upper(),
                    url=url,
                    headers=headers,
                    json=body, # httpx handles the serialization for json body
                    timeout=30.0 # A sensible default timeout
                )

                # This is a key error handling step. It will raise an exception for 4xx and 5xx responses.
                response.raise_for_status()

                # --- 5. Process Successful Response ---
                try:
                    response_body = response.json()
                except json.JSONDecodeError:
                    # If response is not JSON, return it as raw text
                    response_body = response.text

                output = {
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "body": response_body
                }

                return {"step_id": step.step_id, "success": True, "type": "http_request", "output": output}

        except httpx.HTTPStatusError as e:
            # Catches 4xx and 5xx errors
            # Safely try to get response text, but handle cases where it might not exist
            response_text = ""
            try:
                response_text = e.response.text
            except Exception:
                response_text = "(Could not retrieve error response body)"
            error_msg = f"API returned an error: {e.response.status_code} {e.response.reason_phrase}. Response: {response_text}"
            logger.error(f"Step '{step.step_id}': {error_msg}")
            return {"step_id": step.step_id, "success": False, "error": error_msg}
        except httpx.RequestError as e:
            # Catches network errors, DNS issues, timeouts, etc.
            error_msg = f"Network request failed: {e.__class__.__name__} - {e}"
            logger.error(f"Step '{step.step_id}': {error_msg}")
            return {"step_id": step.step_id, "success": False, "error": error_msg}
        except Exception as e:
            # Catch-all for any other unexpected errors
            error_msg = f"An unexpected error occurred during the HTTP request: {e}"
            logger.error(f"Step '{step.step_id}': {error_msg}", exc_info=True)
            return {"step_id": step.step_id, "success": False, "error": error_msg}