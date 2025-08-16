"""
Fatebook MCP Server

A Model Context Protocol (MCP) server that provides integration with Fatebook,
a prediction tracking platform. This server allows AI assistants like Claude
to create, manage, and track predictions directly through MCP.
"""

__version__ = "0.1.0"
__author__ = "Stephen Malina"
__description__ = "Model Context Protocol server for Fatebook prediction tracking"

from .models import (
    Question,
    QuestionReference,
    QuestionsList,
    QuestionsResponse,
    User,
    Tag,
    Forecast,
    Comment,
)

__all__ = [
    "Question",
    "QuestionReference", 
    "QuestionsList",
    "QuestionsResponse",
    "User",
    "Tag", 
    "Forecast",
    "Comment",
]