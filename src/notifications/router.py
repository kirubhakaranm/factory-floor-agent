"""Notification router — dispatches document notifications via pluggable channels."""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from src.documents.models import DocumentMeta, DocumentType

logger = logging.getLogger("primeev.notifications")


# ─── Channel Interface ─────────────────────────────────────────────────────────


class NotificationChannel(ABC):
    """Base class for notification channels. Implement this to add Teams, Jira, etc."""

    @abstractmethod
    def send(
        self,
        recipients: list[str],
        subject: str,
        body: str,
        attachment_path: Path | None = None,
    ) -> bool:
        """Send a notification. Returns True if successful."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        ...


# ─── Routing Configuration ────────────────────────────────────────────────────


NOTIFICATION_ROUTES: dict[DocumentType, dict[str, list[str]]] = {
    DocumentType.EIGHT_D: {
        "email": ["quality_manager@primeev.com", "plant_manager@primeev.com"],
        "teams": ["quality-alerts"],
        "jira": ["QUAL"],
    },
    DocumentType.NCR: {
        "email": ["supplier_quality@primeev.com"],
        "teams": ["supplier-quality"],
    },
    DocumentType.WORK_ORDER: {
        "email": ["maintenance_lead@primeev.com"],
        "teams": ["maintenance"],
        "jira": ["MAINT"],
    },
    DocumentType.INCIDENT_REPORT: {
        "email": ["quality_manager@primeev.com", "plant_manager@primeev.com", "shift_supervisor@primeev.com"],
        "teams": ["incidents"],
    },
    DocumentType.PDCA_RECORD: {
        "email": ["quality_manager@primeev.com", "process_engineer@primeev.com"],
        "teams": ["continuous-improvement"],
    },
    DocumentType.MAINTENANCE_NOTICE: {
        "email": ["production_supervisor@primeev.com", "shift_lead@primeev.com"],
        "teams": ["production"],
    },
}


# ─── Router ────────────────────────────────────────────────────────────────────


class NotificationRouter:
    """Routes document notifications to appropriate channels."""

    def __init__(self) -> None:
        self._channels: dict[str, NotificationChannel] = {}

    def register_channel(self, channel: NotificationChannel) -> None:
        self._channels[channel.name] = channel
        logger.info("Registered notification channel: %s", channel.name)

    def notify(
        self,
        meta: DocumentMeta,
        summary: str,
        attachment_path: Path | None = None,
    ) -> dict[str, bool]:
        """Send notifications for a document through all configured channels.

        Returns dict of {channel_name: success_bool}.
        """
        routes = NOTIFICATION_ROUTES.get(meta.doc_type, {})
        results: dict[str, bool] = {}

        subject = f"[PrimeEV] {meta.doc_type.value.replace('_', ' ').title()} — {meta.doc_id}"

        for channel_name, recipients in routes.items():
            channel = self._channels.get(channel_name)
            if channel is None:
                logger.debug("Channel '%s' not registered — skipping", channel_name)
                results[channel_name] = False
                continue

            try:
                success = channel.send(recipients, subject, summary, attachment_path)
                results[channel_name] = success
                if success:
                    logger.info("Notification sent via %s to %s", channel_name, recipients)
                else:
                    logger.warning("Notification failed via %s", channel_name)
            except Exception as e:
                logger.error("Notification error via %s: %s", channel_name, e)
                results[channel_name] = False

        return results
