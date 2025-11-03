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

from database import FaceDatabase
from models import SCRFD, ArcFace
from utils.logging import setup_logging
from utils.helpers import compute_similarity, draw_bbox_info, draw_bbox

warnings.filterwarnings("ignore")
setup_logging(log_to_file=True)


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
            # Connect without specifying database first
            conn = mysql.connector.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password
            )
            cursor = conn.cursor()

            # Create database if it doesn't exist
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

            # Create attendance table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS attendance (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    student_id INT NOT NULL,
                    attendance_date DATE NOT NULL,
                    first_seen_time TIME NOT NULL,
                    last_seen_time TIME NOT NULL,
                    attendance_count INT DEFAULT 1,
                    FOREIGN KEY (student_id) REFERENCES students(id),
                    UNIQUE KEY unique_attendance (student_id, attendance_date)
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

    def add_student(self, name):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT IGNORE INTO students (name) VALUES (%s)",
                    (name,)
                )
                cursor.close()
                logging.info(f"Student {name} added to database")
        except mysql.connector.Error as e:
            logging.error(f"Error adding student: {e}")

    def record_attendance(self, name):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Get or create student
                cursor.execute("SELECT id FROM students WHERE name = %s", (name,))
                result = cursor.fetchone()

                if not result:
                    cursor.execute("INSERT INTO students (name) VALUES (%s)", (name,))
                    student_id = cursor.lastrowid
                else:
                    student_id = result[0]

                # Get current date and time
                current_date = datetime.now().date()
                current_time = datetime.now().time()

                # Check if attendance exists for today
                cursor.execute("""
                    SELECT id, attendance_count FROM attendance 
                    WHERE student_id = %s AND attendance_date = %s
                """, (student_id, current_date))

                attendance_record = cursor.fetchone()

                if attendance_record:
                    # Update existing record
                    attendance_id, count = attendance_record
                    cursor.execute("""
                        UPDATE attendance 
                        SET last_seen_time = %s, attendance_count = attendance_count + 1
                        WHERE id = %s
                    """, (current_time, attendance_id))
                    new_count = count + 1
                    logging.info(f"Updated attendance for {name}: count = {new_count}")
                else:
                    # Create new record
                    cursor.execute("""
                        INSERT INTO attendance 
                        (student_id, attendance_date, first_seen_time, last_seen_time, attendance_count)
                        VALUES (%s, %s, %s, %s, 1)
                    """, (student_id, current_date, current_time, current_time))
                    new_count = 1
                    logging.info(f"New attendance record for {name}: count = 1")

                cursor.close()
                return new_count

        except mysql.connector.Error as e:
            logging.error(f"Error recording attendance: {e}")
            return None

    def get_today_attendance(self, name):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                current_date = datetime.now().date()

                cursor.execute("""
                    SELECT a.attendance_count 
                    FROM attendance a
                    JOIN students s ON a.student_id = s.id
                    WHERE s.name = %s AND a.attendance_date = %s
                """, (name, current_date))

                result = cursor.fetchone()
                cursor.close()

                return result[0] if result else 0

        except mysql.connector.Error as e:
            logging.error(f"Error getting attendance: {e}")
            return 0

    def get_attendance_report(self, date=None):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                target_date = date or datetime.now().date()

                cursor.execute("""
                    SELECT s.name, a.first_seen_time, a.last_seen_time, a.attendance_count
                    FROM attendance a
                    JOIN students s ON a.student_id = s.id
                    WHERE a.attendance_date = %s
                    ORDER BY s.name
                """, (target_date,))

                results = cursor.fetchall()
                cursor.close()
                return results

        except mysql.connector.Error as e:
            logging.error(f"Error getting attendance report: {e}")
            return []


def parse_args():
    parser = argparse.ArgumentParser(description="Face Detection-and-Recognition with FAISS")

    parser.add_argument("--det-weight", type=str, default="./weights/det_500m.onnx", help="Path to detection model")
    parser.add_argument("--rec-weight", type=str, default="./weights/w600k_mbf.onnx", help="Path to recognition model")
    parser.add_argument("--similarity-thresh", type=float, default=0.4, help="Similarity threshold between faces")
    parser.add_argument("--confidence-thresh", type=float, default=0.5, help="Confidence threshold for face detection")
    parser.add_argument("--faces-dir", type=str, default="./assets/faces", help="Path to faces stored dir")
    parser.add_argument("--source", type=str, default="./assets/in_video.mp4", help="Video file or webcam source")
    parser.add_argument("--max-num", type=int, default=0, help="Maximum number of face detections from a frame")
    parser.add_argument(
        "--db-path",
        type=str,
        default="./database/face_database",
        help="path to vector db and metadata"
    )
    parser.add_argument("--update-db", action="store_true", help="Force update of the face database")
    parser.add_argument("--output", type=str, default="output_video.mp4", help="Output path for annotated video")
    parser.add_argument("--attendance-cooldown", type=int, default=300,
                        help="Cooldown in seconds between attendance records")
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

        face_db.add_face(out_vec, person_name)

    face_db.save()
    logging.info(f"Face database built successfully with {face_db.index.ntotal} face embeddings")
    return face_db


def frame_processor(frame: np.ndarray, detector: SCRFD, recognizer: ArcFace, face_db: FaceDatabase,
                    attendance_db: AttendanceDatabase, colors: dict, last_seen: dict,
                    params: argparse.Namespace) -> np.ndarray:
    try:
        bboxes, kpss = detector.detect(frame, params.max_num)

        if len(bboxes) == 0:
            return frame

        embeddings = []
        processed_bboxes = []
        current_time = time.time()

        for bbox, kps in zip(bboxes, kpss):
            try:
                *bbox_coords, conf_score = bbox.astype(np.int32)
                embedding = recognizer.get_embedding(frame, kps)
                embeddings.append(embedding)
                processed_bboxes.append(bbox_coords)
            except Exception as e:
                logging.warning(f"Error processing face embedding: {e}")
                continue

        if not embeddings:
            return frame

        results = face_db.batch_search(embeddings, params.similarity_thresh)

        for bbox, (name, similarity) in zip(processed_bboxes, results):
            if name != "Unknown":
                if name not in last_seen or (current_time - last_seen[name]) >= params.attendance_cooldown:
                    # Record attendance in MySQL
                    count = attendance_db.record_attendance(name)
                    last_seen[name] = current_time
                    logging.info(f"Attendance recorded for {name} (Count: {count})")

                attendance_count = attendance_db.get_today_attendance(name)

                if name not in colors:
                    colors[name] = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
                draw_bbox_info(frame, bbox, similarity=similarity, name=f"{name} (#{attendance_count})",
                               color=colors[name])
            else:
                draw_bbox_info(frame, bbox, similarity=similarity, name="Unknown", color=(0, 0, 255))

    except Exception as e:
        logging.error(f"Error in frame processing: {e}")

    return frame


def register_face(params):
    try:
        detector = SCRFD(params.det_weight, input_size=(640, 640), conf_thres=params.confidence_thresh)
        recognizer = ArcFace(params.rec_weight)
        attendance_db = AttendanceDatabase(
            host=params.mysql_host,
            port=params.mysql_port,
            user=params.mysql_user,
            password=params.mysql_password,
            database=params.mysql_database
        )
    except Exception as e:
        logging.error(f"Failed to load model weights: {e}")
        return
    with build_face_database(detector, recognizer, params, force_update=params.update_db) as face_db:
        colors = {}
        last_seen = {}
        try:
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                raise IOError(f"Could not open video source: {params.source}")

            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            out = cv2.VideoWriter(params.output, cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))
            full_name = input("Registered name: ")
            frame_count = 0
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                start = time.time()
                frame = frame_processor(frame, detector, recognizer, face_db, attendance_db, colors, last_seen, params)
                end = time.time()

                out.write(frame)
                cv2.imshow("Face Recognition", frame)
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

                    report = attendance_db.get_attendance_report()
                    print("\n" + "=" * 60)
                    print(f"ATTENDANCE REPORT - {datetime.now().date()}")
                    print("=" * 60)
                    for record in report:
                        print(f"{record['name']:20} | Count: {record['attendance_count']:3} | "
                              f"First: {record['first_seen_time']} | Last: {record['last_seen_time']}")
                    print("=" * 60 + "\n")
            frame_count += 1
            logging.debug(f"Frame {frame_count}, FPS: {1 / (end - start):.2f}")

            logging.info(f"Processed {frame_count} frames.")

        except Exception as e:
            logging.error(f"Error during video processing: {e}")
        finally:
            if 'cap' in locals():
                cap.release()
            if 'out' in locals():
                out.release()
            cv2.destroyAllWindows()

            print("\n" + "=" * 60)
            print("FINAL ATTENDANCE SUMMARY")
            print("=" * 60)
            report = attendance_db.get_attendance_report()
            for record in report:
                print(f"{record['name']:20} | Total Count: {record['attendance_count']}")
            print("=" * 60 + "\n")


if __name__ == "__main__":
    args = parse_args()
    try:
        args.source = int(args.source)
    except ValueError:
        pass
    register_face(args)
