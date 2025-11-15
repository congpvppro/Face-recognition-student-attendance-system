import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
import threading

import cv2
import time
import warnings
import argparse
import logging
import numpy as np
from database import AttendanceDatabase
import yaml
from models.face_tracking.byte_tracker import BYTETracker
from models.face_tracking.visualize import plot_tracking
from database import FaceDatabase
from models import SCRFD, ArcFace, AntiSpoof, AttendanceTracker
from utils.logging import setup_logging
from datetime import datetime

warnings.filterwarnings("ignore")
setup_logging(log_to_file=True)

COLOR_REAL = (0, 255, 0)
COLOR_FAKE = (0, 0, 255)
COLOR_UNKNOWN = (127, 127, 127)
import threading

# Replace the data_mapping dictionary with:
data_mapping = {
    "raw_image": [],
    "tracking_ids": [],
    "detection_bboxes": [],
    "detection_landmarks": [],
    "tracking_bboxes": [],
}
data_lock = threading.Lock()
recognition_ready = threading.Event()

id_face_mapping = {}

def parse_args():

    parser = argparse.ArgumentParser(description="Face Recognition Attendance with ByteTrack")

    parser.add_argument("--det-weight", type=str, default="./weights/det_500m.onnx", help="Path to detection model")
    parser.add_argument("--rec-weight", type=str, default="./weights/w600k_mbf.onnx", help="Path to recognition model")
    parser.add_argument("--spoof-weight", type=str, default="weights/AntiSpoofing_bin_1.5_128.onnx",
                        help="Path to Anti-spoofing model")
    parser.add_argument("--similarity-thresh", type=float, default=0.4, help="Similarity threshold between faces")
    parser.add_argument("--confidence-thresh", type=float, default=0.5, help="Confidence threshold for face detection")
    parser.add_argument("--faces-dir", type=str, default="./assets/faces", help="Path to faces stored dir")
    parser.add_argument("--max-num", type=int, default=0, help="Maximum number of face detections from a frame")
    parser.add_argument("--db-path", type=str, default="./database/face_database",
                        help="path to vector db and metadata")
    parser.add_argument("--update-db", action="store_true", help="Force update of the face database")
    parser.add_argument("--output", type=str, default="output_video.mp4", help="Output path for annotated video")
    parser.add_argument("--exit-cooldown", type=int, default=5, help="Seconds before marking someone as left")
    parser.add_argument("--attendance-cooldown", type=int, default=300,
                        help="Cooldown in seconds between attendance records")
    # ByteTrack parameters
    parser.add_argument("--track-thresh", type=float, default=0.6, help="High confidence threshold for tracking")
    parser.add_argument("--track-buffer", type=int, default=30, help="Frames to keep lost tracks")
    parser.add_argument("--match-thresh", type=float, default=0.8, help="IoU threshold for matching")
    parser.add_argument("--min-box-area", type=int, default=100, help="Minimum bbox area")

    # SQLite parameters
    parser.add_argument("--attendance-db-path", type=str, default="./database/attendance.db", help="Path to SQLite attendance database")

    return parser.parse_args()


def build_face_database(detector: SCRFD, recognizer: ArcFace, params: argparse.Namespace,
                        force_update: bool = False) -> FaceDatabase:
    face_db = FaceDatabase(db_path=params.db_path, max_workers=4)

    if not force_update and face_db.load():
        logging.info("Loaded face database from disk.")
        return face_db

    logging.info("Building face database from images...")

    if not os.path.exists(params.faces_dir):
        logging.warning(f"Faces directory {params.faces_dir} does not exist. Creating empty database.")
        face_db.save()
        return face_db

    for person_name in os.listdir(params.faces_dir):
        person_dir = os.path.join(params.faces_dir, person_name)

        if not os.path.isdir(person_dir):
            logging.warning(f"Skipping {person_name} - not a directory")
            continue

        logging.info(f"Processing person: {person_name}")

        image_files = [f for f in os.listdir(person_dir)
                       if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))]

        if not image_files:
            logging.warning(f"No images found for {person_name}")
            continue

        final_embeddings = []
        out_vec = None

        for filename in image_files:
            image_path = os.path.join(person_dir, filename)
            image = cv2.imread(image_path)

            if image is None:
                logging.warning(f"Could not read image: {image_path}")
                continue

            try:
                bboxes, kpss = detector.detect(image, max_num=1)

                if len(kpss) == 0:
                    logging.warning(f"No face detected in {image_path}. Skipping...")
                    continue

                embedding = recognizer.get_embedding(image, kpss[0], normalized=True)
                final_embeddings.append(embedding)
                out_vec = np.average(final_embeddings, axis=0)
                logging.info(f"Added face embedding for: {person_name} from {filename}")
            except Exception as e:
                logging.error(f"Error processing {image_path}: {e}")
                continue

        if out_vec is not None:
            face_db.add_face(out_vec, person_name)

    face_db.save()
    logging.info(f"Face database built successfully with {face_db.index.ntotal} face embeddings")
    return face_db

def load_config(file_name):

    with open(file_name, "r") as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)


def process_tracking(frame, detector, tracker, args, frame_id, fps):
    global data_mapping

    # Face detection and tracking
    outputs, img_info, bboxes, landmarks = detector.detect_tracking(image=frame)
    tracking_tlwhs = []
    tracking_ids = []
    tracking_scores = []
    tracking_bboxes = []

    if outputs is not None:
        online_targets = tracker.update(
            outputs, [img_info["height"], img_info["width"]], (640, 640)
        )

        for i in range(len(online_targets)):
            t = online_targets[i]
            tlwh = t.tlwh
            tid = t.track_id
            vertical = tlwh[2] / tlwh[3] > args["aspect_ratio_thresh"]
            if tlwh[2] * tlwh[3] > args["min_box_area"] and not vertical:
                x1, y1, w, h = tlwh
                tracking_bboxes.append([x1, y1, x1 + w, y1 + h])
                tracking_tlwhs.append(tlwh)
                tracking_ids.append(tid)
                tracking_scores.append(t.score)
        tracking_image = plot_tracking(
            img_info["raw_img"],
            tracking_tlwhs,
            tracking_ids,
            names=id_face_mapping,
            frame_id=frame_id + 1,
            fps=fps,
        )
    else:
        tracking_image = img_info["raw_img"]

    # CHANGE: Use thread lock to safely update shared data
    with data_lock:
        data_mapping["raw_image"] = img_info["raw_img"].copy()  # Make a copy!
        data_mapping["detection_bboxes"] = bboxes.copy() if len(bboxes) > 0 else []
        data_mapping["detection_landmarks"] = landmarks.copy() if len(landmarks) > 0 else []
        data_mapping["tracking_ids"] = tracking_ids.copy()
        data_mapping["tracking_bboxes"] = tracking_bboxes.copy()

    # Signal that new data is ready
    recognition_ready.set()

    return tracking_image


# def recognition(recognizer: ArcFace, face_db: FaceDatabase, attendance_tracker: AttendanceTracker,
#                 last_seen: dict, params: argparse.Namespace):
#     """Recognition thread - runs continuously"""
#     logging.info("Recognition thread started")
#
#     while True:
#         # Wait for new tracking data
#         recognition_ready.wait(timeout=1.0)
#         recognition_ready.clear()
#
#         # Safely copy data we need
#         with data_lock:
#             # CHANGE: Better condition checking
#             raw_image = data_mapping["raw_image"]
#             detection_landmarks = data_mapping["detection_landmarks"]
#
#             # Check if data is valid
#             if not isinstance(raw_image, np.ndarray) or raw_image.size == 0:
#                 continue
#             if not isinstance(detection_landmarks, (list, np.ndarray)) or len(detection_landmarks) == 0:
#                 continue
#
#             frame = raw_image.copy()
#             detection_landmarks = [kps.copy() for kps in detection_landmarks]
#             tracking_bboxes = data_mapping["tracking_bboxes"].copy() if len(data_mapping["tracking_bboxes"]) > 0 else []
#             tracking_ids = data_mapping["tracking_ids"].copy() if len(data_mapping["tracking_ids"]) > 0 else []
#
#         if len(detection_landmarks) == 0 or len(tracking_ids) == 0:
#             continue
#
#         # Perform recognition
#         embeddings = []
#         current_time = time.time()
#
#         try:
#             for kps in detection_landmarks:
#                 embedding = recognizer.get_embedding(frame, kps)
#                 embeddings.append(embedding)
#         except Exception as e:
#             logging.error(f"Error getting embeddings: {e}")
#             continue
#
#         if embeddings and len(tracking_bboxes) == len(embeddings):
#             results = face_db.batch_search(embeddings, params.similarity_thresh)
#
#             # Build tracked_objects for AttendanceTracker
#             tracked_objects = {}
#
#             for i, ((name, similarity), track_id, bbox) in enumerate(zip(results, tracking_ids, tracking_bboxes)):
#                 # Calculate centroid
#                 centroid = ((bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2)
#                 tracked_objects[track_id] = (centroid, name)
#
#                 if name != "Unknown":
#                     # Update mapping for visualization
#                     id_face_mapping[track_id] = name
#
#                     # Optional: Log first recognition (with cooldown)
#                     if name not in last_seen or (current_time - last_seen[name]) >= 30:
#                         last_seen[name] = current_time
#                         logging.info(f"Recognized: {name} (similarity: {similarity:.3f})")
#
#             # Update attendance tracker (handles entry/exit)
#             attendance_tracker.update(tracked_objects)

def recognition(recognizer: ArcFace, face_db: FaceDatabase, attendance_tracker: AttendanceTracker,
                last_seen: dict, params: argparse.Namespace, stop_event):
    logging.info("Recognition thread started")

    while not stop_event.is_set():
        recognition_ready.wait(timeout=0.5)
        recognition_ready.clear()

        with data_lock:
            raw_image = data_mapping["raw_image"]
            detection_landmarks = data_mapping["detection_landmarks"]

            if not isinstance(raw_image, np.ndarray) or raw_image.size == 0:
                continue
            if not isinstance(detection_landmarks, (list, np.ndarray)) or len(detection_landmarks) == 0:
                attendance_tracker.update({})
                continue

            frame = raw_image.copy()
            detection_landmarks = [kps.copy() for kps in detection_landmarks]
            tracking_bboxes = data_mapping["tracking_bboxes"].copy() if len(data_mapping["tracking_bboxes"]) > 0 else []
            tracking_ids = data_mapping["tracking_ids"].copy() if len(data_mapping["tracking_ids"]) > 0 else []

        if len(detection_landmarks) == 0 or len(tracking_ids) == 0:
            attendance_tracker.update({})
            continue

        embeddings = []
        current_time = time.time()

        try:
            for kps in detection_landmarks:
                embedding = recognizer.get_embedding(frame, kps)
                embeddings.append(embedding)
        except Exception as e:
            logging.error(f"Error getting embeddings: {e}")
            attendance_tracker.update({})
            continue

        if embeddings and len(tracking_bboxes) == len(embeddings):
            results = face_db.batch_search(embeddings, params.similarity_thresh)

            tracked_objects = {}

            for i, ((name, similarity), track_id, bbox) in enumerate(zip(results, tracking_ids, tracking_bboxes)):
                centroid = ((bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2)
                tracked_objects[track_id] = (centroid, name)

                if name != "Unknown":
                    id_face_mapping[track_id] = name

                    if name not in last_seen or (current_time - last_seen[name]) >= 30:
                        last_seen[name] = current_time
                        logging.info(f" Recognized: {name} (similarity: {similarity:.3f})")

            attendance_tracker.update(tracked_objects)

            attendance_tracker.cleanup_lost_tracks(tracking_ids)
        else:
            # No valid tracking data
            attendance_tracker.update({})


def tracking(detector, recognizer, attendance_db, config_tracking, params, stop_event):
    tracker = BYTETracker(args=config_tracking, frame_rate=30)

    # ADD: Variables for absent checking
    session_start_checked = False
    check_time = None
    registered_students = []  # Load from database or config file

    # ADD: Load registered students from database
    try:
        with attendance_db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM students ORDER BY name")
            registered_students = [row[0] for row in cursor.fetchall()]
            cursor.close()
            logging.info(f"Loaded {len(registered_students)} registered students")
    except Exception as e:
        logging.error(f"Error loading registered students: {e}")

    try:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            raise IOError(f"Could not open video source")

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        out = cv2.VideoWriter(params.output, cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))

        full_name = input("Registered name (for manual capture, press Enter to skip): ")
        frame_count = 0

        logging.info("Starting attendance tracking with ByteTrack...")

        while not stop_event.is_set():
            ret, frame = cap.read()
            if not ret:
                break

            # ADD: Check for session start and mark absent students after 5 minutes
            current_time = datetime.now()
            session_info = attendance_db.get_current_session_time()

            if session_info and not session_start_checked:
                # Calculate time since session start
                session_start = datetime.combine(current_time.date(), session_info['start_time'])
                time_diff = (current_time - session_start).total_seconds() / 60

                # Check after 5 minutes of session start
                if time_diff >= 5:
                    absent_students = attendance_db.get_absent_students(registered_students)
                    if absent_students:
                        print(f"\n{'=' * 70}")
                        print(f" ABSENT STUDENTS ALERT (5 minutes after session start)")
                        print(f"{'=' * 70}")
                        print(
                            f"Session {session_info['session_number']} - Started at: {session_info['start_time'].strftime('%H:%M')}")
                        print(f"Current time: {current_time.strftime('%H:%M:%S')}")
                        print(f"\nAbsent students ({len(absent_students)}):")
                        for i, student in enumerate(absent_students, 1):
                            print(f"  {i}. {student}")
                            attendance_db.mark_absent(student)
                        print(f"{'=' * 70}\n")
                        logging.warning(f"{len(absent_students)} students marked as absent")

                    session_start_checked = True

            # Reset check for next session
            if session_info and check_time != session_info['session_number']:
                session_start_checked = False
                check_time = session_info['session_number']

            start = time.time()
            frame = process_tracking(frame, detector=detector, tracker=tracker,
                                     args=config_tracking, frame_id=frame_count, fps=fps)
            end = time.time()

            fps_text = f"FPS: {1 / (end - start):.1f}"
            cv2.putText(frame, fps_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                        1, (0, 255, 0), 2)

            out.write(frame)
            cv2.imshow("Face Recognition Attendance - ByteTrack", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                stop_event.set()
                break
            elif key == ord('b'):
                face_db = build_face_database(detector, recognizer, params, force_update=True)
            elif key == ord('s') and full_name:
                save_dir = os.path.join("assets/faces", full_name)
                os.makedirs(save_dir, exist_ok=True)
                cur_count = len(os.listdir(save_dir))
                save_path = os.path.join(save_dir, f"{full_name}_{cur_count + 1}.jpg")
                cv2.imwrite(save_path, frame)
                logging.info(f"Saved snapshot: {save_path}")
            elif key == ord('r'):
                total_sessions = 45
                report = attendance_db.get_attendance_report_with_scores(total_sessions)
                print("\n" + "=" * 100)
                print(f"ATTENDANCE REPORT - Semester (Total Sessions: {total_sessions})")
                print("=" * 100)
                print(
                    f"{'Name':<20} | {'Days':<5} | {'Late':<5} | {'Absent':<7} | {'Total Score':<12} | {'Score/10':<10}")
                print("-" * 100)
                for record in report:
                    print(f"{record['name']:<20} | {record['days_attended']:<5} | "
                          f"{record['late_count']:<5} | {record['absent_count']:<7} | "
                          f"{record['total_score']:<12.1f} | {record['score_out_of_10']:<10.1f}")
                print("=" * 100 + "\n")
            elif key == ord('c'):
                current_students = attendance_db.get_current_students()
                print("\n" + "=" * 50)
                print("CURRENT STUDENTS IN CLASS")
                print("=" * 50)
                for student in current_students:
                    print(f"  • {student}")
                print("=" * 50 + "\n")
            elif key == ord('d'):
                print("\n" + "=" * 70)
                print("WARNING: DATABASE RESET")
                confirm = input("Type 'DELETE' to confirm database reset: ")

                if confirm == "DELETE":
                    if attendance_db.reset_database():
                        print(" Database reset successfully!")
                        registered_students = []

                        global id_face_mapping
                        id_face_mapping = {}

                        logging.info("Database reset completed")
                    else:
                        print("Failed to reset database")
                        logging.error("Database reset failed")
                else:
                    print("Database reset cancelled")
                    logging.info("Database reset cancelled by user")

                print("=" * 70 + "\n")
            frame_count += 1

        logging.info(f"Processed {frame_count} frames.")

    except Exception as e:
        logging.error(f"Error during video processing: {e}")
        stop_event.set()
    finally:
        if 'cap' in locals():
            cap.release()
        if 'out' in locals():
            out.release()
        cv2.destroyAllWindows()

def main(params):
    try:
        detector = SCRFD(params.det_weight, input_size=(640, 640), conf_thres=params.confidence_thresh)
        recognizer = ArcFace(params.rec_weight)
        anti_spoofing = AntiSpoof(params.spoof_weight)
        file_name = "models/face_tracking/config_tracking.yaml"
        config_tracking = load_config(file_name)
        attendance_db = AttendanceDatabase(db_path=params.attendance_db_path)
    except Exception as e:
        logging.error(f"Failed to load models or database: {e}")
        return

    face_db = build_face_database(detector, recognizer, params, force_update=params.update_db)

    last_seen = {}
    attendance_tracker = AttendanceTracker(attendance_db, cooldown_seconds=params.exit_cooldown)

    stop_event = threading.Event()

    thread_track = threading.Thread(
        target=tracking,
        args=(detector, recognizer, attendance_db, config_tracking, params, stop_event),
        daemon=True
    )
    thread_track.start()

    thread_recognize = threading.Thread(
        target=recognition,
        args=(recognizer, face_db, attendance_tracker, last_seen, params,stop_event),
        daemon=True
    )
    thread_recognize.start()


    thread_track.join()
    stop_event.set()
    thread_recognize.join(timeout=2)

if __name__ == '__main__':
    args = parse_args()
    main(args)
