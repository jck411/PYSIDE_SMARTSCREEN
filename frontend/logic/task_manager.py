#!/usr/bin/env python3
import asyncio
import logging

from frontend.config import logger

class TaskManager:
    """
    Manages asynchronous tasks and provides utilities for task execution.
    """
    def __init__(self, loop=None):
        self.tasks = {}
        self._loop = loop or asyncio.get_event_loop()
        logger.info("[TaskManager] Initialized")
        
    def create_task(self, name, coro):
        """
        Create and track a named task
        
        Args:
            name: String identifier for the task
            coro: Coroutine to execute
        
        Returns:
            Task object
        """
        task = self._loop.create_task(coro)
        self.tasks[name] = task
        logger.debug(f"[TaskManager] Created task: {name}")
        return task
        
    def cancel_task(self, name):
        """
        Cancel a specific task by name
        
        Args:
            name: String identifier for the task
        
        Returns:
            Boolean indicating if task was found and cancelled
        """
        if name in self.tasks and not self.tasks[name].done():
            self.tasks[name].cancel()
            logger.info(f"[TaskManager] Cancelled task: {name}")
            return True
        return False
        
    def cancel_all_tasks(self):
        """
        Cancel all tracked tasks
        
        Returns:
            Number of tasks cancelled
        """
        count = 0
        for name, task in list(self.tasks.items()):
            if not task.done():
                task.cancel()
                count += 1
        
        if count > 0:
            logger.info(f"[TaskManager] Cancelled {count} tasks")
        return count
        
    def schedule_coroutine(self, coro):
        """
        Schedule a coroutine without tracking it
        
        Args:
            coro: Coroutine to execute
            
        Returns:
            Task object
        """
        return self._loop.create_task(coro)
        
    def cleanup(self):
        """
        Cancel all tasks and perform cleanup
        """
        cancelled = self.cancel_all_tasks()
        logger.info(f"[TaskManager] Cleanup complete, cancelled {cancelled} tasks")
