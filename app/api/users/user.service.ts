import {
  ConflictError,
  InternalServerError,
  NotFoundError,
  UnauthorizedError,
} from "@common/errors/httpErrors";
import { db } from "@user/sqlite";
import type {
  CreateUserSchema,
  LoginSchema,
  SignUpSchema,
  UserResponseSchema,
} from "@user/user.model";
import { comparePassword, hashPassword } from "@user/utils/passwordHash";
import type { Static } from "elysia";

type JwtClient = {
  sign: (payload: Record<string, string | number>) => Promise<string>;
  verify: (token: string) => Promise<Record<string, string | number> | false>;
};

type UserFromDb = Static<typeof UserResponseSchema>;

export class UserService {
  private jwt: JwtClient;

  constructor(jwt: JwtClient) {
    this.jwt = jwt;
  }

  async login(credentials: Static<typeof LoginSchema>) {
    const query = db.query<UserFromDb, { $email: string }>(
      "SELECT id, email, password, role FROM users WHERE email = $email",
    );
    const userFromDb = query.get({ $email: credentials.email });

    if (!userFromDb) {
      throw new UnauthorizedError("Invalid email or password.");
    }

    const passwordMatch = await comparePassword(
      credentials.password,
      userFromDb.password,
    );
    if (!passwordMatch) {
      throw new UnauthorizedError("Invalid email or password.");
    }

    const userPayload = {
      id: userFromDb.id,
      email: userFromDb.email,
      role: userFromDb.role,
    };
    const token = await this.jwt.sign(userPayload);

    return { token, user: userPayload };
  }

  async createUser(userData: Static<typeof CreateUserSchema>) {
    const query = db.query<{ id: number }, { $email: string }>(
      "SELECT id FROM users WHERE email = $email",
    );
    const existingEmail = query.get({ $email: userData.email });
    if (existingEmail) {
      throw new ConflictError("A user with this email already exists.");
    }

    const query2 = db.query<{ id: number }, { $username: string }>(
      "SELECT id FROM users WHERE username = $username",
    );
    const existingUsername = query2.get({ $username: userData.username });
    if (existingUsername) {
      throw new ConflictError("A user with this username already exists.");
    }

    const hashedPassword = await hashPassword(userData.password);
    const { email, username, first_name, last_name, dob, role } = userData;

    const insertQuery = db.query<UserFromDb, any>(`
	     INSERT INTO users (email, username, password, first_name, last_name, dob, role)
	     VALUES ($email, $username, $password, $first_name, $last_name, $dob, $role)
	     RETURNING *;
	   `);

    const newUser = insertQuery.get({
      $email: email,
      $username: username,
      $password: hashedPassword,
      $first_name: first_name,
      $last_name: last_name,
      $dob: dob,
      $role: role || "student",
    });

    if (!newUser) {
      throw new InternalServerError(
        "Failed to create user account due to server error.",
      );
    }

    return newUser;
  }

  async getAllUsers() {
    const query = db.query<UserFromDb, []>("SELECT * FROM users");
    const allUsers = query.all();
    return { users: allUsers };
  }

  async getUserById(id: number) {
    const query = db.query<UserFromDb, { $id: number }>(
      "SELECT * FROM users WHERE id = $id",
    );
    const user = query.get({ $id: id });
    if (!user) {
      throw new NotFoundError("User not found.");
    }
    return user;
  }

  async updateUser(id: number, userData: Partial<Static<typeof SignUpSchema>>) {
    const { email, username, password, first_name, last_name, dob } = userData;
    let hashedPassword;
    if (password) {
      hashedPassword = await hashPassword(password);
    }

    const query = db.query<UserFromDb, any>(`
      UPDATE users
      SET
        email = COALESCE($email, email),
        username = COALESCE($username, username),
        password = COALESCE($password, password),
        first_name = COALESCE($first_name, first_name),
        last_name = COALESCE($last_name, last_name),
        dob = COALESCE($dob, dob),
        updated_at = CURRENT_TIMESTAMP
      WHERE id = $id
      RETURNING *;
    `);

    const updatedUser = query.get({
      $id: id,
      $email: email ?? null,
      $username: username ?? null,
      $password: hashedPassword ?? null,
      $first_name: first_name ?? null,
      $last_name: last_name ?? null,
      $dob: dob ?? null,
    });

    if (!updatedUser) {
      throw new NotFoundError("User not found.");
    }
    return updatedUser;
  }

  async deleteUser(id: number) {
    const query = db.query<{ id: number }, { $id: number }>(
      "DELETE FROM users WHERE id = $id RETURNING id",
    );
    const deletedUser = query.get({ $id: id });
    if (!deletedUser) {
      throw new NotFoundError("User not found.");
    }
    return { message: `User with ID ${id} successfully deleted.` };
  }

  async linkParentToStudent(parentId: number, studentId: string) {
    // Check if parent exists
    await this.getUserById(parentId);

    // Check if student exists (using raw query since StudentService is not injected)
    const studentQuery = db.query<{ id: string }, { $id: string }>(
      "SELECT id FROM students WHERE id = $id",
    );
    const student = studentQuery.get({ $id: studentId });
    if (!student) {
      throw new NotFoundError(`Student with ID ${studentId} not found.`);
    }

    // Check if already linked
    const existingLink = db
      .query(
        "SELECT * FROM parent_student WHERE parent_id = $parentId AND student_id = $studentId",
      )
      .get({ $parentId: parentId, $studentId: studentId });

    if (existingLink) {
      return { message: "Parent already linked to this student." };
    }

    const insertQuery = db.query(
      "INSERT INTO parent_student (parent_id, student_id) VALUES ($parentId, $studentId)",
    );
    insertQuery.run({ $parentId: parentId, $studentId: studentId });

    return { message: "Parent successfully linked to student." };
  }

  async getStudentsForParent(parentId: number) {
    const query = db.query(
      `SELECT s.*
	     FROM students s
	     JOIN parent_student ps ON s.id = ps.student_id
	     WHERE ps.parent_id = $parentId`,
    );
    const students = query.all({ $parentId: parentId });
    return { students };
  }

  async getAllParentStudentLinks() {
    const query = db.query(
      `SELECT ps.parent_id, ps.student_id, s.first_name, s.last_name, s.class_id
             FROM parent_student ps
             JOIN students s ON ps.student_id = s.id`,
    );
    const links = query.all();
    return { links };
  }
}
