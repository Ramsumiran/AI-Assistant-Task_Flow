from datetime import date
"""
==========================================================
models.py

Contains:
1. SQLAlchemy ORM Models
2. Pydantic Schemas
3. Custom Email Validation
4. Database Table Creation
==========================================================
"""

# ==========================================================
# Imports
# ==========================================================

from datetime import date

from pydantic import BaseModel, ConfigDict, field_validator
from sqlalchemy import Column, Date, ForeignKey, Integer, String

from sqlalchemy.orm import relationship

from database import Base, engine

from enum import Enum


# ==========================================================
# Email Validation Function
# ==========================================================

def validate_allowed_email(email: str, allowed_domains: list = None) -> str:
    """
    Validate email without using regular expressions.
    """

    # Default allowed domains
    if allowed_domains is None:
        allowed_domains = [
            "gmail.com",
            "outlook.com",
            "yahoo.com",
            "yahoomail.com"
        ]

    # Check datatype
    if not isinstance(email, str):
        raise ValueError("Email must be a string.")

    # Remove spaces and convert to lowercase
    email = email.strip().lower()

    # Must contain exactly one '@'
    if (
        email.count("@") != 1
        or email.startswith("@")
        or email.endswith("@")
    ):
        raise ValueError("Invalid email format.")

    # Split username and domain
    local_part, domain = email.rsplit("@", 1)

    # Username cannot be empty
    if not local_part:
        raise ValueError("Invalid username.")

    # Domain validation
    if (
        "." not in domain
        or domain.startswith(".")
        or domain.endswith(".")
    ):
        raise ValueError("Invalid email domain.")

    # Allowed domain check
    if domain not in allowed_domains:
        raise ValueError(
            f"Only these email domains are allowed: "
            f"{', '.join(allowed_domains)}"
        )

    return email

# ==========================================================
# Task Priority
# ==========================================================

class TaskPriority(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


# ==========================================================
# Task Status
# ==========================================================

class TaskStatus(str, Enum):
    PENDING = "Pending"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"

# ==========================================================
# SQLAlchemy ORM Models
# ==========================================================

class User(Base):

    __tablename__ = "users"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    name = Column(
        String(100),
        nullable=False
    )

    email = Column(
        String(150),
        unique=True,
        nullable=False
    )

    password = Column(
        String(255),
        nullable=False
    )

    projects = relationship(
        "Project",
        back_populates="owner",
        cascade="all, delete-orphan"
    )


class Project(Base):

    __tablename__ = "projects"

    id = Column(Integer,primary_key=True,index=True)
    name = Column(String(150),nullable=False)
    description = Column(String(255),nullable=True)
    owner_id = Column(Integer,ForeignKey("users.id"),nullable=False)

    owner = relationship(
        "User",
        back_populates="projects"
    )

    tasks = relationship(
        "Task",
        back_populates="project",
        cascade="all, delete-orphan"
    )


class Task(Base):

    __tablename__ = "tasks"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    title = Column(
        String(200),
        nullable=False
    )

    description = Column(
        String(500),
        nullable=True
    )

    priority = Column(
        String(20),
        nullable=False
    )

    due_date = Column(
        Date,
        nullable=True
    )

    status = Column(
        String(20),
        default="Pending",
        nullable=False
    )

    project_id = Column(
        Integer,
        ForeignKey("projects.id"),
        nullable=False
    )

    project = relationship(
        "Project",
        back_populates="tasks"
    )


# ==========================================================
# Pydantic Schemas
# ==========================================================

# -----------------------
# User Schemas
# -----------------------

class UserCreate(BaseModel):

    name: str
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def check_email(cls, value: str):
        return validate_allowed_email(value)


class UserLogin(BaseModel):

    email: str
    password: str

    @field_validator("email")
    @classmethod
    def check_email(cls, value: str):
        return validate_allowed_email(value)


class UserResponse(BaseModel):

    id: int
    name: str
    email: str

    model_config = ConfigDict(
        from_attributes=True
    )


# -----------------------
# Project Schemas
# -----------------------

class ProjectCreate(BaseModel):

    name: str
    description: str | None = None
    # owner_id: int


class ProjectResponse(BaseModel):

    id: int
    name: str
    description: str | None = None
    owner_id: int

    model_config = ConfigDict(
        from_attributes=True
    )


# -----------------------
# Task Schemas
# -----------------------

class TaskCreate(BaseModel):

    title: str
    description: str | None = None
    priority: TaskPriority
    due_date: date | None = None
    status: TaskStatus = TaskStatus.PENDING
    project_id: int



class TaskResponse(BaseModel):

    id: int
    title: str
    description: str | None
    priority: TaskPriority
    due_date: date | None
    status: TaskStatus
    project_id: int

    model_config = ConfigDict(
        from_attributes=True
    )

# ==========================================================
# AI Parse Request Schema
# ==========================================================

class AIParsedTask(BaseModel):
    title: str
    description: str
    priority: str
    due_date: date | None = None

# ==========================================================
# AI chat message schema
# ==========================================================
class AIChatRequest(BaseModel):
    message: str


class AIChatResponse(BaseModel):
    response: str
    
# ==========================================================
# Create Database Tables
# ==========================================================

if __name__ == "__main__":

    print("Creating database tables...")

    Base.metadata.create_all(bind=engine)

    print("✅ Database tables created successfully!")