from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field, field_validator


class SlimBaseModel(BaseModel):
    """Base model that excludes None fields by default to save context tokens"""

    def model_dump(self, *, exclude_none: bool = True, **kwargs) -> Dict[str, Any]:
        return super().model_dump(exclude_none=exclude_none, **kwargs)


class User(SlimBaseModel):
    """User information for forecasts and comments"""

    id: Optional[Union[str, int]] = None
    name: str

    @field_validator("id")
    @classmethod
    def convert_id_to_string(cls, v):
        """Convert integer IDs to strings"""
        return str(v) if v is not None else v


class Tag(SlimBaseModel):
    """Tag model for question categorization"""

    id: Optional[Union[str, int]] = None
    name: str

    @field_validator("id")
    @classmethod
    def convert_id_to_string(cls, v):
        """Convert integer IDs to strings"""
        return str(v) if v is not None else v


class Forecast(SlimBaseModel):
    """Forecast made on a question"""

    id: Optional[Union[str, int]] = None
    forecast: float = Field(ge=0, le=1, description="Forecast value between 0 and 1")
    user: User
    created_at: Optional[datetime] = Field(None, alias="createdAt")
    option_id: Optional[Union[str, int]] = Field(
        None, alias="optionId", description="For multi-choice questions"
    )

    @field_validator("id", "option_id")
    @classmethod
    def convert_id_to_string(cls, v):
        """Convert integer IDs to strings"""
        return str(v) if v is not None else v

    class Config:
        populate_by_name = True
        by_alias = True  # Use aliases when serializing


class Comment(SlimBaseModel):
    """Comment on a question"""

    id: Optional[Union[str, int]] = None
    comment: str
    user: User
    created_at: Optional[datetime] = Field(None, alias="createdAt")

    @field_validator("id")
    @classmethod
    def convert_id_to_string(cls, v):
        """Convert integer IDs to strings"""
        return str(v) if v is not None else v

    class Config:
        populate_by_name = True
        by_alias = True  # Use aliases when serializing


class Question(SlimBaseModel):
    """Fatebook question model with optional fields for detailed responses"""

    # Core fields (id is optional since getQuestion doesn't return it)
    id: Optional[str] = None
    title: str
    type: Literal["BINARY", "NUMERIC", "MULTIPLE_CHOICE"] = "BINARY"
    resolved: bool = False

    # Timestamps
    created_at: datetime = Field(alias="createdAt")
    resolve_by: datetime = Field(alias="resolveBy")
    resolved_at: Optional[datetime] = Field(None, alias="resolvedAt")

    # Resolution information
    resolution: Optional[Literal["YES", "NO", "AMBIGUOUS"]] = None

    # Additional content (typically in detailed view)
    notes: Optional[str] = None

    # Related data (typically in detailed view)
    forecasts: Optional[List[Forecast]] = Field(
        default=None, description="List of forecasts on this question"
    )
    tags: Optional[List[Tag]] = Field(default=None, description="Tags associated with the question")
    comments: Optional[List[Comment]] = Field(default=None, description="Comments on the question")

    # Visibility settings (typically in detailed view)
    shared_publicly: Optional[bool] = Field(None, alias="sharedPublicly")
    unlisted: Optional[bool] = None
    hide_forecasts_until: Optional[datetime] = Field(None, alias="hideForecastsUntil")
    share_with_lists: Optional[List[str]] = Field(None, alias="shareWithLists")
    share_with_email: Optional[List[str]] = Field(None, alias="shareWithEmail")

    # Additional fields from getQuestion endpoint
    your_latest_prediction: Optional[str] = Field(None, alias="yourLatestPrediction")
    question_scores: Optional[List] = Field(None, alias="questionScores")

    class Config:
        populate_by_name = True
        by_alias = True  # Use aliases when serializing

    # Computed properties
    @property
    def forecast_count(self) -> int:
        """Number of forecasts on this question"""
        return len(self.forecasts) if self.forecasts else 0

    @property
    def status_text(self) -> str:
        """Human-readable status string"""
        if self.resolved:
            return f"✅ RESOLVED ({self.resolution})"
        return "⏳ OPEN"

    def format_short(self) -> str:
        """Format for list display"""
        tags_text = ", ".join([tag.name for tag in self.tags]) if self.tags else ""
        tags_display = f" | Tags: {tags_text}" if tags_text else ""
        forecast_text = (
            f" | {self.forecast_count} forecast{'s' if self.forecast_count != 1 else ''}"
        )

        id_text = f" | ID: {self.id}" if self.id else ""
        return f"**{self.title}**\n{self.status_text}{id_text}{forecast_text}{tags_display}"

    def format_detailed(self) -> str:
        """Format for detailed single question display"""
        lines = [
            f"**{self.title}**",
        ]
        if self.id:
            lines.append(f"ID: {self.id}")
        lines.extend(
            [
                f"Type: {self.type}",
                f"Created: {self.created_at.isoformat()}",
                f"Resolve By: {self.resolve_by.isoformat()}",
            ]
        )

        status = "✅ Resolved" if self.resolved else "⏳ Open"
        if self.resolved and self.resolved_at:
            status += f" as {self.resolution} on {self.resolved_at.isoformat()}"
        lines.append(f"Status: {status}")

        if self.notes:
            lines.append(f"Notes: {self.notes}")

        if self.forecasts:
            lines.append(f"Forecasts ({len(self.forecasts)}):")
            for forecast in self.forecasts:
                lines.append(f"  • {forecast.user.name}: {forecast.forecast:.0%}")

        if self.tags:
            tag_names = [tag.name for tag in self.tags]
            lines.append(f"Tags: {', '.join(tag_names)}")

        if self.comments:
            lines.append(f"Comments ({len(self.comments)}):")
            for comment in self.comments:
                lines.append(f"  • {comment.user.name}: {comment.comment}")

        visibility = []
        if self.shared_publicly:
            visibility.append("Public")
        if self.unlisted:
            visibility.append("Unlisted")
        if visibility:
            lines.append(f"Visibility: {', '.join(visibility)}")

        return "\n".join(lines)


class QuestionsResponse(SlimBaseModel):
    """Response from getQuestions endpoint"""

    items: List[Question]
    cursor: Optional[str] = None


class QuestionsList(SlimBaseModel):
    """List of questions for MCP responses - matches expected MCP schema"""

    result: List[Question]

    class Config:
        populate_by_name = True
        by_alias = True


class QuestionReference(SlimBaseModel):
    """Minimal question reference with id and title"""

    id: str
    title: str
