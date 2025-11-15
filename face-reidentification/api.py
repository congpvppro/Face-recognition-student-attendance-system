import os
import cv2
import numpy as np
import warnings
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import FileResponse
from typing import Optional
import uuid

# Suppress warnings
warnings.filterwarnings("ignore")
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

# Import your project's modules
from models import SCRFD, ArcFace
from database import FaceDatabase

# --- Configuration ---
# Get the absolute path of the directory where this script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DET_WEIGHT = os.path.join(BASE_DIR, "weights", "det_500m.onnx")
REC_WEIGHT = os.path.join(BASE_DIR, "weights", "w600k_mbf.onnx")
DB_PATH = os.path.join(BASE_DIR, "database", "face_database")
UNREGISTERED_FACES_PATH = os.path.join(BASE_DIR, "database", "unregistered_faces")
SIMILARITY_THRESH = 0.4
CONFIDENCE_THRESH = 0.5


# --- Lifespan Management (Modern Syntax) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load models and database when the application starts."""
    try:
        # Startup: Load models and database
        app.state.detector = SCRFD(DET_WEIGHT, input_size=(640, 640), conf_thres=CONFIDENCE_THRESH)
        app.state.recognizer = ArcFace(REC_WEIGHT)
        app.state.face_db = FaceDatabase(db_path=DB_PATH)
        
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
        
        yield  # Application runs here
        
        # Shutdown: Cleanup resources
        print("Shutting down and cleaning up resources...")
        
    except Exception as e:
        print(f"Error during startup: {e}")
        raise RuntimeError(f"Failed to initialize models or database: {e}")


# --- FastAPI App Initialization ---
app = FastAPI(title="Face Recognition API", lifespan=lifespan)


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
        
        # Check against other unregistered faces (in-memory)
        for existing_embedding in app.state.unregistered_embeddings.values():
            similarity = np.dot(new_embedding, existing_embedding)
            if similarity > SIMILARITY_THRESH:
                raise HTTPException(
                    status_code=409,
                    detail="This face is already pending registration."
                )
        
        # Generate a unique ID for this face image
        face_id = str(uuid.uuid4())
        image_path = os.path.join(UNREGISTERED_FACES_PATH, f"{face_id}.jpg")
        
        # Save the original image
        cv2.imwrite(image_path, frame)
        
        # Add to in-memory cache
        app.state.unregistered_embeddings[face_id] = new_embedding
        
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
        
        # Clean up the unregistered face image and cache entry
        image_path = os.path.join(UNREGISTERED_FACES_PATH, f"{face_id}.jpg")
        if os.path.exists(image_path):
            os.remove(image_path)
        
        del app.state.unregistered_embeddings[face_id]
        
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
    if not os.path.exists(image_path):
        return {"message": f"Unregistered face {face_id} already deleted or not found."}
    
    try:
        os.remove(image_path)
        if hasattr(app.state, 'unregistered_embeddings') and face_id in app.state.unregistered_embeddings:
            del app.state.unregistered_embeddings[face_id]
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


# --- To run this API, use the command: ---
# uvicorn api:app --host 0.0.0.0 --port 8000 --reload
