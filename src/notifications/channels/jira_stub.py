"""Jira ticket creation channel — stub implementation.

To enable: implement JiraChannel with your Jira Cloud credentials.
See: https://developer.atlassian.com/cloud/jira/platform/rest/v3/
"""

import logging
from pathlib import Path

from src.notifications.router import NotificationChannel

logger = logging.getLogger("primeev.notifications.jira")


class JiraChannel(NotificationChannel):
    """Creates Jira tickets for documents — stub implementation.

    To implement:
    1. pip install jira
    2. Set JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN in .env
    3. Replace the send() method with actual Jira API calls

    Example implementation:
        from jira import JIRA
        jira = JIRA(server=url, basic_auth=(email, token))
        issue = jira.create_issue(
            project=recipients[0],  # project key e.g. "QUAL"
            summary=subject,
            description=body,
            issuetype={"name": "Task"},
        )
    """

    def __init__(self, jira_url: str | None = None, email: str | None = None, token: str | None = None):
        self._jira_url = jira_url
        self._email = email
        self._token = token

    @property
    def name(self) -> str:
        return "jira"

    def send(
        self,
        recipients: list[str],
        subject: str,
        body: str,
        attachment_path: Path | None = None,
    ) -> bool:
        if not self._jira_url:
            logger.debug("Jira not configured — skipping ticket creation")
            return False

        # Stub: log what would be created
        project_key = recipients[0] if recipients else "FACTORY"
        logger.info(
            "Jira ticket (stub): project=%s, summary='%s', description length=%d",
            project_key, subject, len(body),
        )
        return False  # Return False since no real ticket was created
