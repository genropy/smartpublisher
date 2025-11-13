#!/usr/bin/env python3
"""Mail service example with account management and sending."""

from typing import Literal
from smartswitch import Switcher
from smartpublisher import Publisher


class AccountHandler:
    """Handler for account management."""

    __slots__ = ("accounts", "smpublisher")
    api = Switcher(prefix="account_")

    def __init__(self):
        self.accounts = {}

    @api
    def account_add(
        self,
        name: str,
        smtp_host: str,
        smtp_port: int = 587,
        username: str = "",
        use_tls: bool = True,
        auth_method: Literal["plain", "login", "oauth2"] = "plain",
    ):
        """Add a new mail account.

        Args:
            name: Account name/identifier
            smtp_host: SMTP server hostname (e.g., smtp.gmail.com)
            smtp_port: SMTP server port (default: 587)
            username: Email username/address
            use_tls: Use TLS encryption (default: True)
            auth_method: Authentication method (plain, login, or oauth2)
        """
        if name in self.accounts:
            return {"success": False, "error": f"Account '{name}' already exists"}

        self.accounts[name] = {
            "name": name,
            "smtp_host": smtp_host,
            "smtp_port": smtp_port,
            "username": username,
            "use_tls": use_tls,
            "auth_method": auth_method,
        }

        return {
            "success": True,
            "message": f"Account '{name}' added: {username}@{smtp_host}:{smtp_port}",
            "account": self.accounts[name],
        }

    @api
    def account_delete(self, name: str):
        """Delete a mail account.

        Args:
            name: Account name to delete
        """
        if name not in self.accounts:
            return {"success": False, "error": f"Account '{name}' not found"}

        account = self.accounts.pop(name)
        return {"success": True, "message": f"Account '{name}' deleted", "account": account}

    @api
    def account_list(self):
        """List all mail accounts."""
        return {"count": len(self.accounts), "accounts": list(self.accounts.values())}


class MailHandler:
    """Handler for mail operations."""

    __slots__ = ("account_handler", "messages", "smpublisher")
    api = Switcher(prefix="mail_")

    def __init__(self, account_handler):
        self.account_handler = account_handler
        self.messages = []

    @api
    def mail_send(
        self,
        account: str,
        to: str,
        subject: str,
        body: str,
        priority: Literal["low", "normal", "high"] = "normal",
        html: bool = False,
    ):
        """Send an email message.

        Args:
            account: Account name to use for sending
            to: Recipient email address
            subject: Email subject
            body: Email body text
            priority: Message priority (low, normal, or high)
            html: Send as HTML instead of plain text (default: False)
        """
        if account not in self.account_handler.accounts:
            return {
                "success": False,
                "error": f"Account '{account}' not found. Use 'account add' first.",
            }

        account_data = self.account_handler.accounts[account]
        message = {
            "id": len(self.messages) + 1,
            "account": account,
            "from": account_data["username"],
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
            "message": f"Email sent to {to} via account '{account}'",
            "message_id": message["id"],
            "details": message,
        }

    @api
    def mail_list(self):
        """List all sent messages."""
        return {"count": len(self.messages), "messages": self.messages}

    @api
    def mail_clear(self):
        """Clear all sent messages."""
        count = len(self.messages)
        self.messages.clear()
        return {"success": True, "cleared": count}


class MainClass(Publisher):
    """Mail service application."""

    def initialize(self):
        self.account = AccountHandler()
        self.mail = MailHandler(self.account)
        self.publish("account", self.account, cli=True, openapi=True)
        self.publish("mail", self.mail, cli=True, openapi=True)


if __name__ == "__main__":
    app = MainClass()
    app.run()
