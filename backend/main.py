
import json
from ai_chat_service import chat_with_ai
from llm_service import clean_json_response, ask_llm, ask_llm_for_task
from models import AIParsedTask


from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from models import ProjectCreate, Task, Project, TaskCreate, TaskResponse
from database import SessionLocal, get_db
from models import User, UserCreate, UserResponse, AIChatRequest, AIChatResponse

from authentication import decode_access_token, hash_password


from datetime import date
from ai_assistant import parse_task

from algorithms import (
    insertion_sort,
    linear_search,
    binary_search_task,
    sort_tasks_by_priority,
    count_tasks_by_status
)
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse


# ==========================================================
# Create FastAPI Application
# ==========================================================

app = FastAPI(
    title="TaskFlow API",
    description="Task management API with authentication",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR.parent / "frontend"



# ==========================================================
# Authentication Security
# ==========================================================

security = HTTPBearer()


# ==========================================================
# Get Current Authenticated User
# ==========================================================

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get the currently authenticated user.

    Steps:
    1. Read JWT token.
    2. Decode and verify JWT.
    3. Get user ID from token.
    4. Find user in database.
    5. Return user.
    """

    # Get the token from:
    # Authorization: Bearer <token>
    token = credentials.credentials

    # Decode and verify the JWT
    try:
        payload = decode_access_token(token)

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get the user ID from the "sub" field
    user_id = payload.get("sub")

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User ID is missing from token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Open database session

    db = SessionLocal()

    try:
        # Find the user using SQLAlchemy ORM
        user = db.get(User, int(user_id))

    finally:
        # Always close the database connection
        db.close()

    # User doesn't exist
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Return authenticated user
    return user


# ==========================================================
# Basic Test Route
# ==========================================================

# BASE_DIR = Path(__file__).resolve().parent
# FRONTEND_DIR = BASE_DIR.parent / "frontend"

# app.mount(
#     "/static",
#     StaticFiles(directory=FRONTEND_DIR),
#     name="static"
# )

# @app.get("/")
# def home():
#     return FileResponse(FRONTEND_DIR / "index.html")
    # return
    # {
    #     "message": "TaskFlow API is running"
    # }

# ==========================================================
# Protected /users/me Route
# ==========================================================

@app.get("/users/me")
def get_my_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Return the profile of the currently authenticated user.
    """

    return current_user

# ==========================================================
# users Registration route
# ==========================================================

@app.post("/register",response_model=UserResponse,status_code=201)
def register_user(user: UserCreate):
    """
    Register a new user.
    """

    db = SessionLocal()

    try:

        # --------------------------------------------------
        # Check duplicate email
        # --------------------------------------------------
        existing_user = (
            db.query(User)
            .filter(User.email == user.email)
            .first()
        )

        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Email already registered."
            )

        # --------------------------------------------------
        # Create ORM User object
        # --------------------------------------------------
        new_user = User(
            name=user.name,
            email=user.email,
            password=hash_password(user.password)
        )

        # --------------------------------------------------
        # Save user
        # --------------------------------------------------
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return new_user

    finally:
        db.close()

# ==========================================================
# Add Login route
# ==========================================================


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str

# ==========================================================
# Pydantic Schemas
# =========================================================

class TaskStatusUpdate(BaseModel):
    status: str

# ==========================================================
# Authentication function
# ==========================================================

from authentication import (
    hash_password,
    verify_password,
    create_access_token
)
# ==========================================================
# User Login Route
# ==========================================================

@app.post("/login", response_model=TokenResponse)
def login_user(login: LoginRequest):
    """
    Authenticate a user and return a JWT access token.
    """

    db = SessionLocal()

    try:
        # 1. Find user by email
        user = (
            db.query(User)
            .filter(User.email == login.email)
            .first()
        )

        # 2. User does not exist
        if not user:
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )

        # 3. Verify password
        if not verify_password(login.password, user.password):
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )

        # 4. Create JWT
        access_token = create_access_token(
            data={"sub": str(user.id)}
        )

        # 5. Return token
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }

    finally:
        db.close()

# =========================================================
# Create Task
# ========================================================

@app.post("/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED
)
def create_task(task: TaskCreate,
    current_user=Depends(get_current_user)
):
    db = SessionLocal()

    try:
        # Find the project
        project = (
            db.query(Project)
            .filter(Project.id == task.project_id)
            .first()
        )

        # Project does not exist
        if not project:
            raise HTTPException(
                status_code=404,
                detail="Project not found"
            )

        # Make sure the logged-in user owns the project
        if project.owner_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to use this project"
            )

        # Create task
        new_task = Task(
            title=task.title,
            description=task.description,
            priority=task.priority,
            due_date=task.due_date,
            status=task.status,
            project_id=task.project_id
        )

        db.add(new_task)
        db.commit()
        db.refresh(new_task)

        return new_task

    finally:
        db.close()

# ==============================================
# Get All Tasks for a Project
# ==============================================
# @app.get("/tasks", response_model=list[TaskResponse])
# def get_tasks(
#     current_user=Depends(get_current_user)
# ):
#     db = SessionLocal()

#     try:
#         tasks = (
#             db.query(Task)
#             .join(Project)
#             .filter(Project.owner_id == current_user.id)
#             .all()
#         )
#         # Use our algorithm to sort tasks 
#         tasks = sort_tasks_by_priority(tasks)
#         return tasks

#     finally:
#         db.close()

# ========================================
# Add the Statistics endpoint to count tasks by status
# ========================================

@app.get("/tasks/statistics")
def get_task_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Get all tasks belonging to the current user
    tasks = (
        db.query(Task)
        .join(Project, Task.project_id == Project.id)
        .filter(Project.owner_id == current_user.id)
        .all()
    )

    # Count tasks by status
    pending = sum(1 for task in tasks if task.status == "Pending")
    in_progress = sum(1 for task in tasks if task.status == "In Progress")
    completed = sum(1 for task in tasks if task.status == "Completed")

    total = len(tasks)

    # Calculate completion percentage
    if total > 0:
        completion_percentage = round(
            (completed / total) * 100,
            2
        )
    else:
        completion_percentage = 0

    return {
        "Pending": pending,
        "In Progress": in_progress,
        "Completed": completed,
        "Total": total,
        "Completion Percentage": completion_percentage
    }



# ==========================================
# Search Tasks Using Algorithms
# ==========================================

@app.get("/tasks/search")
def search_tasks(
    title: str,
    algo: str = "linear",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Get tasks belonging to the current user's projects
    tasks = (
        db.query(Task)
        .join(Project, Task.project_id == Project.id)
        .filter(Project.owner_id == current_user.id)
        .all()
    )

    # ------------------------------------------
    # Linear Search
    # ------------------------------------------

    if algo == "linear":

        result = linear_search(
            tasks,
            title,
            key=lambda task: task.title
        )

    # ------------------------------------------
    # Binary Search
    # ------------------------------------------

    elif algo == "binary":

        # Binary Search requires the data to be sorted first.
        sorted_tasks = insertion_sort(
            tasks,
            key=lambda task: task.title
        )

        result = binary_search_task(
            sorted_tasks,
            title,
            key=lambda task: task.title
        )

    # ------------------------------------------
    # Invalid algorithm
    # ------------------------------------------

    else:
        raise HTTPException(
            status_code=400,
            detail="algo must be 'linear' or 'binary'"
        )

    # ------------------------------------------
    # No matching task
    # ------------------------------------------

    if result is None:
        return []

    # ------------------------------------------
    # Return matching task
    # ------------------------------------------

    return [result]





# ========================================
# Get one task by ID
# ========================================
@app.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task(task_id: int,
    current_user=Depends(get_current_user)
):
    db = SessionLocal()

    try:
        task = (
            db.query(Task)
            .join(Project)
            .filter(
                Task.id == task_id,
                Project.owner_id == current_user.id
            )
            .first()
        )

        if not task:
            raise HTTPException(
                status_code=404,
                detail="Task not found"
            )

        return task

    finally:
        db.close()

# ========================================
# Update a task by ID
# ========================================

@app.put("/tasks/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int,
    task: TaskCreate,
    current_user=Depends(get_current_user)
):
    db = SessionLocal()

    try:
        existing_task = (
            db.query(Task)
            .join(Project)
            .filter(
                Task.id == task_id,
                Project.owner_id == current_user.id
            )
            .first()
        )

        if not existing_task:
            raise HTTPException(
                status_code=404,
                detail="Task not found"
            )

        existing_task.title = task.title
        existing_task.description = task.description
        existing_task.priority = task.priority
        existing_task.due_date = task.due_date
        existing_task.status = task.status

        db.commit()
        db.refresh(existing_task)

        return existing_task

    finally:
        db.close()

# =======================================
# Path route to update task status
# =======================================


@app.patch("/tasks/{task_id}/status")
def update_task_status(
    task_id: int,
    status_data: TaskStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = (
        db.query(Task)
        .join(Project)
        .filter(
            Task.id == task_id,
            Project.owner_id == current_user.id
        )
        .first()
    )

    if not task:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    allowed_statuses = [
        "Pending",
        "In Progress",
        "Completed"
    ]

    if status_data.status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail="Invalid status"
        )

    task.status = status_data.status

    db.commit()
    db.refresh(task)

    return task


# ========================================
# Delete a task by ID
# ========================================

@app.delete("/tasks/{task_id}")
def delete_task(
    task_id: int,
    current_user=Depends(get_current_user)
):
    db = SessionLocal()

    try:
        task = (
            db.query(Task)
            .join(Project)
            .filter(
                Task.id == task_id,
                Project.owner_id == current_user.id
            )
            .first()
        )

        if not task:
            raise HTTPException(
                status_code=404,
                detail="Task not found"
            )

        db.delete(task)
        db.commit()

        return {
            "message": "Task deleted successfully",
            "task_id": task_id
        }

    finally:
        db.close()
# =================================
# Create Project route
# ===============================

@app.post("/projects", status_code=201)
def create_project(
    project: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    new_project = Project(
        name=project.name,
        description=project.description,
        owner_id=current_user.id
    )

    db.add(new_project)
    db.commit()
    db.refresh(new_project)

    return new_project
# ==================================
# Get Projects for the current user
# =================================

@app.get("/projects")
def get_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    projects = (
        db.query(Project)
        .filter(Project.owner_id == current_user.id)
        .all()
    )

    return projects


# ==========================================
# Get Tasks for a Specific Project
# Optional status filter
# ==========================================

@app.get("/projects/{project_id}/tasks")
def get_project_tasks(
    project_id: int,
    status: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check that the project belongs to the logged-in user
    project = (
        db.query(Project)
        .filter(
            Project.id == project_id,
            Project.owner_id == current_user.id
        )
        .first()
    )

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found"
        )

    # Start with all tasks for this project
    query = (
        db.query(Task)
        .filter(Task.project_id == project_id)
    )

    # Apply status filter if provided
    if status:
        allowed_statuses = [
            "Pending",
            "In Progress",
            "Completed"
        ]

        if status not in allowed_statuses:
            raise HTTPException(
                status_code=400,
                detail="Invalid status"
            )

        query = query.filter(Task.status == status)

    tasks = query.all()

    return tasks



# ==========================================
# Get Project by ID for the current user
# ==========================================

@app.get("/projects/{project_id}")
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = (
        db.query(Project)
        .filter(
            Project.id == project_id,
            Project.owner_id == current_user.id
        )
        .first()
    )

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found"
        )

    return project
# =========================================
# Update Project by ID for the current user
# =======================================

@app.put("/projects/{project_id}")
def update_project(
    project_id: int,
    project_data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = (
        db.query(Project)
        .filter(
            Project.id == project_id,
            Project.owner_id == current_user.id
        )
        .first()
    )

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found"
        )

    project.name = project_data.name
    project.description = project_data.description

    db.commit()
    db.refresh(project)

    return project

# =========================================
# Delete Project by ID for the current user
# ======================================

@app.delete("/projects/{project_id}")
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = (
        db.query(Project)
        .filter(
            Project.id == project_id,
            Project.owner_id == current_user.id
        )
        .first()
    )

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found"
        )

    db.delete(project)
    db.commit()

    return {
        "message": "Project deleted successfully"
    }
# =========================================
# Create Task API route 
# =======================================

@app.post("/tasks", status_code=201)
def create_task(
    task_data: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check that the project exists
    project = (
        db.query(Project)
        .filter(
            Project.id == task_data.project_id,
            Project.owner_id == current_user.id
        )
        .first()
    )

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found"
        )

    # Create the task
    new_task = Task(
        title=task_data.title,
        description=task_data.description,
        priority=task_data.priority,
        due_date=task_data.due_date,
        status=task_data.status,
        project_id=task_data.project_id
    )

    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    return new_task

# ==========================================
# Get Tasks with Sorting + Pagination
# ==========================================

@app.get("/tasks", response_model=list[TaskResponse])
def get_tasks(
    page: int = 1,
    limit: int = 10,
    sort: str = "priority",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Validate page
    if page < 1:
        raise HTTPException(
            status_code=400,
            detail="Page must be 1 or greater"
        )

    # Validate limit
    if limit < 1 or limit > 100:
        raise HTTPException(
            status_code=400,
            detail="Limit must be between 1 and 100"
        )

    # Get tasks belonging to the current user's projects
    tasks = (
        db.query(Task)
        .join(Project)
        .filter(Project.owner_id == current_user.id)
        .all()
    )

    # Sort tasks using the custom Insertion Sort algorithm
    if sort == "priority":

        priority_order = {
            "High": 1,
            "Medium": 2,
            "Low": 3
        }

        tasks = insertion_sort(
            tasks,
            key=lambda task: priority_order.get(
                task.priority,
                99
            )
        )

    elif sort == "due_date":

        tasks = insertion_sort(
            tasks,
            key=lambda task: (
                task.due_date
                if task.due_date is not None
                else date.max
            )
        )

    else:
        raise HTTPException(
            status_code=400,
            detail="sort must be 'priority' or 'due_date'"
        )

    # Pagination
    offset = (page - 1) * limit

    tasks = tasks[offset:offset + limit]

    return tasks



# ==========================
# Get Tasks for a Project API route
# ==========================

# @app.get("/tasks")
# def get_tasks(
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     tasks = (
#         db.query(Task)
#         .join(Project)
#         .filter(Project.owner_id == current_user.id)
#         .all()
#     )

#     return tasks


# ====================================
# Get Task by ID API route
# ====================================

@app.get("/tasks/{task_id}")
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = (
        db.query(Task)
        .join(Project)
        .filter(
            Task.id == task_id,
            Project.owner_id == current_user.id
        )
        .first()
    )

    if not task:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    return task
# ========================================
# Update Task by ID API route
# ========================================

@app.put("/tasks/{task_id}")
def update_task(
    task_id: int,
    task_data: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = (
        db.query(Task)
        .join(Project)
        .filter(
            Task.id == task_id,
            Project.owner_id == current_user.id
        )
        .first()
    )

    if not task:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    task.title = task_data.title
    task.description = task_data.description
    task.priority = task_data.priority
    task.due_date = task_data.due_date
    task.status = task_data.status
    task.project_id = task_data.project_id

    db.commit()
    db.refresh(task)

    return task


# ==========================================
# AI Quick-Add Task
# ==========================================

@app.post("/tasks/quick-add", response_model=TaskResponse)
def quick_add_task(
    text: str,
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # --------------------------------------
    # 1. Try online LLM first
    # --------------------------------------

    try:

        prompt = f"""
Convert this user request into a TaskFlow task.

User request:
{text}

Return ONLY valid JSON.

The JSON must contain exactly these fields:

{{
    "title": "short task title",
    "description": "task description",
    "priority": "High, Medium, or Low",
    "due_date": "YYYY-MM-DD or null"
}}

Rules:

1. priority must be exactly High, Medium, or Low.
2. If there is no deadline, due_date must be null.
3. Keep the title short.
4. Remove words such as "urgently" and deadline information from the title.
5. Do not add extra fields.
"""

        # Ask online LLM
        ai_response = ask_llm_for_task(prompt)

        print("AI response:")
        print(ai_response)

        # Remove ```json ... ``` if present
        cleaned_response = clean_json_response(ai_response)

        # Convert JSON string to Python dictionary
        parsed_data = json.loads(cleaned_response)

        # Validate using Pydantic
        validated_task = AIParsedTask.model_validate(
            parsed_data
        )

        # Convert Pydantic object to dictionary
        parsed_task = validated_task.model_dump()

        print("Online AI parsing successful.")

    except Exception as error:

        # --------------------------------------
        # Online AI failed → offline fallback
        # --------------------------------------

        print("Online AI failed:")
        print(type(error).__name__)
        print(str(error))

        try:

            parsed_task = parse_task(text)

            print("Using offline parser fallback.")

        except ValueError as fallback_error:

            raise HTTPException(
                status_code=400,
                detail=str(fallback_error)
            )

    # --------------------------------------
    # 2. Verify project ownership
    # --------------------------------------

    project = (
        db.query(Project)
        .filter(
            Project.id == project_id,
            Project.owner_id == current_user.id
        )
        .first()
    )

    if project is None:

        raise HTTPException(
            status_code=404,
            detail="Project not found"
        )

    # --------------------------------------
    # 3. Create Task
    # --------------------------------------

    new_task = Task(
        title=parsed_task["title"],
        description=parsed_task["description"],
        priority=parsed_task["priority"],
        due_date=parsed_task["due_date"],
        status="Pending",
        project_id=project_id
    )

    # --------------------------------------
    # 4. Save Task to database
    # --------------------------------------

    db.add(new_task)

    db.commit()

    db.refresh(new_task)

    return new_task
    
    # --------------------------------------
    # 2. Verify that the project belongs
    #    to the current user
    # --------------------------------------

    project = (
        db.query(Project)
        .filter(
            Project.id == project_id,
            Project.owner_id == current_user.id
        )
        .first()
    )

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found"
        )

    # --------------------------------------
    # 3. Create Task
    # --------------------------------------

    new_task = Task(
        title=parsed_task["title"],
        description=parsed_task["description"],
        priority=parsed_task["priority"],
        due_date=parsed_task["due_date"],
        status="Pending",
        project_id=project_id
    )

    # --------------------------------------
    # 4. Save Task
    # --------------------------------------

    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    return new_task

# ==========================================
# AI Conversational Chat
# ==========================================

@app.post("/ai/chat", response_model=AIChatResponse)
def ai_chat(
    request: AIChatRequest
):
    response = chat_with_ai(request.message)

    return AIChatResponse(
        response=response
    )
app.mount(
    "/",
    StaticFiles(directory=FRONTEND_DIR, html=True),
    name="frontend"
)
