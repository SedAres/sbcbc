"""Database models for LocalAcademy 0.2."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()

course_creators = db.Table(
    "course_creators",
    db.Column("course_id", db.Integer, db.ForeignKey("courses.id"), primary_key=True),
    db.Column("creator_id", db.Integer, db.ForeignKey("creators.id"), primary_key=True),
)

course_categories = db.Table(
    "course_categories",
    db.Column("course_id", db.Integer, db.ForeignKey("courses.id"), primary_key=True),
    db.Column("category_id", db.Integer, db.ForeignKey("categories.id"), primary_key=True),
    db.Column("order_index", db.Integer, default=0),
)

course_tags = db.Table(
    "course_tags",
    db.Column("course_id", db.Integer, db.ForeignKey("courses.id"), primary_key=True),
    db.Column("tag_id", db.Integer, db.ForeignKey("tags.id"), primary_key=True),
)


class TimestampMixin:
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class Creator(TimestampMixin, db.Model):
    __tablename__ = "creators"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    icon = db.Column(db.String(512))
    banner = db.Column(db.String(512))
    theme = db.Column(db.String(50))
    courses = db.relationship("Course", secondary=course_creators, back_populates="creators")

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "name": self.name, "icon": self.icon, "banner": self.banner}


class Category(TimestampMixin, db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    icon = db.Column(db.String(512))
    banner = db.Column(db.String(512))
    theme = db.Column(db.String(50))
    courses = db.relationship("Course", secondary=course_categories, back_populates="categories")

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "name": self.name, "icon": self.icon, "banner": self.banner}


class Tag(TimestampMixin, db.Model):
    __tablename__ = "tags"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    icon = db.Column(db.String(512))
    banner = db.Column(db.String(512))
    theme = db.Column(db.String(50))
    courses = db.relationship("Course", secondary=course_tags, back_populates="tags")

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "name": self.name, "icon": self.icon, "banner": self.banner}


class Course(TimestampMixin, db.Model):
    __tablename__ = "courses"

    id = db.Column(db.Integer, primary_key=True)
    display_name = db.Column(db.String(255), nullable=False)
    root_path = db.Column(db.String(1024), nullable=False, unique=True)
    is_available = db.Column(db.Boolean, default=False, nullable=False)
    drive_letter = db.Column(db.String(10))
    thumbnail = db.Column(db.String(512))
    description = db.Column(db.Text)
    theme = db.Column(db.String(50))
    total_files = db.Column(db.Integer, default=0)
    total_duration = db.Column(db.Integer, default=0)
    last_accessed = db.Column(db.DateTime(timezone=True))

    files = db.relationship("CourseFile", back_populates="course", cascade="all, delete-orphan")
    progress = db.relationship("PlaybackProgress", back_populates="course", cascade="all, delete-orphan")
    settings = db.relationship(
        "CourseSetting", back_populates="course", cascade="all, delete-orphan", uselist=False
    )
    creators = db.relationship("Creator", secondary=course_creators, back_populates="courses")
    categories = db.relationship("Category", secondary=course_categories, back_populates="courses")
    tags = db.relationship("Tag", secondary=course_tags, back_populates="courses")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "display_name": self.display_name,
            "root_path": self.root_path,
            "is_available": bool(self.is_available),
            "thumbnail": self.thumbnail,
            "description": self.description or "",
            "total_files": self.total_files or 0,
            "total_duration": self.total_duration or 0,
            "creators": [creator.to_dict() for creator in self.creators],
            "categories": [category.to_dict() for category in self.categories],
            "tags": [tag.to_dict() for tag in self.tags],
        }


class CourseFile(TimestampMixin, db.Model):
    __tablename__ = "course_files"

    id = db.Column(db.Integer, primary_key=True)
    file_hash = db.Column(db.String(16), unique=True, nullable=False, index=True)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False, index=True)
    file_path = db.Column(db.String(2048), nullable=False)
    relative_path = db.Column(db.String(1024), nullable=False)
    file_name = db.Column(db.String(512), nullable=False)
    display_name = db.Column(db.String(512))
    file_type = db.Column(db.String(24), nullable=False)
    file_extension = db.Column(db.String(16), nullable=False)
    file_size = db.Column(db.BigInteger, default=0)
    duration = db.Column(db.Integer)
    thumbnail = db.Column(db.String(512))
    video_quality = db.Column(db.String(20))
    parent_folder = db.Column(db.String(1024))
    order_index = db.Column(db.Integer, default=0)

    course = db.relationship("Course", back_populates="files")
    progress = db.relationship("PlaybackProgress", back_populates="file", cascade="all, delete-orphan")
    notes = db.relationship("Note", back_populates="file", cascade="all, delete-orphan")
    bookmarks = db.relationship("Bookmark", back_populates="file", cascade="all, delete-orphan")

    @property
    def title(self) -> str:
        return self.display_name or self.file_name

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "file_hash": self.file_hash,
            "course_id": self.course_id,
            "relative_path": self.relative_path,
            "file_name": self.file_name,
            "display_name": self.title,
            "file_type": self.file_type,
            "file_extension": self.file_extension,
            "file_size": self.file_size or 0,
            "duration": self.duration or 0,
            "thumbnail": self.thumbnail,
            "video_quality": self.video_quality,
            "parent_folder": self.parent_folder,
            "order_index": self.order_index or 0,
        }


class PlaybackProgress(TimestampMixin, db.Model):
    __tablename__ = "playback_progress"

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False, index=True)
    file_id = db.Column(db.Integer, db.ForeignKey("course_files.id"), nullable=False, index=True)
    current_time = db.Column(db.Float, default=0.0, nullable=False)
    completed = db.Column(db.Boolean, default=False, nullable=False)
    last_watched = db.Column(
        db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc), index=True,
    )

    course = db.relationship("Course", back_populates="progress")
    file = db.relationship("CourseFile", back_populates="progress")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "file_id": self.file_id,
            "current_time": self.current_time or 0,
            "completed": bool(self.completed),
            "last_watched": self.last_watched.isoformat() if self.last_watched else None,
        }


class Note(TimestampMixin, db.Model):
    __tablename__ = "notes"

    id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey("course_files.id"), nullable=False, index=True)
    timestamp = db.Column(db.Float)
    content = db.Column(db.Text, nullable=False)
    updated_at = db.Column(
        db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    file = db.relationship("CourseFile", back_populates="notes")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "file_id": self.file_id,
            "timestamp": self.timestamp,
            "content": self.content,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Bookmark(TimestampMixin, db.Model):
    __tablename__ = "bookmarks"

    id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey("course_files.id"), nullable=False, index=True)
    timestamp = db.Column(db.Float, nullable=False)
    label = db.Column(db.String(255))
    file = db.relationship("CourseFile", back_populates="bookmarks")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "file_id": self.file_id,
            "timestamp": self.timestamp,
            "label": self.label,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Setting(db.Model):
    __tablename__ = "settings"

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text)
    value_type = db.Column(db.String(20), default="string")

    def get_value(self) -> Any:
        if self.value is None:
            return None
        kind = self.value_type or "string"
        if kind == "int":
            return int(self.value)
        if kind == "float":
            return float(self.value)
        if kind == "bool":
            return self.value.casefold() in {"true", "1", "yes", "on"}
        if kind == "json":
            return json.loads(self.value)
        return self.value

    def set_value(self, value: Any) -> None:
        if isinstance(value, bool):
            self.value_type, self.value = "bool", "true" if value else "false"
        elif isinstance(value, int):
            self.value_type, self.value = "int", str(value)
        elif isinstance(value, float):
            self.value_type, self.value = "float", str(value)
        elif isinstance(value, (dict, list, tuple)):
            self.value_type, self.value = "json", json.dumps(value)
        else:
            self.value_type, self.value = "string", str(value)

    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        row = cls.query.filter_by(key=key).first()
        return row.get_value() if row else default

    @classmethod
    def set_many(cls, values: dict[str, Any]) -> None:
        for key, value in values.items():
            row = cls.query.filter_by(key=key).first()
            if row is None:
                row = cls(key=key)
                db.session.add(row)
            row.set_value(value)
        db.session.commit()


class CourseSetting(db.Model):
    """Nullable overrides; NULL means use the global preference."""

    __tablename__ = "course_settings"

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False, unique=True)
    playback_speed = db.Column(db.Float)
    skip_silence_enabled = db.Column(db.Boolean)
    skip_silence_db_threshold = db.Column(db.Integer)
    skip_silence_min_duration = db.Column(db.Float)
    skip_silence_speed = db.Column(db.Float)
    subtitle_enabled = db.Column(db.Boolean)
    rtl_enabled = db.Column(db.Boolean)
    course = db.relationship("Course", back_populates="settings")

    def to_dict(self) -> dict[str, Any]:
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
            if column.name not in {"id", "course_id"}
        }


class SubtitleTrack(TimestampMixin, db.Model):
    """A caption file uploaded directly to one lesson (rather than stored beside it)."""

    __tablename__ = "subtitle_tracks"

    id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey("course_files.id", ondelete="CASCADE"), nullable=False, index=True)
    label = db.Column(db.String(120), nullable=False)
    language = db.Column(db.String(16), default="und")
    original_name = db.Column(db.String(255))
    webvtt_content = db.Column(db.Text, nullable=False)
    file = db.relationship("CourseFile", backref=db.backref("attached_subtitles", cascade="all, delete-orphan"))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "file_id": self.file_id,
            "label": self.label,
            "language": self.language,
            "original_name": self.original_name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


DEFAULT_SETTINGS: dict[str, Any] = {
    "playback_speed": 1.0,
    "skip_silence_enabled": False,
    "skip_silence_db_threshold": -42,
    "skip_silence_min_duration": 0.65,
    "skip_silence_speed": 8.0,
    "subtitle_enabled": True,
    "rtl_enabled": False,
    "theater_mode": False,
    "auto_advance": True,
    "timestamp_template": "[{HH}:{MM}:{SS}]({url})",
    "hotkeys": {
        "play_pause": "num_5",
        "rewind_5s": "num_4",
        "forward_5s": "num_6",
        "prev_file": "num_1",
        "next_file": "num_3",
        "volume_up": "num_8",
        "volume_down": "num_2",
        "speed_up": "num_9",
        "speed_down": "num_7",
        "toggle_subtitles": "num_0",
    },
}

SETTING_TYPES: dict[str, type] = {
    "playback_speed": float,
    "skip_silence_enabled": bool,
    "skip_silence_db_threshold": int,
    "skip_silence_min_duration": float,
    "skip_silence_speed": float,
    "subtitle_enabled": bool,
    "rtl_enabled": bool,
    "theater_mode": bool,
    "auto_advance": bool,
    "timestamp_template": str,
}

COURSE_SETTING_TYPES: dict[str, type] = {
    key: kind
    for key, kind in SETTING_TYPES.items()
    if key in {
        "playback_speed",
        "skip_silence_enabled",
        "skip_silence_db_threshold",
        "skip_silence_min_duration",
        "skip_silence_speed",
        "subtitle_enabled",
        "rtl_enabled",
    }
}
