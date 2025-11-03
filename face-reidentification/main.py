import os
import cv2
import random
import time
import warnings
import argparse
import logging
import numpy as np
import mysql.connector
from datetime import datetime
from contextlib import contextmanager
from collections import defaultdict
from scipy.spatial import distance as dist
from database import FaceDatabase
from models import SCRFD, ArcFace, AntiSpoof
from utils.logging import setup_logging
from utils.helpers import compute_similarity, draw_bbox_info, draw_bbox

warnings.filterwarnings("ignore")
setup_logging(log_to_file=True)

COLOR_REAL = (0, 255, 0)
COLOR_FAKE = (0, 0, 255)
COLOR_UNKNOWN = (127, 127, 127)


class CentroidTracker:

    def __init__(self, max_disappeared=50, max_distance=100):
        self.next_object_id = 0
        self.objects = {}  # object_id: centroid
        self.object_names = {}  # object_id: name
        self.disappeared = {}  # object_id: frame_count
        self.max_disappeared = max_disappeared
        self.max_distance = max_distance

    def register(self, centroid, name="Unknown"):
        """Register new object with centroid and name"""
        self.objects[self.next_object_id] = centroid
        self.object_names[self.next_object_id] = name
        self.disappeared[self.next_object_id] = 0
        self.next_object_id += 1

    def deregister(self, object_id):
        """Remove object from tracking"""
        del self.objects[object_id]
        del self.object_names[object_id]
        del self.disappeared[object_id]

    def update(self, detections):
        # If no detections, mark all as disappeared
        if len(detections) == 0:
            for object_id in list(self.disappeared.keys()):
                self.disappeared[object_id] += 1
                if self.disappeared[object_id] > self.max_disappeared:
                    self.deregister(object_id)
            return self.get_objects()

        # Calculate centroids for new detections
        input_centroids = []
        input_names = []
        for (bbox, name) in detections:
            x1, y1, x2, y2 = bbox
            cx = int((x1 + x2) / 2.0)
            cy = int((y1 + y2) / 2.0)
            input_centroids.append((cx, cy))
            input_names.append(name)

        # If no existing objects, register all
        if len(self.objects) == 0:
            for i in range(len(input_centroids)):
                self.register(input_centroids[i], input_names[i])
        else:
            # Match existing objects with new detections
            object_ids = list(self.objects.keys())
            object_centroids = list(self.objects.values())

            # Compute distance matrix
            D = dist.cdist(np.array(object_centroids), np.array(input_centroids))

            # Find minimum distance for each existing object
            rows = D.min(axis=1).argsort()
            cols = D.argmin(axis=1)[rows]

            used_rows = set()
            used_cols = set()

            # Associate detections with existing objects
            for (row, col) in zip(rows, cols):
                if row in used_rows or col in used_cols:
                    continue

                if D[row, col] > self.max_distance:
                    continue

                object_id = object_ids[row]
                self.objects[object_id] = input_centroids[col]
                # Update name if it's not "Unknown"
                if input_names[col] != "Unknown":
                    self.object_names[object_id] = input_names[col]
                self.disappeared[object_id] = 0

                used_rows.add(row)
                used_cols.add(col)

            # Handle disappeared objects
            unused_rows = set(range(D.shape[0])) - used_rows
            for row in unused_rows:
                object_id = object_ids[row]
                self.disappeared[object_id] += 1
                if self.disappeared[object_id] > self.max_disappeared:
                    self.deregister(object_id)

            # Register new objects
            unused_cols = set(range(D.shape[1])) - used_cols
            for col in unused_cols:
                self.register(input_centroids[col], input_names[col])

        return self.get_objects()

    def get_objects(self):
        """Get current tracked objects with names"""
        return {oid: (centroid, self.object_names[oid])
                for oid, centroid in self.objects.items()}


class AttendanceDatabase:

    def __init__(self, host='localhost', port=3306, user='root', password='07112005', database='attendance_db'):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.connection = None
        self._init_database()

    def _init_database(self):
        try:
            conn = mysql.connector.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password
            )
            cursor = conn.cursor()

            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database}")
            cursor.execute(f"USE {self.database}")

            # Create students table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS students (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255) NOT NULL UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create attendance sessions table (tracks entry/exit)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS attendance_sessions (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    student_id INT NOT NULL,
                    session_date DATE NOT NULL,
                    entry_time DATETIME NOT NULL,
                    exit_time DATETIME,
                    duration_minutes INT,
                    status ENUM('present', 'left') DEFAULT 'present',
                    FOREIGN KEY (student_id) REFERENCES students(id),
                    INDEX idx_date_status (session_date, status)
                )
            """)

            # Create daily attendance summary
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_attendance (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    student_id INT NOT NULL,
                    attendance_date DATE NOT NULL,
                    total_sessions INT DEFAULT 0,
                    total_minutes INT DEFAULT 0,
                    first_entry DATETIME,
                    last_exit DATETIME,
                    current_status ENUM('present', 'absent') DEFAULT 'absent',
                    FOREIGN KEY (student_id) REFERENCES students(id),
                    UNIQUE KEY unique_daily_attendance (student_id, attendance_date)
                )
            """)

            conn.commit()
            cursor.close()
            conn.close()
            logging.info("Database initialized successfully")

        except mysql.connector.Error as e:
            logging.error(f"Error initializing database: {e}")
            raise

    @contextmanager
    def get_connection(self):
        conn = mysql.connector.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.database
        )
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def get_or_create_student(self, name):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM students WHERE name = %s", (name,))
                result = cursor.fetchone()

                if not result:
                    cursor.execute("INSERT INTO students (name) VALUES (%s)", (name,))
                    student_id = cursor.lastrowid
                else:
                    student_id = result[0]

                cursor.close()
                return student_id
        except mysql.connector.Error as e:
            logging.error(f"Error getting/creating student: {e}")
            return None

    def record_entry(self, name):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                student_id = self.get_or_create_student(name)

                current_datetime = datetime.now()
                current_date = current_datetime.date()

                # Create new session
                cursor.execute("""
                    INSERT INTO attendance_sessions 
                    (student_id, session_date, entry_time, status)
                    VALUES (%s, %s, %s, 'present')
                """, (student_id, current_date, current_datetime))

                session_id = cursor.lastrowid

                # Update daily summary
                cursor.execute("""
                    INSERT INTO daily_attendance 
                    (student_id, attendance_date, total_sessions, first_entry, current_status)
                    VALUES (%s, %s, 1, %s, 'present')
                    ON DUPLICATE KEY UPDATE
                        total_sessions = total_sessions + 1,
                        current_status = 'present',
                        first_entry = LEAST(first_entry, %s)
                """, (student_id, current_date, current_datetime, current_datetime))

                cursor.close()
                logging.info(f"Entry recorded for {name} at {current_datetime.strftime('%H:%M:%S')}")
                return session_id

        except mysql.connector.Error as e:
            logging.error(f"Error recording entry: {e}")
            return None

    def record_exit(self, name):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                student_id = self.get_or_create_student(name)

                current_datetime = datetime.now()
                current_date = current_datetime.date()

                # Find the most recent open session
                cursor.execute("""
                    SELECT id, entry_time FROM attendance_sessions
                    WHERE student_id = %s 
                    AND session_date = %s 
                    AND status = 'present'
                    ORDER BY entry_time DESC
                    LIMIT 1
                """, (student_id, current_date))

                result = cursor.fetchone()

                if result:
                    session_id, entry_time = result
                    duration = int((current_datetime - entry_time).total_seconds() / 60)

                    # Update session
                    cursor.execute("""
                        UPDATE attendance_sessions
                        SET exit_time = %s, duration_minutes = %s, status = 'left'
                        WHERE id = %s
                    """, (current_datetime, duration, session_id))

                    # Update daily summary
                    cursor.execute("""
                        UPDATE daily_attendance
                        SET total_minutes = total_minutes + %s,
                            last_exit = %s,
                            current_status = 'absent'
                        WHERE student_id = %s AND attendance_date = %s
                    """, (duration, current_datetime, student_id, current_date))

                    cursor.close()
                    logging.info(
                        f" Exit recorded for {name} at {current_datetime.strftime('%H:%M:%S')} (Duration: {duration} min)")
                    return True
                else:
                    logging.warning(f"No open session found for {name}")
                    cursor.close()
                    return False

        except mysql.connector.Error as e:
            logging.error(f"Error recording exit: {e}")
            return False

    def get_current_status(self, name):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                current_date = datetime.now().date()

                cursor.execute("""
                    SELECT da.current_status
                    FROM daily_attendance da
                    JOIN students s ON da.student_id = s.id
                    WHERE s.name = %s AND da.attendance_date = %s
                """, (name, current_date))

                result = cursor.fetchone()
                cursor.close()

                return result[0] if result else 'absent'

        except mysql.connector.Error as e:
            logging.error(f"Error getting status: {e}")
            return 'absent'

    def get_daily_report(self, date=None):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                target_date = date or datetime.now().date()

                cursor.execute("""
                    SELECT 
                        s.name,
                        da.total_sessions,
                        da.total_minutes,
                        da.first_entry,
                        da.last_exit,
                        da.current_status
                    FROM daily_attendance da
                    JOIN students s ON da.student_id = s.id
                    WHERE da.attendance_date = %s
                    ORDER BY s.name
                """, (target_date,))

                results = cursor.fetchall()
                cursor.close()
                return results

        except mysql.connector.Error as e:
            logging.error(f"Error getting daily report: {e}")
            return []


class AttendanceTracker:

    def __init__(self, attendance_db, cooldown_seconds=5):
        self.attendance_db = attendance_db
        self.cooldown_seconds = cooldown_seconds
        self.tracked_people = {}  # name: {'last_seen': time, 'status': 'present'/'absent', 'session_id': int}
        self.track_to_name = {}  # track_id: name

    def update(self, tracked_objects):
        current_time = time.time()
        current_tracked_names = set()

        # Update tracking with current detections
        for track_id, (centroid, name) in tracked_objects.items():
            if name != "Unknown":
                current_tracked_names.add(name)
                self.track_to_name[track_id] = name

                # Check if person just entered
                if name not in self.tracked_people:
                    # New entry
                    session_id = self.attendance_db.record_entry(name)
                    self.tracked_people[name] = {
                        'last_seen': current_time,
                        'status': 'present',
                        'session_id': session_id,
                        'track_id': track_id
                    }
                else:
                    # Update last seen time
                    person_data = self.tracked_people[name]

                    # If person was marked as left but reappeared
                    if person_data['status'] == 'absent':
                        session_id = self.attendance_db.record_entry(name)
                        person_data['session_id'] = session_id
                        person_data['status'] = 'present'

                    person_data['last_seen'] = current_time
                    person_data['track_id'] = track_id

        # Check for people who have left (not seen for cooldown period)
        for name, person_data in list(self.tracked_people.items()):
            if person_data['status'] == 'present':
                time_since_seen = current_time - person_data['last_seen']

                if name not in current_tracked_names and time_since_seen > self.cooldown_seconds:
                    # Person has left
                    self.attendance_db.record_exit(name)
                    person_data['status'] = 'absent'
                    logging.info(f"{name} left the class")

    def get_status(self, name):
        if name in self.tracked_people:
            return self.tracked_people[name]['status']
        return 'absent'


def parse_args():
    parser = argparse.ArgumentParser(description="Face Recognition Attendance with Entry/Exit Tracking")

    parser.add_argument("--det-weight", type=str, default="./weights/det_500m.onnx", help="Path to detection model")
    parser.add_argument("--rec-weight", type=str, default="./weights/w600k_mbf.onnx", help="Path to recognition model")
    parser.add_argument("--spoof-weight", type=str, default="weights/AntiSpoofing_bin_1.5_128.onnx",
                        help="Path to Anti-spoofing model")
    parser.add_argument("--similarity-thresh", type=float, default=0.4, help="Similarity threshold between faces")
    parser.add_argument("--confidence-thresh", type=float, default=0.5, help="Confidence threshold for face detection")
    parser.add_argument("--faces-dir", type=str, default="./assets/faces", help="Path to faces stored dir")
    parser.add_argument("--source", type=str, default="./assets/in_video.mp4", help="Video file or webcam source")
    parser.add_argument("--max-num", type=int, default=0, help="Maximum number of face detections from a frame")
    parser.add_argument("--db-path", type=str, default="./database/face_database",
                        help="path to vector db and metadata")
    parser.add_argument("--update-db", action="store_true", help="Force update of the face database")
    parser.add_argument("--output", type=str, default="output_video.mp4", help="Output path for annotated video")
    parser.add_argument("--exit-cooldown", type=int, default=5, help="Seconds before marking someone as left")
    parser.add_argument("--max-disappeared", type=int, default=50, help="Max frames before deregistering track")
    parser.add_argument("--mysql-host", type=str, default="localhost", help="MySQL host")
    parser.add_argument("--mysql-port", type=int, default=3306, help="MySQL port")
    parser.add_argument("--mysql-user", type=str, default="root", help="MySQL user")
    parser.add_argument("--mysql-password", type=str, default="07112005", help="MySQL password")
    parser.add_argument("--mysql-database", type=str, default="attendance_db", help="MySQL database name")

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


def increased_crop(img, bbox: tuple, bbox_inc: float = 1.5):
    # Crop face based on its bounding box
    real_h, real_w = img.shape[:2]

    x, y, w, h = bbox
    w, h = w - x, h - y
    l = max(w, h)

    xc, yc = x + w / 2, y + h / 2
    x, y = int(xc - l * bbox_inc / 2), int(yc - l * bbox_inc / 2)
    x1 = 0 if x < 0 else x
    y1 = 0 if y < 0 else y
    x2 = real_w if x + l * bbox_inc > real_w else x + int(l * bbox_inc)
    y2 = real_h if y + l * bbox_inc > real_h else y + int(l * bbox_inc)

    img = img[y1:y2, x1:x2, :]
    img = cv2.copyMakeBorder(img,
                             y1 - y, int(l * bbox_inc - y2 + y),
                             x1 - x, int(l * bbox_inc) - x2 + x,
                             cv2.BORDER_CONSTANT, value=[0, 0, 0])
    return img


def make_prediction(img, bbox, anti_spoof):
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    pred = anti_spoof([increased_crop(img, bbox, bbox_inc=1.5)])[0]
    score = pred[0][0]
    label = np.argmax(pred)

    return label, score


def frame_processor(frame: np.ndarray, detector: SCRFD, recognizer: ArcFace, anti_spoofing: AntiSpoof,
                    face_db: FaceDatabase,
                    tracker: CentroidTracker, attendance_tracker: AttendanceTracker, colors: dict,
                    params: argparse.Namespace) -> np.ndarray:
    try:
        bboxes, kpss = detector.detect(frame, params.max_num)
        detections = []  # List of (bbox, name) tuples

        if len(bboxes) > 0:
            # Get embeddings for all faces
            embeddings = []
            processed_bboxes = []

            for bbox, kps in zip(bboxes, kpss):
                try:
                    *bbox_coords, conf_score = bbox.astype(np.int32)
                    embedding = recognizer.get_embedding(frame, kps)
                    embeddings.append(embedding)
                    processed_bboxes.append(bbox_coords)
                except Exception as e:
                    logging.warning(f"Error processing face embedding: {e}")
                    continue

            if embeddings:
                # Batch search for all faces
                results = face_db.batch_search(embeddings, params.similarity_thresh)

                # Prepare detections for tracker
                for bbox, (name, similarity) in zip(processed_bboxes, results):
                    detections.append((bbox, name))

        # Update tracker with detections
        tracked_objects = tracker.update(detections)

        # Update attendance based on tracking
        attendance_tracker.update(tracked_objects)

        # Draw tracking results
        for track_id, (centroid, name) in tracked_objects.items():
            # Find corresponding bbox
            bbox = None
            for det_bbox, det_name in detections:
                x1, y1, x2, y2 = det_bbox
                cx, cy = centroid
                if x1 <= cx <= x2 and y1 <= cy <= y2:
                    bbox = det_bbox
                    break
            if bbox:
                pred = make_prediction(frame, bbox, anti_spoofing)
                x1, y1, x2, y2 = bbox
                if pred is not None:
                    label, score = pred
                    if label == 0:
                        if score > params.confidence_thresh:
                            res_text = "REAL{:.2f}".format(score)
                            color = COLOR_REAL
                        else:
                            res_text = "unknown"
                            color = COLOR_UNKNOWN
                    else:
                        res_text = "FAKE      {:.2f}".format(score)
                        color = COLOR_FAKE
                    cv2.putText(frame, res_text, (x1 + 40, y1 + 10),
                                cv2.FONT_HERSHEY_COMPLEX, 0.6, color, 2)
            if bbox and name != "Unknown":
                status = attendance_tracker.get_status(name)

                if name not in colors:
                    colors[name] = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

                # Draw bbox with tracking info
                x1, y1, x2, y2 = bbox
                color = colors[name]
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

                # Draw label with status
                label = f"ID:{track_id} {name} {status}"
                label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                cv2.rectangle(frame, (x1, y1 - label_size[1] - 10),
                              (x1 + label_size[0], y1), color, -1)
                cv2.putText(frame, label, (x1, y1 - 5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

                # Draw centroid
                cv2.circle(frame, centroid, 4, color, -1)
            elif bbox:
                # Unknown person
                x1, y1, x2, y2 = bbox
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                cv2.putText(frame, f"ID:{track_id} Unknown", (x1, y1 - 5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

    except Exception as e:
        logging.error(f"Error in frame processing: {e}")

    return frame


def main(params):
    try:
        detector = SCRFD(params.det_weight, input_size=(640, 640), conf_thres=params.confidence_thresh)
        recognizer = ArcFace(params.rec_weight)
        anti_spoofing = AntiSpoof(params.spoof_weight)
        attendance_db = AttendanceDatabase(
            host=params.mysql_host,
            port=params.mysql_port,
            user=params.mysql_user,
            password=params.mysql_password,
            database=params.mysql_database
        )
    except Exception as e:
        logging.error(f"Failed to load models or database: {e}")
        return

    with build_face_database(detector, recognizer, params, force_update=params.update_db) as face_db:
        colors = {}
        tracker = CentroidTracker(max_disappeared=params.max_disappeared)
        attendance_tracker = AttendanceTracker(attendance_db, cooldown_seconds=params.exit_cooldown)

        try:
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                raise IOError(f"Could not open video source: {params.source}")

            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            out = cv2.VideoWriter(params.output, cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))

            full_name = input("Registered name (for manual capture, press Enter to skip): ")
            frame_count = 0

            logging.info(" Starting attendance tracking with entry/exit detection...")
            logging.info(f"⏱ Exit cooldown: {params.exit_cooldown} seconds")

            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                start = time.time()
                frame = frame_processor(frame, detector, recognizer, anti_spoofing, face_db, tracker,
                                        attendance_tracker, colors, params)
                end = time.time()

                # Add FPS counter
                fps_text = f"FPS: {1 / (end - start):.1f}"
                cv2.putText(frame, fps_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                            1, (0, 255, 0), 2)

                out.write(frame)
                cv2.imshow("Face Recognition Attendance", frame)

                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('s') and full_name:
                    save_dir = os.path.join("assets/faces", full_name)
                    os.makedirs(save_dir, exist_ok=True)
                    cur_count = len(os.listdir(save_dir))
                    save_path = os.path.join(save_dir, f"{full_name}_{cur_count + 1}.jpg")
                    cv2.imwrite(save_path, frame)
                    logging.info(f"Saved snapshot: {save_path}")
                elif key == ord('b'):
                    face_db = build_face_database(detector, recognizer, params, force_update=True)
                elif key == ord('r'):
                    # Print attendance report
                    report = attendance_db.get_daily_report()
                    print("\n" + "=" * 80)
                    print(f"ATTENDANCE REPORT - {datetime.now().date()}")
                    print("=" * 80)
                    for record in report:
                        print(f"{record['name']:20} | Sessions: {record['total_sessions']:2} | "
                              f"Time: {record['total_minutes']:4}min | "
                              f"Entry: {record['first_entry'].strftime('%H:%M:%S') if record['first_entry'] else 'N/A'}")
                    print("=" * 80 + "\n")

                frame_count += 1

            logging.info(f"Processed {frame_count} frames.")

        except Exception as e:
            logging.error(f"Error during video processing: {e}")
        finally:
            if 'cap' in locals():
                cap.release()
            if 'out' in locals():
                out.release()
            cv2.destroyAllWindows()


if __name__ == '__main__':
    args = parse_args()
    try:
        args.source = int(args.source)
    except ValueError:
        pass
    main(args)