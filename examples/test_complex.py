#!/usr/bin/env python3
"""Test complex signature with various parameter types."""

from enum import Enum
from typing import Literal
from smpub import Publisher, PublishedClass
from smartswitch import Switcher


class Priority(str, Enum):
    """Priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TaskHandler(PublishedClass):
    """Handler for task operations with complex signatures."""

    __slots__ = ("tasks",)
    api = Switcher(prefix="task_")

    def __init__(self):
        self.tasks = []

    @api
    def task_create(
        self,
        title: str,
        priority: Literal["low", "medium", "high"],
        max_retries: int = 3,
        notify: bool = False,
    ):
        """Create a new task with complex parameters.

        Args:
            title: Task title (string)
            priority: Priority level (low, medium, or high)
            max_retries: Maximum number of retries (integer, default: 3)
            notify: Send notification when complete (boolean, default: False)
        """
        task = {
            "id": len(self.tasks) + 1,
            "title": title,
            "priority": priority,
            "max_retries": max_retries,
            "notify": notify,
            "status": "created",
        }
        self.tasks.append(task)

        return {
            "success": True,
            "task": task,
            "message": f"Task '{title}' created with priority={priority}, "
            f"max_retries={max_retries}, notify={notify}",
        }

    @api
    def task_list(self):
        """List all tasks."""
        return {"count": len(self.tasks), "tasks": self.tasks}

    @api
    def task_clear(self):
        """Clear all tasks."""
        count = len(self.tasks)
        self.tasks.clear()
        return {"cleared": count}


class TestApp(Publisher):
    """Test application with complex signatures."""

    def initialize(self):
        self.tasks = TaskHandler()
        self.publish("tasks", self.tasks, cli=True, openapi=True)


if __name__ == "__main__":
    app = TestApp()
    app.run()
