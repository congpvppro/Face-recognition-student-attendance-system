import os
import cv2
import numpy as np
import warnings
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Depends, Header
from fastapi.responses import FileResponse
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

# --- Configuration ---
# Get the absolute path of the directory where this script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DET_WEIGHT = os.path.join(BASE_DIR, "weights", "det_500m.onnx")
REC_WEIGHT = os.path.join(BASE_DIR, "weights", "w600k_mbf.onnx")
DB_PATH = os.path.join(BASE_DIR, "database", "face_database")
ATTENDANCE_DB_PATH = os.path.join(BASE_DIR, "database", "attendance.db")
UNREGISTERED_FACES_PATH = os.path.join(BASE_DIR, "database", "unregistered_faces")
SIMILARITY_THRESH = 0.4
CONFIDENCE_THRESH = 0.5

# JWT Configuration
JWT_SECRET = os.environ.get("JWT_SECRET", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24 * 7  # 7 days


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


# --- To run this API, use the command: ---
# uvicorn api:app --host 0.0.0.0 --port 8000 --reload
