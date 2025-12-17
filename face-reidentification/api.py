import os
import cv2
import numpy as np
import warnings
import csv
import io
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Depends, Header, Query
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
from pydantic import BaseModel, EmailStr
import uuid
import jwt
from datetime import datetime, timedelta

# Suppress warnings
warnings.filterwarnings("ignore")
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

# Import your project's modules
from models import SCRFD, ArcFace
from database import FaceDatabase, UserDatabase
from agent.AnalysisAgent import AnalysisAgent
from agent.Utility import get_student_attendance_graph_data

# --- Configuration ---
# Get the absolute path of the directory where this script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DET_WEIGHT = os.path.join(BASE_DIR, "weights", "det_500m.onnx")
REC_WEIGHT = os.path.join(BASE_DIR, "weights", "w600k_mbf.onnx")
DB_PATH = os.path.join(BASE_DIR, "database", "face_database")
ATTENDANCE_DB_PATH = os.path.join(BASE_DIR, "database", "attendance.db")
AGENT_DB_PATH = os.path.join(BASE_DIR, "agent", "attendance.db")  # Agent database with attendance data
UNREGISTERED_FACES_PATH = os.path.join(BASE_DIR, "database", "unregistered_faces")
SIMILARITY_THRESH = 0.4
CONFIDENCE_THRESH = 0.5

# JWT Configuration
JWT_SECRET = os.environ.get("JWT_SECRET", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24 * 7  # 7 days


# --- Helper Functions ---
def get_agent_student_id_by_name(student_name: str) -> str:
    """
    Find student ID in agent database by matching student name.
    This is more reliable than ID mapping since names are consistent across databases.
    """
    import sqlite3
    try:
        agent_conn = sqlite3.connect(AGENT_DB_PATH)
        cursor = agent_conn.cursor()
        
        # Try to find student by name (could be in 'name' or 'first_name'+'last_name')
        cursor.execute("""
            SELECT id FROM students 
            WHERE name = ? 
            LIMIT 1
        """, (student_name,))
        
        result = cursor.fetchone()
        agent_conn.close()
        
        if result:
            return str(result[0])
        
        # If not found, return None (will cause empty data)
        return None
    except Exception as e:
        print(f"Error mapping student name to agent ID: {e}")
        return None


def get_agent_student_id(main_student_id: str) -> str:
    """
    Get agent database student ID from main database student ID.
    Steps:
    1. Get student info from main DB
    2. Extract student name
    3. Find matching student in agent DB by name
    """
    try:
        # Get student from main database
        student = app.state.user_db.get_student_by_id(main_student_id)
        if not student:
            return None
        
        # Construct full name
        student_full_name = f"{student.get('first_name', '')} {student.get('last_name', '')}".strip()
        if not student_full_name:
            student_full_name = student.get('name', '')
        
        # Find in agent DB
        return get_agent_student_id_by_name(student_full_name)
    except Exception as e:
        print(f"Error getting agent student ID: {e}")
        return None


# --- Pydantic Models for User API ---
class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    first_name: str
    last_name: str
    dob: Optional[str] = None
    role: Optional[str] = "student"

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    password: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    dob: Optional[str] = None

class UserRoleUpdate(BaseModel):
    role: str

class ParentStudentLink(BaseModel):
    parent_id: int
    student_id: str

class TokenResponse(BaseModel):
    token: str
    user: dict


# --- JWT Helper Functions ---
def create_jwt_token(user_data: dict) -> str:
    """Create a JWT token for a user"""
    payload = {
        "id": user_data["id"],
        "email": user_data["email"],
        "role": user_data["role"],
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_jwt_token(token: str) -> Optional[dict]:
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

async def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    """Dependency to get current user from JWT token"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header format")
    
    token = authorization[7:]  # Remove "Bearer " prefix
    payload = verify_jwt_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return payload

async def get_admin_user(current_user: dict = Depends(get_current_user)) -> dict:
    """Dependency to ensure current user is admin"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


# --- Lifespan Management (Modern Syntax) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load models and database when the application starts."""
    try:
        # Startup: Load models and database
        app.state.detector = SCRFD(DET_WEIGHT, input_size=(640, 640), conf_thres=CONFIDENCE_THRESH)
        app.state.recognizer = ArcFace(REC_WEIGHT)
        app.state.face_db = FaceDatabase(db_path=DB_PATH)
        app.state.user_db = UserDatabase(db_path=ATTENDANCE_DB_PATH)
        
        if not app.state.face_db.load():
            print("Could not load existing face database, a new one will be created upon face addition.")
        
        # Ensure the directory for unregistered faces exists
        os.makedirs(UNREGISTERED_FACES_PATH, exist_ok=True)
        
        # Load existing unregistered faces into memory
        app.state.unregistered_embeddings = {}
        for filename in os.listdir(UNREGISTERED_FACES_PATH):
            if filename.endswith(".jpg"):
                face_id = os.path.splitext(filename)[0]
                image_path = os.path.join(UNREGISTERED_FACES_PATH, filename)
                frame = cv2.imread(image_path)
                if frame is not None:
                    _, kpss = app.state.detector.detect(frame, max_num=1)
                    if len(kpss) > 0:
                        embedding = app.state.recognizer.get_embedding(frame, kpss[0], normalized=True)
                        app.state.unregistered_embeddings[face_id] = embedding
        
        print(f"Models and database loaded successfully. {len(app.state.unregistered_embeddings)} unregistered faces loaded.")
        print(f"User database initialized at {ATTENDANCE_DB_PATH}")
        
        yield  # Application runs here
        
        # Shutdown: Cleanup resources
        print("Shutting down and cleaning up resources...")
        
    except Exception as e:
        print(f"Error during startup: {e}")
        raise RuntimeError(f"Failed to initialize models or database: {e}")


# --- FastAPI App Initialization ---
app = FastAPI(title="Face Recognition API", lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Helper Functions ---
async def process_image(image_bytes: bytes) -> np.ndarray:
    """
    Decodes image bytes and prepares it for processing.
    """
    try:
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Could not decode image.")
        return img
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Image processing failed: {str(e)}")


def validate_models_loaded(app: FastAPI) -> None:
    """Validates that all required models and database are loaded."""
    if not hasattr(app.state, 'detector') or not hasattr(app.state, 'recognizer') or not hasattr(app.state, 'face_db'):
        raise HTTPException(status_code=503, detail="Models or database not loaded. The service is not ready.")


# --- API Endpoints ---
@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "message": "Face Recognition API is running"}


@app.post("/recognize")
async def recognize_face(file: UploadFile = File(...)):
    """
    Receives an image, performs face detection and recognition,
    and returns the name of the recognized person.
    """
    validate_models_loaded(app)
    
    try:
        # Read and process the uploaded image
        image_bytes = await file.read()
        frame = await process_image(image_bytes)
        
        # Detect faces
        bboxes, kpss = app.state.detector.detect(frame, max_num=1)
        
        if len(kpss) == 0:
            raise HTTPException(status_code=404, detail="No face detected in the image.")
        
        # Get embedding for the first detected face
        embedding = app.state.recognizer.get_embedding(frame, kpss[0], normalized=True)
        
        # Search for the face in the database
        results = app.state.face_db.search(embedding, SIMILARITY_THRESH)
        
        # Check if a known face was found
        if results and results[0] != "Unknown":
            name, similarity = results
            return {"student_id": name, "similarity": float(similarity)}
        else:
            raise HTTPException(status_code=404, detail="Face not recognized or similarity too low.")
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail="An internal server error occurred during face recognition.")


@app.post("/add_face")
async def add_face(student_id: str = Form(...), file: UploadFile = File(...)):
    """
    Receives an image and a student ID, detects the face,
    and adds the face embedding to the database.
    """
    validate_models_loaded(app)
    
    try:
        # Read and process the uploaded image
        image_bytes = await file.read()
        frame = await process_image(image_bytes)
        
        # Detect faces
        bboxes, kpss = app.state.detector.detect(frame, max_num=1)
        
        if len(kpss) == 0:
            raise HTTPException(status_code=404, detail="No face detected in the image.")
        
        # Get embedding for the first detected face
        embedding = app.state.recognizer.get_embedding(frame, kpss[0], normalized=True)
        
        # Add the face to the database
        app.state.face_db.add_face(embedding, student_id)
        app.state.face_db.save()
        
        return {"message": f"Face for student {student_id} added successfully."}
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail="An internal server error occurred during face addition.")


@app.post("/register_face")
async def register_face(class_id: int = Form(...), file: UploadFile = File(...)):
    """
    Receives an image, saves it, and returns a unique ID for the face.
    This face is considered "unregistered" until an admin assigns a student ID to it.
    """
    if not hasattr(app.state, 'detector'):
        raise HTTPException(status_code=503, detail="Detector not loaded. The service is not ready.")
    
    try:
        image_bytes = await file.read()
        frame = await process_image(image_bytes)
        
        # Detect faces to ensure there is a face in the image
        bboxes, kpss = app.state.detector.detect(frame, max_num=1)
        if len(kpss) == 0:
            raise HTTPException(status_code=404, detail="No face detected in the image.")
        
        # Check if the face already exists in the main database
        new_embedding = app.state.recognizer.get_embedding(frame, kpss[0], normalized=True)
        results = app.state.face_db.search(new_embedding, SIMILARITY_THRESH)
        
        if results and results[0] != "Unknown":
            student_id, similarity = results
            raise HTTPException(
                status_code=409,
                detail=f"Face already registered to student {student_id}."
            )
        
        # Check against other unregistered faces (in-memory) with higher threshold
        # to reduce false positives
        PENDING_SIMILARITY_THRESH = 0.6  # Higher threshold for pending faces
        for face_id, existing_embedding in list(app.state.unregistered_embeddings.items()):
            similarity = np.dot(new_embedding, existing_embedding)
            if similarity > PENDING_SIMILARITY_THRESH:
                # Check if the file still exists, if not remove from cache
                image_path = os.path.join(UNREGISTERED_FACES_PATH, f"{face_id}.jpg")
                if not os.path.exists(image_path):
                    del app.state.unregistered_embeddings[face_id]
                    # Also remove from database if exists
                    app.state.user_db.delete_unregistered_face(face_id)
                    continue
                raise HTTPException(
                    status_code=409,
                    detail=f"This face is already pending registration (similarity: {similarity:.2f})."
                )
        
        # Generate a unique ID for this face image
        face_id = str(uuid.uuid4())
        image_path = os.path.join(UNREGISTERED_FACES_PATH, f"{face_id}.jpg")
        
        # Save the original image
        cv2.imwrite(image_path, frame)
        
        # Add to in-memory cache
        app.state.unregistered_embeddings[face_id] = new_embedding
        
        # Store in database with class_id
        app.state.user_db.create_unregistered_face(face_id, class_id)
        
        return {"face_id": face_id, "message": "Face captured successfully.", "class_id": class_id}
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"An unexpected error occurred during face registration: {e}")
        raise HTTPException(status_code=500, detail="An internal server error occurred during face registration.")


@app.post("/commit_face")
async def commit_face(student_id: str = Form(...), face_id: str = Form(...)):
    """
    Commits a previously captured face to the main database with a student ID.
    """
    validate_models_loaded(app)
    
    # Check if the face_id exists in our cache
    if face_id not in app.state.unregistered_embeddings:
        raise HTTPException(
            status_code=404,
            detail=f"Unregistered face with ID {face_id} not found in memory cache."
        )
    
    try:
        # Use the pre-computed embedding directly from cache
        embedding = app.state.unregistered_embeddings[face_id]
        
        # Add the face to the main database
        app.state.face_db.add_face(embedding, student_id)
        app.state.face_db.save()
        
        # Update student's face_registered status
        app.state.user_db.update_student_face_registered(student_id, True)
        
        # Clean up the unregistered face image and cache entry
        image_path = os.path.join(UNREGISTERED_FACES_PATH, f"{face_id}.jpg")
        if os.path.exists(image_path):
            os.remove(image_path)
        
        del app.state.unregistered_embeddings[face_id]
        
        # Remove from database
        app.state.user_db.delete_unregistered_face(face_id)
        
        return {"message": f"Face for student {student_id} has been successfully registered."}
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"An error occurred during face commit: {e}")
        raise HTTPException(
            status_code=500,
            detail="An internal server error occurred during face registration."
        )


@app.delete("/delete_face/{student_id}")
async def delete_face(student_id: str):
    """
    Deletes all face embeddings associated with a student ID from the database.
    """
    if not hasattr(app.state, 'face_db'):
        raise HTTPException(status_code=503, detail="Database not loaded.")
    
    try:
        num_deleted = app.state.face_db.delete_face(student_id)
        app.state.face_db.save()
        return {
            "message": f"Successfully processed deletion for student {student_id}. {num_deleted} face(s) were removed."
        }
    
    except Exception as e:
        print(f"An error occurred during face deletion: {e}")
        raise HTTPException(status_code=500, detail="An internal server error occurred during face deletion.")


@app.delete("/unregister_face/{face_id}")
async def unregister_face(face_id: str):
    """
    Deletes a previously captured unregistered face image.
    """
    image_path = os.path.join(UNREGISTERED_FACES_PATH, f"{face_id}.jpg")
    
    try:
        # Remove from file system
        if os.path.exists(image_path):
            os.remove(image_path)
        
        # Remove from memory cache
        if hasattr(app.state, 'unregistered_embeddings') and face_id in app.state.unregistered_embeddings:
            del app.state.unregistered_embeddings[face_id]
        
        # Remove from database
        if hasattr(app.state, 'user_db'):
            app.state.user_db.delete_unregistered_face(face_id)
        
        return {"message": f"Unregistered face {face_id} deleted successfully."}
    except Exception as e:
        print(f"An error occurred during unregistered face deletion: {e}")
        raise HTTPException(status_code=500, detail="An internal server error occurred during face deletion.")


@app.get("/unregistered_face/{face_id}")
async def get_unregistered_face(face_id: str):
    """
    Serves the image of an unregistered face.
    """
    image_path = os.path.join(UNREGISTERED_FACES_PATH, f"{face_id}.jpg")
    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="Image not found.")
    
    return FileResponse(image_path, media_type="image/jpeg")


@app.get("/unregistered_faces")
async def get_all_unregistered_faces():
    """
    Get all unregistered faces from database.
    """
    faces = app.state.user_db.get_all_unregistered_faces()
    return {"faces": faces}


@app.get("/unregistered_faces/class/{class_id}")
async def get_unregistered_faces_by_class(class_id: int):
    """
    Get all unregistered faces for a specific class.
    """
    faces = app.state.user_db.get_unregistered_faces_by_class(class_id)
    return {"faces": faces}


# ==================== User Authentication Endpoints ====================

@app.post("/api/auth/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    """
    Authenticate user with email and password.
    Returns JWT token and user info.
    """
    user = app.state.user_db.login(credentials.email, credentials.password)
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    
    token = create_jwt_token(user)
    
    return {"token": token, "user": user}


@app.post("/api/users", status_code=201)
async def create_user(user_data: UserCreate):
    """
    Create a new user account.
    """
    user = app.state.user_db.create_user(
        email=user_data.email,
        username=user_data.username,
        password=user_data.password,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        dob=user_data.dob,
        role=user_data.role or "student"
    )
    
    if not user:
        raise HTTPException(status_code=409, detail="A user with this email or username already exists.")
    
    return user


@app.get("/api/users/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """
    Get the current authenticated user's info.
    """
    user = app.state.user_db.get_user_by_id(current_user["id"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    
    return {"user": user}


@app.get("/api/users")
async def get_all_users(current_user: dict = Depends(get_admin_user)):
    """
    Get all users (admin only).
    """
    users = app.state.user_db.get_all_users()
    return {"users": users}


@app.get("/api/users/{user_id}")
async def get_user_by_id(user_id: int, current_user: dict = Depends(get_current_user)):
    """
    Get user by ID.
    """
    # Users can only view their own profile unless they're admin
    if current_user["id"] != user_id and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Access denied.")
    
    user = app.state.user_db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    
    return user


@app.put("/api/users/{user_id}")
async def update_user(user_id: int, user_data: UserUpdate, current_user: dict = Depends(get_current_user)):
    """
    Update user by ID.
    """
    # Users can only update their own profile unless they're admin
    if current_user["id"] != user_id and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Access denied.")
    
    user = app.state.user_db.update_user(
        user_id=user_id,
        email=user_data.email,
        username=user_data.username,
        password=user_data.password,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        dob=user_data.dob
    )
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    
    return user


@app.patch("/api/users/{user_id}/role")
async def update_user_role(user_id: int, role_data: UserRoleUpdate, current_user: dict = Depends(get_admin_user)):
    """
    Update user role (admin only).
    """
    user = app.state.user_db.update_user_role(user_id, role_data.role)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found or invalid role.")
    
    return user


@app.delete("/api/users/{user_id}")
async def delete_user(user_id: int, current_user: dict = Depends(get_admin_user)):
    """
    Delete user by ID (admin only).
    """
    success = app.state.user_db.delete_user(user_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="User not found.")
    
    return {"message": f"User with ID {user_id} successfully deleted."}


# ==================== Users by Role Endpoints ====================

@app.get("/api/users/role/{role}")
async def get_users_by_role(role: str, current_user: dict = Depends(get_admin_user)):
    """
    Get all users with a specific role (admin only).
    """
    valid_roles = ["admin", "teacher", "parent", "student"]
    if role not in valid_roles:
        raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {valid_roles}")
    
    users = app.state.user_db.get_users_by_role(role)
    return {"users": users}


# ==================== Parent-Student Relationship Endpoints ====================

@app.post("/api/users/parent-student/link")
async def link_parent_to_student(link_data: ParentStudentLink, current_user: dict = Depends(get_admin_user)):
    """
    Link a parent to a student (admin only).
    """
    success = app.state.user_db.link_parent_to_student(link_data.parent_id, link_data.student_id)
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to link parent to student. Check if both exist.")
    
    return {"message": "Parent successfully linked to student."}


@app.delete("/api/users/parent-student/link")
async def unlink_parent_from_student(link_data: ParentStudentLink, current_user: dict = Depends(get_admin_user)):
    """
    Remove parent-student link (admin only).
    """
    success = app.state.user_db.unlink_parent_from_student(link_data.parent_id, link_data.student_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Link not found.")
    
    return {"message": "Parent-student link removed."}


@app.get("/api/users/{parent_id}/students")
async def get_students_for_parent(parent_id: int, current_user: dict = Depends(get_current_user)):
    """
    Get all students linked to a parent.
    """
    # Parents can only view their own students, admins can view any
    if current_user["id"] != parent_id and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Access denied.")
    
    students = app.state.user_db.get_students_for_parent(parent_id)
    return {"students": students}


@app.get("/api/users/parent-student/links")
async def get_all_parent_student_links(current_user: dict = Depends(get_admin_user)):
    """
    Get all parent-student relationships (admin only).
    """
    links = app.state.user_db.get_all_parent_student_links()
    return {"links": links}


# ==================== Attendance Export Endpoints ====================

@app.get("/api/attendance/export")
async def export_attendance(
    class_id: int = Query(..., description="Class ID"),
    date: str = Query(..., description="Date in YYYY-MM-DD format"),
    format: str = Query("csv", description="Export format: csv or excel"),
    current_user: dict = Depends(get_current_user)
):
    """
    Export attendance data for a class on a specific date as CSV or Excel.
    Uses AnalysisAgent for consistent export logic.
    """
    # Only teachers and admins can export
    if current_user["role"] not in ["admin", "teacher"]:
        raise HTTPException(status_code=403, detail="Access denied.")
    
    try:
        result = AnalysisAgent.export_class_attendance(class_id, date, format)
        
        if not result:
            raise HTTPException(status_code=500, detail="Failed to generate export.")
        
        content = result['content']
        filename = result['filename']
        
        if format == 'excel':
            return StreamingResponse(
                io.BytesIO(content),
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        else:
            # CSV format - encode with BOM for Excel compatibility
            return StreamingResponse(
                io.BytesIO(content.encode('utf-8-sig')),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error exporting attendance: {e}")
        raise HTTPException(status_code=500, detail="Failed to export attendance data.")


@app.get("/api/attendance/export-report")
async def export_student_report(
    class_id: Optional[int] = Query(None, description="Class ID to filter students"),
    student_id: Optional[str] = Query(None, description="Specific student ID"),
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format (optional, for total summary leave empty)"),
    format: str = Query("csv", description="Export format: csv or excel"),
    current_user: dict = Depends(get_current_user)
):
    """
    Export student attendance report as CSV or Excel.
    Can filter by class_id, student_id, and/or date.
    If no date is provided, returns total summary across all dates.
    """
    # Only teachers and admins can export
    if current_user["role"] not in ["admin", "teacher"]:
        raise HTTPException(status_code=403, detail="Access denied.")
    
    try:
        result = AnalysisAgent.export_student_report(
            student_id=student_id,
            date=date,
            format=format,
            class_id=class_id
        )
        
        if not result:
            raise HTTPException(status_code=500, detail="Failed to generate report.")
        
        content = result['content']
        filename = result['filename']
        
        if format == 'excel':
            return StreamingResponse(
                io.BytesIO(content),
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        else:
            # CSV format - encode with BOM for Excel compatibility
            return StreamingResponse(
                io.BytesIO(content.encode('utf-8-sig')),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error exporting student report: {e}")
        raise HTTPException(status_code=500, detail="Failed to export student report.")

# ==================== Student Profile Endpoints ====================
@app.get("/api/students/{student_id}/profile")
async def get_student_profile(
    student_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get complete student profile with basic info and statistics.
    Access control: Admin can view all, Teacher can view their students,
    Parent can view their children, Student can view themselves.
    """
    # Check permissions
    user_role = current_user.get("role")
    user_id = current_user.get("id")
    
    # Get student info
    student = app.state.user_db.get_student_by_id(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Permission check
    if user_role == "student":
        # Students can only view their own profile
        # Assuming student_id matches user_id for student role
        # You may need to adjust this logic based on your user-student relationship
        pass  # Add your logic here
    elif user_role == "parent":
        # Check if this student is linked to this parent
        parent_students = app.state.user_db.get_students_for_parent(user_id)
        student_ids = [s['id'] for s in parent_students]
        if student_id not in student_ids:
            raise HTTPException(status_code=403, detail="Access denied")
    elif user_role == "teacher":
        # Check if student is in teacher's class
        # You may need to implement this check
        pass  # Add your logic here
    # Admin has full access, no check needed
    
    # Determine which database to use for attendance statistics
    # STU-prefixed IDs use agent database, others use main database
    use_agent_db = student_id.startswith("STU")
    
    if use_agent_db:
        # Get student name to map to agent database
        student_full_name = f"{student.get('first_name', '')} {student.get('last_name', '')}".strip()
        if not student_full_name:
            student_full_name = student.get('name', '')
        
        # Find corresponding student ID in agent database by name
        agent_student_id = get_agent_student_id_by_name(student_full_name)
        
        if not agent_student_id:
            # No matching student in agent DB, return empty statistics
            return {
                "student": student,
                "statistics": {
                    'total_sessions': 0,
                    'on_time_count': 0,
                    'late_count': 0,
                    'absent_count': 0,
                    'excused_count': 0,
                    'attendance_rate': 0
                }
            }
        
        # Get attendance statistics from AGENT database
        import sqlite3
        agent_conn = sqlite3.connect(AGENT_DB_PATH)
        cursor = agent_conn.cursor()
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total_sessions,
                SUM(CASE WHEN attendance_status = 'on_time' THEN 1 ELSE 0 END) as on_time_count,
                SUM(CASE WHEN attendance_status = 'late' THEN 1 ELSE 0 END) as late_count,
                SUM(CASE WHEN attendance_status = 'absent' THEN 1 ELSE 0 END) as absent_count,
                SUM(CASE WHEN attendance_status = 'excused' THEN 1 ELSE 0 END) as excused_count,
                AVG(CASE WHEN attendance_status != 'absent' THEN 1.0 ELSE 0.0 END) * 100 as attendance_rate
            FROM attendance_sessions
            WHERE student_id = ?
        """, (agent_student_id,))
        
        stats_row = cursor.fetchone()
        stats = {
            'total_sessions': stats_row[0] or 0,
            'on_time_count': stats_row[1] or 0,
            'late_count': stats_row[2] or 0,
            'absent_count': stats_row[3] or 0,
            'excused_count': stats_row[4] or 0,
            'attendance_rate': round(stats_row[5] or 0, 1)
        }
        
        agent_conn.close()
    else:
        # Get attendance statistics from MAIN database
        with app.state.user_db._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_sessions,
                    SUM(CASE WHEN attendance_status = 'on_time' THEN 1 ELSE 0 END) as on_time_count,
                    SUM(CASE WHEN attendance_status = 'late' THEN 1 ELSE 0 END) as late_count,
                    SUM(CASE WHEN attendance_status = 'absent' THEN 1 ELSE 0 END) as absent_count,
                    SUM(CASE WHEN attendance_status = 'excused' THEN 1 ELSE 0 END) as excused_count,
                    AVG(CASE WHEN attendance_status != 'absent' THEN 1.0 ELSE 0.0 END) * 100 as attendance_rate
                FROM attendance_sessions
                WHERE student_id = ?
            """, (student_id,))
            
            stats_row = cursor.fetchone()
            stats = {
                'total_sessions': stats_row[0] or 0,
                'on_time_count': stats_row[1] or 0,
                'late_count': stats_row[2] or 0,
                'absent_count': stats_row[3] or 0,
                'excused_count': stats_row[4] or 0,
                'attendance_rate': round(stats_row[5] or 0, 1)
            }
    
    return {
        "student": student,
        "statistics": stats
    }
@app.get("/api/students/{student_id}/graph-data")
async def get_student_graph_data(
    student_id: str,
    days_before: int = 30,
    current_user: dict = Depends(get_current_user)
):
    """
    Get attendance graph data for the last N days.
    Returns daily attendance rates for visualization.
    """
    # Add same permission checks as above
    # ...
    
    try:
        # STU-prefixed IDs use agent database, others use main database
        use_agent_db = student_id.startswith("STU")
        
        if use_agent_db:
            # Get agent student ID by looking up name
            agent_student_id = get_agent_student_id(student_id)
            
            if not agent_student_id:
                return {"graph_data": []}
            
            # Use AGENT database
            import sqlite3
            from datetime import datetime, timedelta
            
            agent_conn = sqlite3.connect(AGENT_DB_PATH)
            cursor = agent_conn.cursor()
            
            target_date = datetime.today().strftime('%Y-%m-%d')
            start_date = (datetime.today() - timedelta(days=days_before)).strftime('%Y-%m-%d')
            
            cursor.execute("""
            SELECT 
                date(session_date) as day,
                COUNT(CASE WHEN attendance_status = 'absent' THEN 1 END) as absent_count,
                COUNT(CASE WHEN attendance_status != 'absent' THEN 1 END) as present_count,
                COUNT(*) as total_sessions
            FROM attendance_sessions 
            WHERE student_id = ? 
              AND session_date >= ? 
              AND session_date <= ?
            GROUP BY date(session_date)
            ORDER BY day
            """, (agent_student_id, start_date, target_date))
            
            formatted_data = []
            for day, absent, present, total in cursor.fetchall():
                present_rate = round((present / total) * 100, 1) if total > 0 else 0
                formatted_data.append({
                    'date': day,
                    'absent_count': absent,
                    'present_count': present,
                    'total_sessions': total,
                    'present_rate': present_rate
                })
            
            agent_conn.close()
            return {"graph_data": formatted_data}
        else:
            # Use MAIN database
            graph_data = get_student_attendance_graph_data(
                student_id, 
                target_date=None,
                days_before=days_before
            )
            
            formatted_data = [
                {
                    'date': row[0],
                    'absent_count': row[1],
                    'present_count': row[2],
                    'total_sessions': row[3],
                    'present_rate': row[4]
                }
                for row in graph_data
            ]
            
            return {"graph_data": formatted_data}
    except Exception as e:
        print(f"Error getting graph data: {e}")
        raise HTTPException(status_code=500, detail="Failed to get graph data")
@app.get("/api/students/{student_id}/analysis")
async def get_student_ai_analysis(
    student_id: str,
    limit: int = 5,
    current_user: dict = Depends(get_current_user)
):
    """
    Get AI analysis and alerts for a student.
    Returns recent analysis from agent_analysis_log.
    """
    # Add permission checks
    # ...
    
    try:
        use_agent_db = student_id.startswith("STU")
        
        if use_agent_db:
            # Get agent student ID and query agent database
            agent_student_id = get_agent_student_id(student_id)
            
            if not agent_student_id:
                return {"analysis": []}
            
            import sqlite3
            agent_conn = sqlite3.connect(AGENT_DB_PATH)
            cursor = agent_conn.cursor()
            
            cursor.execute("""
                SELECT student_name, alert_level, reason, recommendation, analysis_date, intervention_effective
                FROM agent_analysis_log 
                WHERE student_id = ?
                ORDER BY analysis_date DESC
                LIMIT ?
            """, (agent_student_id, limit))
            
            formatted_analysis = [
                {
                    'student_name': row[0],
                    'alert_level': row[1],
                    'reason': row[2],
                    'recommendation': row[3],
                    'analysis_date': row[4],
                    'intervention_effective': row[5]
                }
                for row in cursor.fetchall()
            ]
            
            agent_conn.close()
            return {"analysis": formatted_analysis}
        else:
            # Use main database
            analysis_results = AnalysisAgent.get_student_analysis(student_id)
            
            formatted_analysis = [
                {
                    'student_name': row[0],
                    'alert_level': row[1],
                    'reason': row[2],
                    'recommendation': row[3],
                    'analysis_date': row[4],
                    'intervention_effective': row[5]
                }
                for row in (analysis_results[:limit] if analysis_results else [])
            ]
            
            return {"analysis": formatted_analysis}
    except Exception as e:
        # Return empty array if table doesn't exist or other errors
        print(f"Error getting analysis: {e}")
        return {"analysis": []}
@app.get("/api/students/{student_id}/interventions")
async def get_student_interventions(
    student_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get intervention history for a student.
    Returns last 3 interventions with effectiveness.
    """
    # Add permission checks
    # ...
    
    try:
        use_agent_db = student_id.startswith("STU")
        
        if use_agent_db:
            # Get agent student ID and query agent database
            agent_student_id = get_agent_student_id(student_id)
            
            if not agent_student_id:
                return {"interventions": []}
            
            import sqlite3
            agent_conn = sqlite3.connect(AGENT_DB_PATH)
            cursor = agent_conn.cursor()
            
            cursor.execute("""
                SELECT reason, recommendation, intervention_effective, analysis_date
                FROM agent_analysis_log 
                WHERE student_id = ? AND intervention_effective IS NOT NULL
                ORDER BY analysis_date DESC
                LIMIT 3
            """, (agent_student_id,))
            
            formatted_interventions = [
                {
                    'reason': row[0],
                    'recommendation': row[1],
                    'intervention_effective': row[2],
                    'analysis_date': row[3]
                }
                for row in cursor.fetchall()
            ]
            
            agent_conn.close()
            return {"interventions": formatted_interventions}
        else:
            # Use main database
            interventions = AnalysisAgent.get_intervention_history(student_id)
            
            if not interventions:
                return {"interventions": []}
            
            formatted_interventions = [
                {
                    'reason': row[0],
                    'recommendation': row[1],
                    'intervention_effective': row[2],
                    'analysis_date': row[3]
                }
                for row in interventions
            ]
            
            return {"interventions": formatted_interventions}
    except Exception as e:
        # Return empty array if table doesn't exist or other errors
        print(f"Error getting interventions: {e}")
        return {"interventions": []}
@app.get("/api/students/{student_id}/attendance-history")
async def get_student_attendance_history(
    student_id: str,
    page: int = 1,
    page_size: int = 20,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Get paginated attendance history for a student.
    Supports date filtering.
    """
    # Add permission checks
    # ...
    
    try:
        # STU-prefixed IDs use agent database, others use main database
        use_agent_db = student_id.startswith("STU")
        
        if use_agent_db:
            # Get agent student ID by looking up name
            agent_student_id = get_agent_student_id(student_id)
            
            if not agent_student_id:
                return {
                    "attendance_records": [],
                    "pagination": {"page": page, "page_size": page_size, "total_count": 0, "total_pages": 0}
                }
            
            # Use AGENT database
            import sqlite3
            agent_conn = sqlite3.connect(AGENT_DB_PATH)
            cursor = agent_conn.cursor()
            
            query = """
                SELECT session_date, session_number, entry_time, exit_time, 
                       duration_minutes, attendance_status, late_minutes, attendance_score
                FROM attendance_sessions WHERE student_id = ?
            """
            params = [int(agent_student_id)]
            
            if start_date:
                query += " AND session_date >= ?"
                params.append(start_date)
            if end_date:
                query += " AND session_date <= ?"
                params.append(end_date)
            
            query += " ORDER BY session_date DESC, session_number DESC"
            
            # Count
            count_query = "SELECT COUNT(*) FROM attendance_sessions WHERE student_id = ?"
            count_params = [int(agent_student_id)]
            if start_date:
                count_query += " AND session_date >= ?"
                count_params.append(start_date)
            if end_date:
                count_query += " AND session_date <= ?"
                count_params.append(end_date)
            
            cursor.execute(count_query, count_params)
            total_count = cursor.fetchone()[0] or 0
            
            offset = (page - 1) * page_size
            query += f" LIMIT {page_size} OFFSET {offset}"
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            attendance_records = [
                {'session_date': r[0], 'session_number': r[1], 'entry_time': r[2], 'exit_time': r[3],
                 'duration_minutes': r[4], 'attendance_status': r[5], 'late_minutes': r[6], 'attendance_score': r[7]}
                for r in rows
            ]
            
            agent_conn.close()
            return {
                "attendance_records": attendance_records,
                "pagination": {"page": page, "page_size": page_size, "total_count": total_count,
                              "total_pages": (total_count + page_size - 1) // page_size}
            }
        else:
            # Use MAIN database
            with app.state.user_db._get_connection() as conn:
                cursor = conn.cursor()
            
            # Build query with optional date filters
            query = """
                SELECT 
                    session_date,
                    session_number,
                    entry_time,
                    exit_time,
                    duration_minutes,
                    attendance_status,
                    late_minutes,
                    attendance_score
                FROM attendance_sessions
                WHERE student_id = ?
            """
            params = [student_id]
            
            if start_date:
                query += " AND session_date >= ?"
                params.append(start_date)
            
            if end_date:
                query += " AND session_date <= ?"
                params.append(end_date)
            
            query += " ORDER BY session_date DESC, session_number DESC"
            
            # Get total count - build separate query
            count_query = "SELECT COUNT(*) FROM attendance_sessions WHERE student_id = ?"
            count_params = [student_id]
            
            if start_date:
                count_query += " AND session_date >= ?"
                count_params.append(start_date)
            
            if end_date:
                count_query += " AND session_date <= ?"
                count_params.append(end_date)
            
            cursor.execute(count_query, count_params)
            count_result = cursor.fetchone()
            total_count = count_result[0] if count_result else 0
            
            # Add pagination
            offset = (page - 1) * page_size
            query += f" LIMIT {page_size} OFFSET {offset}"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # Format results
            attendance_records = [
                {
                    'session_date': row[0],
                    'session_number': row[1],
                    'entry_time': row[2],
                    'exit_time': row[3],
                    'duration_minutes': row[4],
                    'attendance_status': row[5],
                    'late_minutes': row[6],
                    'attendance_score': row[7]
                }
                for row in rows
            ]
            
            return {
                "attendance_records": attendance_records,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total_count": total_count,
                    "total_pages": (total_count + page_size - 1) // page_size
                }
            }
    except Exception as e:
        import traceback
        print(f"Error getting attendance history: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Failed to get attendance history")

# --- CSV Attendance Summary Endpoints ---
@app.get("/api/attendance/csv-files")
async def list_csv_files(current_user: dict = Depends(get_current_user)):
    """
    List all CSV files in agent folder.
    Admin only access.
    """
    # Permission check
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        import glob
        import re
        from pathlib import Path
        
        agent_folder = os.path.join(BASE_DIR, "agent")
        csv_files = []
        
        # Find all CSV files
        for filepath in glob.glob(os.path.join(agent_folder, "*.csv")):
            filename = os.path.basename(filepath)
            file_stat = os.stat(filepath)
            
            # Parse date from filename (format: student_attendance_YYYY-MM-DD.csv)
            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
            date_str = date_match.group(1) if date_match else None
            
            # Create display name
            if "TOTAL_SUMMARY" in filename:
                display_name = "Tổng hợp toàn bộ"
            elif date_str:
                display_name = f"Ngày {date_str}"
            else:
                display_name = filename
            
            csv_files.append({
                "filename": filename,
                "display_name": display_name,
                "date": date_str,
                "size": file_stat.st_size,
                "modified": datetime.fromtimestamp(file_stat.st_mtime).isoformat()
            })
        
        # Sort by date (newest first), TOTAL_SUMMARY always first
        csv_files.sort(key=lambda x: (
            0 if "TOTAL_SUMMARY" in x["filename"] else 1,
            x["date"] or ""
        ), reverse=True)
        
        return {"files": csv_files}
    except Exception as e:
        print(f"Error listing CSV files: {e}")
        raise HTTPException(status_code=500, detail="Failed to list CSV files")


@app.get("/api/attendance/csv/{filename}")
async def get_csv_data(
    filename: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Read and parse CSV file, return as JSON.
    Admin only access.
    Security: Validates filename to prevent path traversal.
    """
    # Permission check
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Security: Validate filename (only alphanumeric, dash, underscore, dot)
    import re
    if not re.match(r'^[a-zA-Z0-9_\-\.]+\.csv$', filename):
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    # Prevent path traversal
    if '..' in filename or '/' in filename or '\\' in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    try:
        filepath = os.path.join(BASE_DIR, "agent", filename)
        
        # Check file exists
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail="File not found")
        
        # Read CSV
        data = []
        with open(filepath, 'r', encoding='utf-8') as f:
            csv_reader = csv.DictReader(f)
            headers = csv_reader.fieldnames
            
            for row in csv_reader:
                # Clean and convert data
                data.append({
                    "student_id": row.get("Student ID", "").strip(),
                    "student_name": row.get("Student Name", "").strip(),
                    "total_sessions": int(row.get("Total Sessions", 0) or 0),
                    "attended": int(row.get("Attended", 0) or 0),
                    "absent": int(row.get("Absent", 0) or 0),
                    "late": int(row.get("Late", 0) or 0),
                    "attendance_percent": row.get("Attendance %", "0%").strip(),
                    "avg_score": float(row.get("Avg Score", 0) or 0)
                })
        
        # Calculate summary
        total_students = len(data)
        if total_students > 0:
            total_sessions_sum = sum(d["total_sessions"] for d in data)
            avg_sessions = total_sessions_sum / total_students if total_students > 0 else 0
            
            # Calculate average attendance percentage
            attendance_values = []
            for d in data:
                percent_str = d["attendance_percent"].replace("%", "")
                try:
                    attendance_values.append(float(percent_str))
                except:
                    attendance_values.append(0)
            
            avg_attendance = sum(attendance_values) / len(attendance_values) if attendance_values else 0
        else:
            avg_sessions = 0
            avg_attendance = 0
        
        summary = {
            "total_students": total_students,
            "avg_attendance": f"{avg_attendance:.1f}%",
            "avg_sessions": round(avg_sessions, 1)
        }
        
        return {
            "filename": filename,
            "headers": headers,
            "data": data,
            "summary": summary
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Failed to read CSV file")

# --- To run this API, use the command: ---
# uvicorn api:app --host 0.0.0.0 --port 8000 --reload
