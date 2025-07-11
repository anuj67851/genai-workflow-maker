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
        if not step.http_method or not step.url_template:
            return {"step_id": step.step_id, "success": False, "error": "HTTP Request node is missing 'http_method' or 'url_template'."}

        try:
            # URL is a simple string, so _fill_prompt_template is appropriate.
            url = self._fill_prompt_template(step.url_template, state)

            # Headers and Body are JSON structures, so use the robust _fill_json_template.
            headers = self._fill_json_template(step.headers_template, state) if step.headers_template else {}
            body = self._fill_json_template(step.body_template, state) if step.body_template else None

            # Ensure headers are strings
            headers = {str(k): str(v) for k, v in headers.items()}

            if body and 'content-type' not in (h.lower() for h in headers.keys()):
                headers['Content-Type'] = 'application/json'

        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON structure in Headers or Body template: {e}"
            logger.error(f"Step '{step.step_id}': {error_msg}")
            return {"step_id": step.step_id, "success": False, "error": error_msg}
        except Exception as e:
            error_msg = f"Failed to prepare templates for HTTP request: {e}"
            logger.error(f"Step '{step.step_id}': {error_msg}", exc_info=True)
            return {"step_id": step.step_id, "success": False, "error": error_msg}

        logger.info(f"Executing HTTP {step.http_method.upper()} request to {url}")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method=step.http_method.upper(),
                    url=url,
                    headers=headers,
                    json=body,
                    timeout=30.0
                )
                response.raise_for_status()

                try:
                    response_body = response.json()
                except json.JSONDecodeError:
                    response_body = response.text

                output = {
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "body": response_body
                }
                return {"step_id": step.step_id, "success": True, "type": "http_request", "output": output}

        except httpx.HTTPStatusError as e:
            response_text = ""
            try: response_text = e.response.text
            except Exception: response_text = "(Could not retrieve error response body)"
            error_msg = f"API returned an error: {e.response.status_code} {e.response.reason_phrase}. Response: {response_text}"
            logger.error(f"Step '{step.step_id}': {error_msg}")
            return {"step_id": step.step_id, "success": False, "error": error_msg}
        except httpx.RequestError as e:
            error_msg = f"Network request failed: {e.__class__.__name__} - {e}"
            logger.error(f"Step '{step.step_id}': {error_msg}")
            return {"step_id": step.step_id, "success": False, "error": error_msg}
        except Exception as e:
            error_msg = f"An unexpected error occurred during the HTTP request: {e}"
            logger.error(f"Step '{step.step_id}': {error_msg}", exc_info=True)
            return {"step_id": step.step_id, "success": False, "error": error_msg}