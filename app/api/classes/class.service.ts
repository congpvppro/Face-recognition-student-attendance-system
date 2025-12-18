import { InternalServerError, NotFoundError } from "@common/errors/httpErrors";
import { db } from "@user/sqlite";
import type { Static } from "elysia";
import type { ClassSchema, CreateClassSchema } from "./class.model";

type Class = Static<typeof ClassSchema>;
type CreateClass = Static<typeof CreateClassSchema>;

// Type for student info in class listing
interface StudentInfo {
  id: string;
  name: string;
  first_name: string;
  last_name: string;
  face_registered: number | null;
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
    // Database tables are now initialized in sqlite.ts
  }

  /**
   * Create a new class
   */
  public createClass(classData: CreateClass): Class {
    // Verify teacher exists
    const teacherQuery = db.query<{ id: number }, { $id: number }>(
      "SELECT id FROM users WHERE id = $id AND role = 'teacher'",
    );
    const teacher = teacherQuery.get({ $id: classData.teacher_id });

    if (!teacher) {
      throw new NotFoundError(
        `Teacher with ID ${classData.teacher_id} not found.`,
      );
    }

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
            json_object('id', s.id, 'name', s.name, 'first_name', s.first_name, 'last_name', s.last_name, 'face_registered', s.face_registered)
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
