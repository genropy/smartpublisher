#!/usr/bin/env python3
"""Mail service example with configuration and sending."""

from typing import Literal
from smpub import Publisher, PublishedClass
from smartswitch import Switcher


class MailHandler(PublishedClass):
    """Handler for mail operations."""

    __slots__ = ("config", "messages")
    api = Switcher(prefix="mail_")

    def __init__(self):
        self.config = {}
        self.messages = []

    @api
    def mail_configure_account(
        self,
        smtp_host: str,
        smtp_port: int = 587,
        username: str = "",
        use_tls: bool = True,
        auth_method: Literal["plain", "login", "oauth2"] = "plain",
    ):
        """Configure mail account settings.

        Args:
            smtp_host: SMTP server hostname (e.g., smtp.gmail.com)
            smtp_port: SMTP server port (default: 587)
            username: Email username/address
            use_tls: Use TLS encryption (default: True)
            auth_method: Authentication method (plain, login, or oauth2)
        """
        self.config = {
            "smtp_host": smtp_host,
            "smtp_port": smtp_port,
            "username": username,
            "use_tls": use_tls,
            "auth_method": auth_method,
            "configured": True,
        }

        return {
            "success": True,
            "message": f"Mail account configured: {username}@{smtp_host}:{smtp_port}",
            "config": self.config,
        }

    @api
    def mail_send(
        self,
        to: str,
        subject: str,
        body: str,
        priority: Literal["low", "normal", "high"] = "normal",
        html: bool = False,
    ):
        """Send an email message.

        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body text
            priority: Message priority (low, normal, or high)
            html: Send as HTML instead of plain text (default: False)
        """
        if not self.config.get("configured"):
            return {
                "success": False,
                "error": "Mail account not configured. Run configure_account first.",
            }

        message = {
            "id": len(self.messages) + 1,
            "from": self.config["username"],
            "to": to,
            "subject": subject,
            "body": body,
            "priority": priority,
            "html": html,
            "status": "sent",
        }
        self.messages.append(message)

        return {
            "success": True,
            "message": f"Email sent to {to}",
            "message_id": message["id"],
            "details": message,
        }

    @api
    def mail_list_sent(self):
        """List all sent messages."""
        return {"count": len(self.messages), "messages": self.messages}

    @api
    def mail_get_config(self):
        """Get current mail configuration."""
        if not self.config.get("configured"):
            return {"configured": False, "message": "Mail account not configured"}

        # Don't expose sensitive data in real scenario
        return {
            "configured": True,
            "smtp_host": self.config["smtp_host"],
            "smtp_port": self.config["smtp_port"],
            "username": self.config["username"],
            "use_tls": self.config["use_tls"],
            "auth_method": self.config["auth_method"],
        }

    @api
    def mail_clear_messages(self):
        """Clear all sent messages."""
        count = len(self.messages)
        self.messages.clear()
        return {"success": True, "cleared": count}


class MailApp(Publisher):
    """Mail service application."""

    def initialize(self):
        self.mail = MailHandler()
        self.publish("mail", self.mail, cli=True, openapi=True)


if __name__ == "__main__":
    app = MailApp()
    app.run()
