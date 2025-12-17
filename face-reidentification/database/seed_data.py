"""
Seed script to populate the attendance database with sample data.
Run this after initializing the database to add sample users, classes, and relationships.
"""
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import UserDatabase

def seed_database(db_path: str = None):
    """Seed the database with sample data"""
    
    if db_path is None:
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "attendance.db")
    
    print(f"Seeding database at: {db_path}")
    
    # Initialize UserDatabase (this also creates tables if they don't exist)
    user_db = UserDatabase(db_path=db_path)
    
    # ==================== Create Sample Users ====================
    
    # Admin user
    admin = user_db.create_user(
        email="admin@school.edu",
        username="admin",
        password="admin123",
        first_name="System",
        last_name="Administrator",
        role="admin"
    )
    if admin:
        print(f"✅ Created admin user: {admin['email']}")
    else:
        print("ℹ️  Admin user already exists or failed to create")
    
    # Teachers
    teachers_data = [
        {"email": "teacher1@school.edu", "username": "teacher1", "password": "teacher123",
         "first_name": "John", "last_name": "Williams"},
        {"email": "teacher2@school.edu", "username": "teacher2", "password": "teacher123",
         "first_name": "Mary", "last_name": "Johnson"},
        {"email": "teacher3@school.edu", "username": "teacher3", "password": "teacher123",
         "first_name": "Robert", "last_name": "Davis"},
    ]
    
    teacher_ids = []
    for t in teachers_data:
        teacher = user_db.create_user(
            email=t["email"],
            username=t["username"],
            password=t["password"],
            first_name=t["first_name"],
            last_name=t["last_name"],
            role="teacher"
        )
        if teacher:
            teacher_ids.append(teacher["id"])
            print(f"✅ Created teacher: {teacher['email']}")
        else:
            # Try to get existing teacher ID
            existing_teacher = user_db.get_user_by_email(t["email"])
            if existing_teacher:
                teacher_ids.append(existing_teacher["id"])
                print(f"ℹ️  Teacher {t['email']} already exists (ID: {existing_teacher['id']})")
            else:
                print(f"❌ Failed to create or find teacher {t['email']}")
    
    # Parents
    parents_data = [
        {"email": "parent1@email.com", "username": "parent1", "password": "parent123",
         "first_name": "Alice", "last_name": "Smith"},
        {"email": "parent2@email.com", "username": "parent2", "password": "parent123",
         "first_name": "Bob", "last_name": "Johnson"},
        {"email": "parent3@email.com", "username": "parent3", "password": "parent123",
         "first_name": "Carol", "last_name": "Brown"},
        {"email": "parent4@email.com", "username": "parent4", "password": "parent123",
         "first_name": "David", "last_name": "Davis"},
        {"email": "parent5@email.com", "username": "parent5", "password": "parent123",
         "first_name": "Eve", "last_name": "Wilson"},
    ]
    
    parent_ids = []
    for p in parents_data:
        parent = user_db.create_user(
            email=p["email"],
            username=p["username"],
            password=p["password"],
            first_name=p["first_name"],
            last_name=p["last_name"],
            role="parent"
        )
        if parent:
            parent_ids.append(parent["id"])
            print(f"✅ Created parent: {parent['email']}")
        else:
            # Try to get existing parent ID
            existing_parent = user_db.get_user_by_email(p["email"])
            if existing_parent:
                parent_ids.append(existing_parent["id"])
                print(f"ℹ️  Parent {p['email']} already exists (ID: {existing_parent['id']})")
            else:
                print(f"❌ Failed to create or find parent {p['email']}")
    
    
    # ==================== Create Classes ====================
    
    # Only create classes if we have teacher IDs
    if not teacher_ids:
        print("⚠️  No teachers found, creating classes without teachers")
    
    classes_data = [
        {"name": "Mathematics 101", "teacher_id": teacher_ids[0] if len(teacher_ids) > 0 else None},
        {"name": "Physics 101", "teacher_id": teacher_ids[1] if len(teacher_ids) > 1 else None},
        {"name": "Chemistry 101", "teacher_id": teacher_ids[2] if len(teacher_ids) > 2 else None},
    ]
    
    class_ids = []
    for c in classes_data:
        cls = user_db.create_class(name=c["name"], teacher_id=c["teacher_id"])
        if cls:
            class_ids.append(cls["id"])
            print(f"✅ Created class: {cls['name']} (ID: {cls['id']}, Teacher ID: {c['teacher_id']})")
        else:
            # Try to get existing class ID
            existing_classes = user_db.get_all_classes()
            existing = next((ec for ec in existing_classes if ec['name'] == c['name']), None)
            if existing:
                class_ids.append(existing["id"])
                print(f"ℹ️  Class {c['name']} already exists (ID: {existing['id']})")
            else:
                print(f"❌ Failed to create or find class {c['name']}")
    
    # ==================== Create Students ====================
    
    # Some students have face_registered=1 to simulate having their faces registered
    students_data = [
        {"id": "STU001", "name": "John Smith", "first_name": "John", "last_name": "Smith", "face_registered": 1},
        {"id": "STU002", "name": "Emily Johnson", "first_name": "Emily", "last_name": "Johnson", "face_registered": 1},
        {"id": "STU003", "name": "Michael Brown", "first_name": "Michael", "last_name": "Brown", "face_registered": 0},
        {"id": "STU004", "name": "Sarah Davis", "first_name": "Sarah", "last_name": "Davis", "face_registered": 1},
        {"id": "STU005", "name": "David Wilson", "first_name": "David", "last_name": "Wilson", "face_registered": 0},
        {"id": "STU006", "name": "Jennifer Miller", "first_name": "Jennifer", "last_name": "Miller", "face_registered": 1},
        {"id": "STU007", "name": "Christopher Moore", "first_name": "Christopher", "last_name": "Moore", "face_registered": 0},
        {"id": "STU008", "name": "Jessica Taylor", "first_name": "Jessica", "last_name": "Taylor", "face_registered": 1},
        {"id": "STU009", "name": "Matthew Anderson", "first_name": "Matthew", "last_name": "Anderson", "face_registered": 0},
        {"id": "STU010", "name": "Ashley Thomas", "first_name": "Ashley", "last_name": "Thomas", "face_registered": 0},
    ]
    
    student_ids = []
    for i, s in enumerate(students_data):
        # Assign students to classes in round-robin fashion
        class_id = class_ids[i % len(class_ids)] if class_ids else None
        student = user_db.create_student(
            student_id=s["id"],
            name=s["name"],
            first_name=s["first_name"],
            last_name=s["last_name"],
            class_id=class_id
        )
        if student:
            student_ids.append(student["id"])
            # Update face_registered status
            if s.get("face_registered"):
                user_db.update_student_face_registered(student["id"], True)
            print(f"✅ Created student: {student['name']} (ID: {student['id']}, Face: {'✓' if s.get('face_registered') else '✗'})")
        else:
            # Try to get existing student ID
            existing_student = user_db.get_student_by_id(s["id"])
            if existing_student:
                student_ids.append(existing_student["id"])
                print(f"ℹ️  Student {s['id']} already exists")
            else:
                print(f"❌ Failed to create or find student {s['id']}")
    
    # ==================== Link Parents to Students ====================
    
    # Link each parent to 2 students
    if parent_ids and student_ids:
        links = [
            (parent_ids[0], student_ids[0]),
            (parent_ids[0], student_ids[1]),
            (parent_ids[1], student_ids[2]),
            (parent_ids[1], student_ids[3]),
            (parent_ids[2], student_ids[4]),
            (parent_ids[2], student_ids[5]),
            (parent_ids[3], student_ids[6]),
            (parent_ids[3], student_ids[7]),
            (parent_ids[4], student_ids[8]) if len(student_ids) > 8 else None,
            (parent_ids[4], student_ids[9]) if len(student_ids) > 9 else None,
        ]
        
        for link in links:
            if link:
                parent_id, student_id = link
                success = user_db.link_parent_to_student(parent_id, student_id)
                if success:
                    print(f"✅ Linked parent {parent_id} to student {student_id}")
                else:
                    print(f"ℹ️  Link parent {parent_id} to student {student_id} failed or already exists")
    
    print("\n" + "="*50)
    print("Database seeding completed!")
    print("="*50)
    
    # Print summary
    print(f"\nUsers: {user_db.count_users()}")
    print(f"  - Admins: {user_db.count_users('admin')}")
    print(f"  - Teachers: {user_db.count_users('teacher')}")
    print(f"  - Parents: {user_db.count_users('parent')}")
    print(f"  - Students (users): {user_db.count_users('student')}")
    print(f"\nClasses: {len(user_db.get_all_classes())}")
    print(f"Students: {len(user_db.get_all_students())}")
    
    print("\n" + "="*50)
    print("Sample Login Credentials:")
    print("="*50)
    print("Admin:   admin@school.edu / admin123")
    print("Teacher: teacher1@school.edu / teacher123")
    print("Parent:  parent1@email.com / parent123")
    print("="*50)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Seed the attendance database with sample data")
    parser.add_argument("--db-path", type=str, help="Path to the database file")
    args = parser.parse_args()
    
    seed_database(args.db_path)