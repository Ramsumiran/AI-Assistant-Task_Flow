from datetime import date
from sqlalchemy import Column, Date, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from database import Base, engine
from enum import Enum

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    password = Column(String(255),nullable=False)
    
    # One User → Many Projects
    projects = relationship("Project", back_populates="owner")


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)

    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Many Projects → One User
    owner = relationship("User", back_populates="projects")

    # One Project → Many Tasks
    tasks = relationship("Task", back_populates="project")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(String(500))
    priority = Column(String(20), nullable=False)
    due_date = Column(String(100))
    status = Column(String(20), default="Pending")

    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)

    # Many Tasks → One Project
    project = relationship("Project", back_populates="tasks")




print("Creating database tables...")

Base.metadata.create_all(bind=engine)

print("✅ Database tables created successfully!")