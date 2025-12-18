import sqlite3
import hashlib
import os
from datetime import datetime
from typing import Optional, Dict, List, Any
import logging

class UserDatabase:
    """Database class for user management operations - unified with attendance system"""
    
    def __init__(self, db_path='attendance.db', auto_init=True):
        self.db_path = db_path
        # Ensure directory exists
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        if auto_init:
            self._init_database()
    
    def _init_database(self):
        """Initialize database tables if they don't exist"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Create users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL UNIQUE,
                    username TEXT NOT NULL UNIQUE,
                    password TEXT NOT NULL,
                    first_name TEXT NOT NULL,
                    last_name TEXT NOT NULL,
                    dob TEXT,
                    role TEXT CHECK(role IN ('admin', 'teacher', 'parent', 'student')) NOT NULL DEFAULT 'student',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create classes table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS classes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    teacher_id INTEGER,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (teacher_id) REFERENCES users(id)
                )
            """)
            
            # Create students table with TEXT id for compatibility
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS students (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    first_name TEXT,
                    last_name TEXT,
                    class_id INTEGER,
                    face_registered INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (class_id) REFERENCES classes(id)
                )
            """)
            
            # Add face_registered column if it doesn't exist (for existing databases)
            try:
                cursor.execute("ALTER TABLE students ADD COLUMN face_registered INTEGER DEFAULT 0")
            except sqlite3.OperationalError:
                pass  # Column already exists
            
            # Create parent_student relationship table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS parent_student (
                    parent_id INTEGER NOT NULL,
                    student_id TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (parent_id, student_id),
                    FOREIGN KEY (parent_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
                )
            """)
            
            # Create tickets table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tickets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    parent_id INTEGER NOT NULL,
                    student_id TEXT NOT NULL,
                    teacher_id INTEGER,
                    class_id INTEGER NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending', 'approved', 'rejected')),
                    type TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (parent_id) REFERENCES users(id),
                    FOREIGN KEY (student_id) REFERENCES students(id),
                    FOREIGN KEY (teacher_id) REFERENCES users(id),
                    FOREIGN KEY (class_id) REFERENCES classes(id)
                )
            """)
            
            # Create unregistered_faces table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS unregistered_faces (
                    face_id TEXT PRIMARY KEY,
                    class_id INTEGER NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (class_id) REFERENCES classes(id)
                )
            """)
            
            conn.commit()
            conn.close()
            logging.info(f"User database initialized at {self.db_path}")
            
        except sqlite3.Error as e:
            logging.error(f"Failed to initialize user database: {e}")
            raise
        
    def _get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _hash_password(self, password: str) -> str:
        """Hash password using SHA-256 with salt"""
        salt = os.urandom(32)
        key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        return salt.hex() + key.hex()
    
    def _verify_password(self, password: str, stored_hash: str) -> bool:
        """Verify password against stored hash"""
        try:
            salt = bytes.fromhex(stored_hash[:64])
            stored_key = stored_hash[64:]
            key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
            return key.hex() == stored_key
        except Exception as e:
            logging.error(f"Password verification error: {e}")
            return False
    
    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        """Convert sqlite3.Row to dictionary"""
        if row is None:
            return None
        return dict(row)
    
    def _get_safe_user(self, user: Dict[str, Any]) -> Dict[str, Any]:
        """Return user without password field"""
        if user is None:
            return None
        safe_user = dict(user)
        safe_user.pop('password', None)
        return safe_user

    # ==================== Authentication ====================
    
    def login(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate user with email and password
        Returns user data without password if successful, None otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, email, password, role FROM users WHERE email = ?",
                    (email,)
                )
                user = self._row_to_dict(cursor.fetchone())
                
                if not user:
                    return None
                
                if not self._verify_password(password, user['password']):
                    return None
                
                return {
                    'id': user['id'],
                    'email': user['email'],
                    'role': user['role']
                }
        except sqlite3.Error as e:
            logging.error(f"Login error: {e}")
            return None

    # ==================== User CRUD ====================
    
    def create_user(self, 
                    email: str, 
                    username: str, 
                    password: str, 
                    first_name: str, 
                    last_name: str,
                    dob: Optional[str] = None,
                    role: str = 'student') -> Optional[Dict[str, Any]]:
        """
        Create a new user
        Returns the created user (without password) or None if failed
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if email already exists
                cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
                if cursor.fetchone():
                    logging.warning(f"User with email {email} already exists")
                    return None
                
                # Check if username already exists
                cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
                if cursor.fetchone():
                    logging.warning(f"User with username {username} already exists")
                    return None
                
                hashed_password = self._hash_password(password)
                
                cursor.execute("""
                    INSERT INTO users (email, username, password, first_name, last_name, dob, role)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (email, username, hashed_password, first_name, last_name, dob, role))
                
                conn.commit()
                
                # Fetch the created user
                cursor.execute("SELECT * FROM users WHERE id = ?", (cursor.lastrowid,))
                user = self._row_to_dict(cursor.fetchone())
                
                logging.info(f"Created user: {username} (ID: {user['id']})")
                return self._get_safe_user(user)
                
        except sqlite3.Error as e:
            logging.error(f"Create user error: {e}")
            return None

    def get_all_users(self) -> List[Dict[str, Any]]:
        """Get all users (without passwords)"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users")
                users = [self._row_to_dict(row) for row in cursor.fetchall()]
                return [self._get_safe_user(user) for user in users]
        except sqlite3.Error as e:
            logging.error(f"Get all users error: {e}")
            return []

    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID (without password)"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
                user = self._row_to_dict(cursor.fetchone())
                return self._get_safe_user(user)
        except sqlite3.Error as e:
            logging.error(f"Get user by ID error: {e}")
            return None

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email (without password)"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
                user = self._row_to_dict(cursor.fetchone())
                return self._get_safe_user(user)
        except sqlite3.Error as e:
            logging.error(f"Get user by email error: {e}")
            return None

    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username (without password)"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
                user = self._row_to_dict(cursor.fetchone())
                return self._get_safe_user(user)
        except sqlite3.Error as e:
            logging.error(f"Get user by username error: {e}")
            return None

    def get_users_by_role(self, role: str) -> List[Dict[str, Any]]:
        """Get all users with a specific role"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE role = ?", (role,))
                users = [self._row_to_dict(row) for row in cursor.fetchall()]
                return [self._get_safe_user(user) for user in users]
        except sqlite3.Error as e:
            logging.error(f"Get users by role error: {e}")
            return []

    def update_user(self, 
                    user_id: int,
                    email: Optional[str] = None,
                    username: Optional[str] = None,
                    password: Optional[str] = None,
                    first_name: Optional[str] = None,
                    last_name: Optional[str] = None,
                    dob: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Update user fields
        Only provided fields will be updated
        Returns updated user (without password) or None if failed
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Build dynamic update query
                updates = []
                params = []
                
                if email is not None:
                    updates.append("email = ?")
                    params.append(email)
                if username is not None:
                    updates.append("username = ?")
                    params.append(username)
                if password is not None:
                    updates.append("password = ?")
                    params.append(self._hash_password(password))
                if first_name is not None:
                    updates.append("first_name = ?")
                    params.append(first_name)
                if last_name is not None:
                    updates.append("last_name = ?")
                    params.append(last_name)
                if dob is not None:
                    updates.append("dob = ?")
                    params.append(dob)
                
                if not updates:
                    return self.get_user_by_id(user_id)
                
                updates.append("updated_at = CURRENT_TIMESTAMP")
                params.append(user_id)
                
                query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
                cursor.execute(query, params)
                conn.commit()
                
                if cursor.rowcount == 0:
                    logging.warning(f"User with ID {user_id} not found")
                    return None
                
                return self.get_user_by_id(user_id)
                
        except sqlite3.Error as e:
            logging.error(f"Update user error: {e}")
            return None

    def update_user_role(self, user_id: int, role: str) -> Optional[Dict[str, Any]]:
        """Update user role"""
        valid_roles = ['admin', 'teacher', 'parent', 'student']
        if role not in valid_roles:
            logging.error(f"Invalid role: {role}")
            return None
            
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE users SET role = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (role, user_id)
                )
                conn.commit()
                
                if cursor.rowcount == 0:
                    return None
                    
                return self.get_user_by_id(user_id)
        except sqlite3.Error as e:
            logging.error(f"Update user role error: {e}")
            return None

    def delete_user(self, user_id: int) -> bool:
        """Delete user by ID"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
                conn.commit()
                
                if cursor.rowcount == 0:
                    logging.warning(f"User with ID {user_id} not found")
                    return False
                    
                logging.info(f"Deleted user with ID {user_id}")
                return True
        except sqlite3.Error as e:
            logging.error(f"Delete user error: {e}")
            return False

    # ==================== Parent-Student Relationships ====================
    
    def link_parent_to_student(self, parent_id: int, student_id: str) -> bool:
        """
        Link a parent user to a student
        Returns True if successful, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if parent exists and is a parent role
                cursor.execute("SELECT id, role FROM users WHERE id = ?", (parent_id,))
                parent = cursor.fetchone()
                if not parent:
                    logging.warning(f"Parent with ID {parent_id} not found")
                    return False
                
                # Check if student exists
                cursor.execute("SELECT id FROM students WHERE id = ?", (student_id,))
                if not cursor.fetchone():
                    logging.warning(f"Student with ID {student_id} not found")
                    return False
                
                # Check if already linked
                cursor.execute(
                    "SELECT * FROM parent_student WHERE parent_id = ? AND student_id = ?",
                    (parent_id, student_id)
                )
                if cursor.fetchone():
                    logging.info(f"Parent {parent_id} already linked to student {student_id}")
                    return True
                
                # Create link
                cursor.execute(
                    "INSERT INTO parent_student (parent_id, student_id) VALUES (?, ?)",
                    (parent_id, student_id)
                )
                conn.commit()
                
                logging.info(f"Linked parent {parent_id} to student {student_id}")
                return True
                
        except sqlite3.Error as e:
            logging.error(f"Link parent to student error: {e}")
            return False

    def unlink_parent_from_student(self, parent_id: int, student_id: str) -> bool:
        """Remove parent-student link"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM parent_student WHERE parent_id = ? AND student_id = ?",
                    (parent_id, student_id)
                )
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            logging.error(f"Unlink parent from student error: {e}")
            return False

    def get_students_for_parent(self, parent_id: int) -> List[Dict[str, Any]]:
        """Get all students linked to a parent"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT s.*
                    FROM students s
                    JOIN parent_student ps ON s.id = ps.student_id
                    WHERE ps.parent_id = ?
                """, (parent_id,))
                return [self._row_to_dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logging.error(f"Get students for parent error: {e}")
            return []

    def get_parents_for_student(self, student_id: str) -> List[Dict[str, Any]]:
        """Get all parents linked to a student"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT u.*
                    FROM users u
                    JOIN parent_student ps ON u.id = ps.parent_id
                    WHERE ps.student_id = ?
                """, (student_id,))
                users = [self._row_to_dict(row) for row in cursor.fetchall()]
                return [self._get_safe_user(user) for user in users]
        except sqlite3.Error as e:
            logging.error(f"Get parents for student error: {e}")
            return []

    def get_all_parent_student_links(self) -> List[Dict[str, Any]]:
        """Get all parent-student relationships with details"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT ps.parent_id, ps.student_id,
                           COALESCE(s.first_name, s.name, '') as first_name,
                           COALESCE(s.last_name, '') as last_name,
                           s.class_id
                    FROM parent_student ps
                    JOIN students s ON ps.student_id = s.id
                    JOIN users u ON ps.parent_id = u.id
                """)
                return [self._row_to_dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logging.error(f"Get all parent student links error: {e}")
            return []

    # ==================== Utility Methods ====================
    
    def user_exists(self, email: str = None, username: str = None) -> bool:
        """Check if user exists by email or username"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                if email:
                    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
                    if cursor.fetchone():
                        return True
                if username:
                    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
                    if cursor.fetchone():
                        return True
                return False
        except sqlite3.Error as e:
            logging.error(f"User exists check error: {e}")
            return False

    def count_users(self, role: Optional[str] = None) -> int:
        """Count users, optionally filtered by role"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                if role:
                    cursor.execute("SELECT COUNT(*) FROM users WHERE role = ?", (role,))
                else:
                    cursor.execute("SELECT COUNT(*) FROM users")
                result = cursor.fetchone()
                return result[0] if result else 0
        except sqlite3.Error as e:
            logging.error(f"Count users error: {e}")
            return 0

    # ==================== Ticket Methods ====================
    
    def create_ticket(self, parent_id: int, student_id: str, class_id: int,
                      ticket_type: str, reason: str) -> Optional[Dict[str, Any]]:
        """Create a new ticket"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Get teacher_id from class
                cursor.execute("SELECT teacher_id FROM classes WHERE id = ?", (class_id,))
                class_row = cursor.fetchone()
                teacher_id = class_row['teacher_id'] if class_row else None
                
                cursor.execute("""
                    INSERT INTO tickets (parent_id, student_id, teacher_id, class_id, type, reason)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (parent_id, student_id, teacher_id, class_id, ticket_type, reason))
                
                conn.commit()
                
                cursor.execute("SELECT * FROM tickets WHERE id = ?", (cursor.lastrowid,))
                return self._row_to_dict(cursor.fetchone())
                
        except sqlite3.Error as e:
            logging.error(f"Create ticket error: {e}")
            return None

    def get_tickets_for_parent(self, parent_id: int) -> List[Dict[str, Any]]:
        """Get all tickets for a parent"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT t.*, s.name as student_name, s.first_name as student_first_name,
                           s.last_name as student_last_name, c.name as class_name,
                           u.first_name as teacher_first_name, u.last_name as teacher_last_name
                    FROM tickets t
                    JOIN students s ON t.student_id = s.id
                    JOIN classes c ON t.class_id = c.id
                    LEFT JOIN users u ON t.teacher_id = u.id
                    WHERE t.parent_id = ?
                    ORDER BY t.created_at DESC
                """, (parent_id,))
                return [self._row_to_dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logging.error(f"Get tickets for parent error: {e}")
            return []

    def get_tickets_for_teacher(self, teacher_id: int) -> List[Dict[str, Any]]:
        """Get all tickets for a teacher"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT t.*, s.name as student_name, s.first_name as student_first_name,
                           s.last_name as student_last_name, c.name as class_name,
                           p.first_name as parent_first_name, p.last_name as parent_last_name
                    FROM tickets t
                    JOIN students s ON t.student_id = s.id
                    JOIN classes c ON t.class_id = c.id
                    JOIN users p ON t.parent_id = p.id
                    WHERE t.teacher_id = ?
                    ORDER BY t.status ASC, t.created_at DESC
                """, (teacher_id,))
                return [self._row_to_dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logging.error(f"Get tickets for teacher error: {e}")
            return []

    def update_ticket_status(self, ticket_id: int, status: str, teacher_id: int) -> Optional[Dict[str, Any]]:
        """Update ticket status (approved/rejected)"""
        if status not in ['approved', 'rejected']:
            logging.error(f"Invalid ticket status: {status}")
            return None
            
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE tickets
                    SET status = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ? AND teacher_id = ?
                """, (status, ticket_id, teacher_id))
                conn.commit()
                
                if cursor.rowcount == 0:
                    return None
                
                cursor.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
                return self._row_to_dict(cursor.fetchone())
        except sqlite3.Error as e:
            logging.error(f"Update ticket status error: {e}")
            return None

    # ==================== Class Methods ====================
    
    def create_class(self, name: str, teacher_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Create a new class"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO classes (name, teacher_id) VALUES (?, ?)",
                    (name, teacher_id)
                )
                conn.commit()
                cursor.execute("SELECT * FROM classes WHERE id = ?", (cursor.lastrowid,))
                return self._row_to_dict(cursor.fetchone())
        except sqlite3.Error as e:
            logging.error(f"Create class error: {e}")
            return None

    def get_all_classes(self) -> List[Dict[str, Any]]:
        """Get all classes"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT c.*, u.first_name || ' ' || u.last_name as teacher_name
                    FROM classes c
                    LEFT JOIN users u ON c.teacher_id = u.id
                """)
                return [self._row_to_dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logging.error(f"Get all classes error: {e}")
            return []

    def get_class_by_id(self, class_id: int) -> Optional[Dict[str, Any]]:
        """Get class by ID"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM classes WHERE id = ?", (class_id,))
                return self._row_to_dict(cursor.fetchone())
        except sqlite3.Error as e:
            logging.error(f"Get class by ID error: {e}")
            return None

    # ==================== Student Methods ====================
    
    def create_student(self, student_id: str, name: str, first_name: str,
                       last_name: str, class_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Create a new student"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO students (id, name, first_name, last_name, class_id)
                    VALUES (?, ?, ?, ?, ?)
                """, (student_id, name, first_name, last_name, class_id))
                conn.commit()
                cursor.execute("SELECT * FROM students WHERE id = ?", (student_id,))
                return self._row_to_dict(cursor.fetchone())
        except sqlite3.Error as e:
            logging.error(f"Create student error: {e}")
            return None

    def get_all_students(self) -> List[Dict[str, Any]]:
        """Get all students"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT s.*, c.name as class_name
                    FROM students s
                    LEFT JOIN classes c ON s.class_id = c.id
                """)
                return [self._row_to_dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logging.error(f"Get all students error: {e}")
            return []

    def get_student_by_id(self, student_id: str) -> Optional[Dict[str, Any]]:
        """Get student by ID"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM students WHERE id = ?", (student_id,))
                return self._row_to_dict(cursor.fetchone())
        except sqlite3.Error as e:
            logging.error(f"Get student by ID error: {e}")
            return None

    def get_students_by_class(self, class_id: int) -> List[Dict[str, Any]]:
        """Get all students in a class"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM students WHERE class_id = ?", (class_id,))
                return [self._row_to_dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logging.error(f"Get students by class error: {e}")
            return []

    def update_student_face_registered(self, student_id: str, face_registered: bool) -> bool:
        """Update student's face_registered status"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE students SET face_registered = ? WHERE id = ?",
                    (1 if face_registered else 0, student_id)
                )
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            logging.error(f"Update student face_registered error: {e}")
            return False

    # ==================== Unregistered Faces Methods ====================
    
    def create_unregistered_face(self, face_id: str, class_id: int) -> Optional[Dict[str, Any]]:
        """Create a new unregistered face record"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO unregistered_faces (face_id, class_id)
                    VALUES (?, ?)
                """, (face_id, class_id))
                conn.commit()
                cursor.execute("SELECT * FROM unregistered_faces WHERE face_id = ?", (face_id,))
                return self._row_to_dict(cursor.fetchone())
        except sqlite3.Error as e:
            logging.error(f"Create unregistered face error: {e}")
            return None

    def get_unregistered_face(self, face_id: str) -> Optional[Dict[str, Any]]:
        """Get unregistered face by face_id"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM unregistered_faces WHERE face_id = ?", (face_id,))
                return self._row_to_dict(cursor.fetchone())
        except sqlite3.Error as e:
            logging.error(f"Get unregistered face error: {e}")
            return None

    def get_all_unregistered_faces(self) -> List[Dict[str, Any]]:
        """Get all unregistered faces with class information"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT uf.*, c.name as class_name
                    FROM unregistered_faces uf
                    LEFT JOIN classes c ON uf.class_id = c.id
                    ORDER BY uf.created_at DESC
                """)
                return [self._row_to_dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logging.error(f"Get all unregistered faces error: {e}")
            return []

    def get_unregistered_faces_by_class(self, class_id: int) -> List[Dict[str, Any]]:
        """Get all unregistered faces for a specific class"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM unregistered_faces WHERE class_id = ?
                    ORDER BY created_at DESC
                """, (class_id,))
                return [self._row_to_dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logging.error(f"Get unregistered faces by class error: {e}")
            return []

    def delete_unregistered_face(self, face_id: str) -> bool:
        """Delete unregistered face record"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM unregistered_faces WHERE face_id = ?", (face_id,))
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            logging.error(f"Delete unregistered face error: {e}")
            return False