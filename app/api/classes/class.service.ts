import { InternalServerError, NotFoundError } from "@common/errors/httpErrors";
import { db } from "@user/sqlite";
import type { Static } from "elysia";
import type { ClassSchema, CreateClassSchema } from "./class.model";

type Class = Static<typeof ClassSchema>;
type CreateClass = Static<typeof CreateClassSchema>;

// Type for student info in class listing
interface StudentInfo {
  id: string;
  first_name: string;
  last_name: string;
}

// Type for class with students and teacher info
interface ClassWithDetails extends Class {
  teacher: string | null;
  students: StudentInfo[];
}

// Raw result from database query
interface ClassQueryResult {
  id: number;
  name: string;
  teacher_id: number | null;
  teacher: string | null;
  students: string | null;
}

export class ClassService {
  constructor() {
    this.initDatabase();
  }

  private initDatabase(): void {
    db.run(`
      CREATE TABLE IF NOT EXISTS classes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        teacher_id INTEGER,
        FOREIGN KEY (teacher_id) REFERENCES users(id)
      );
    `);
    db.run(`
      CREATE TABLE IF NOT EXISTS student_classes (
        student_id TEXT NOT NULL,
        class_id INTEGER NOT NULL,
        PRIMARY KEY (student_id, class_id),
        FOREIGN KEY (student_id) REFERENCES students (id),
        FOREIGN KEY (class_id) REFERENCES classes (id)
      );
    `);
  }

  /**
   * Create a new class
   */
  public createClass(classData: CreateClass): Class {
    const query = db.query<Class, { $name: string; $teacher_id: number }>(
      "INSERT INTO classes (name, teacher_id) VALUES ($name, $teacher_id) RETURNING *",
    );
    const newClass = query.get({
      $name: classData.name,
      $teacher_id: classData.teacher_id,
    });

    if (!newClass) {
      throw new InternalServerError(
        "Failed to create class due to a database error.",
      );
    }

    return newClass;
  }

  /**
   * Get a class by ID
   */
  public getClassById(classId: number): Class {
    const query = db.query<Class, { $id: number }>(
      "SELECT * FROM classes WHERE id = $id",
    );
    const classRecord = query.get({ $id: classId });

    if (!classRecord) {
      throw new NotFoundError(`Class with ID ${classId} not found.`);
    }

    return classRecord;
  }

  /**
   * Get all classes with their students and teacher info
   */
  public getClasses(): ClassWithDetails[] {
    const query = db.query<ClassQueryResult, Record<string, never>>(`
      SELECT
        c.id,
        c.name,
        c.teacher_id,
        u.first_name || ' ' || u.last_name as teacher,
        (
          SELECT json_group_array(
            json_object('id', s.id, 'first_name', s.first_name, 'last_name', s.last_name)
          )
          FROM students s
          WHERE s.class_id = c.id
        ) as students
      FROM classes c
      LEFT JOIN users u ON c.teacher_id = u.id
    `);

    const classes = query.all({});

    return classes.map((cls) => ({
      ...cls,
      students: cls.students ? JSON.parse(cls.students) : [],
    }));
  }

  /**
   * Enroll a student in a class
   */
  public enrollStudent(
    studentId: string,
    classId: number,
  ): { message: string } {
    // Verify student exists
    const studentQuery = db.query<{ id: string }, { $id: string }>(
      "SELECT id FROM students WHERE id = $id",
    );
    const student = studentQuery.get({ $id: studentId });

    if (!student) {
      throw new NotFoundError(`Student with ID ${studentId} not found.`);
    }

    // Verify class exists
    const classQuery = db.query<{ id: number }, { $id: number }>(
      "SELECT id FROM classes WHERE id = $id",
    );
    const course = classQuery.get({ $id: classId });

    if (!course) {
      throw new NotFoundError(`Class with ID ${classId} not found.`);
    }

    // Enroll student
    const enrollQuery = db.query(
      "INSERT OR IGNORE INTO student_classes (student_id, class_id) VALUES ($studentId, $classId)",
    );
    enrollQuery.run({ $studentId: studentId, $classId: classId });

    return { message: `Student ${studentId} enrolled in class ${classId}.` };
  }
}
