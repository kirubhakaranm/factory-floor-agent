"""Microsoft Teams notification channel — sends via incoming webhook.

To enable: set TEAMS_WEBHOOK_URL in .env and register this channel.
"""

import logging
from pathlib import Path

from src.notifications.router import NotificationChannel

logger = logging.getLogger("primeev.notifications.teams")


class TeamsWebhookChannel(NotificationChannel):
    """Sends notifications to Microsoft Teams via incoming webhook.

    Requires a Teams incoming webhook URL configured in .env.
    See: https://learn.microsoft.com/en-us/microsoftteams/platform/webhooks-and-connectors/how-to/add-incoming-webhook
    """

    def __init__(self, webhook_url: str | None = None):
        self._webhook_url = webhook_url

    @property
    def name(self) -> str:
        return "teams"

    def send(
        self,
        recipients: list[str],
        subject: str,
        body: str,
        attachment_path: Path | None = None,
    ) -> bool:
        if not self._webhook_url:
            logger.debug("Teams webhook URL not configured — skipping")
            return False

        # Teams Adaptive Card payload
        payload = {
            "type": "message",
            "attachments": [
                {
                    "contentType": "application/vnd.microsoft.card.adaptive",
                    "content": {
                        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                        "type": "AdaptiveCard",
                        "version": "1.4",
                        "body": [
                            {
                                "type": "TextBlock",
                                "text": subject,
                                "weight": "Bolder",
                                "size": "Medium",
                                "color": "Accent",
                            },
                            {
                                "type": "TextBlock",
                                "text": body,
                                "wrap": True,
                            },
                            {
                                "type": "FactSet",
                                "facts": [
                                    {"title": "Channel", "value": ", ".join(recipients)},
                                ],
                            },
                        ],
                    },
                }
            ],
        }

        try:
            import httpx

            response = httpx.post(self._webhook_url, json=payload, timeout=10)
            if response.status_code == 200:
                logger.info("Teams notification sent: %s", subject)
                return True
            else:
                logger.warning("Teams webhook returned %d", response.status_code)
                return False
        except ImportError:
            logger.warning("httpx not available for Teams webhook — install with: pip install httpx")
            return False
        except Exception as e:
            logger.error("Teams notification failed: %s", e)
            return False
