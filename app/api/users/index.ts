// Elysia API server

import { ForbiddenError, UnauthorizedError } from "@common/errors/httpErrors";
import { JWT_SECRET } from "@common/config";
import { jwt } from "@elysiajs/jwt";
import { Elysia, t } from "elysia";
import { StudentSchema } from "@student/student.model";
import {
  CreateUserSchema,
  LoginSchema,
  SafeUserResponseSchema,
  SignUpSchema,
  UserResponseSchema,
} from "./user.model";
import { UserService } from "./user.service";

const ErrorSchema = t.Object({
  message: t.String(),
});

export const usersPlugin = new Elysia({})
  .use(jwt({ name: "jwt", secret: JWT_SECRET, exp: "7d" }))
  .resolve(({ jwt }) => ({
    userService: new UserService(jwt as any),
  }))

  .group("/auth", (app) =>
    app
      .post(
        "/login",
        async ({ body, set, cookie, userService }) => {
          const { token, user } = await userService.login(body);

          cookie.auth?.set({
            value: token,
            path: "/",
            httpOnly: true,
            sameSite: "lax",
            maxAge: 60 * 60 * 24 * 7, // 7 days
          });

          set.status = 200;
          return { token, user };
        },
        {
          body: LoginSchema,
          response: {
            200: t.Object({
              token: t.String(),
              user: t.Object({
                id: t.Number(),
                email: t.String(),
                role: t.String(),
              }),
            }),
            401: ErrorSchema,
          },
          detail: {
            tags: ["Authentication"],
            summary: "Log in a user",
          },
        },
      )

      .post(
        "/logout",
        ({ cookie }) => {
          const token = cookie?.auth?.value as string | undefined;

          if (!token) {
            throw new UnauthorizedError("No active session to log out from.");
          }

          cookie.auth?.remove();
          return { ok: true };
        },
        {
          detail: {
            tags: ["Authentication"],
            summary: "Log out the current user",
          },
          response: {
            200: t.Object({ ok: t.Boolean() }),
            401: ErrorSchema,
          },
        },
      ),
  )

  .group("/users", (app) =>
    app
      .post(
        "/",
        async ({ body, set, userService }) => {
          const newUser = await userService.createUser(body);

          set.status = 201;
          return { user: newUser };
        },
        {
          body: CreateUserSchema,
          response: {
            201: t.Object({ user: t.Omit(UserResponseSchema, ["password"]) }),
            409: ErrorSchema,
            500: ErrorSchema,
          },
          detail: {
            tags: ["User Management"],
            summary: "Register a new user",
          },
        },
      )

      .guard(
        {
          beforeHandle: async ({ jwt, cookie }) => {
            const token = cookie?.auth?.value as string | undefined;
            if (!token) {
              throw new UnauthorizedError("Missing token");
            }
            const payload = await jwt.verify(token);
            if (!payload) {
              throw new UnauthorizedError("Invalid or expired token");
            }
          },
        },
        (app) =>
          app
            .resolve(async ({ jwt, cookie }) => {
              const token = cookie?.auth?.value as string | undefined;
              const userPayload = token
                ? ((await jwt.verify(token)) as {
                    id: number;
                    email: string;
                    role: string;
                  } | null)
                : null;
              return { user: userPayload };
            })

            .get(
              "/",
              async ({ user, userService, set }) => {
                if (user?.role !== "admin") {
                  throw new ForbiddenError("Admins only");
                }

                set.headers["Cache-Control"] =
                  "public, max-age=3600, stale-while-revalidate=3600";
                const { users } = await userService.getAllUsers();
                return { users };
              },
              {
                response: {
                  200: t.Object({ users: t.Array(SafeUserResponseSchema) }),
                  403: ErrorSchema,
                },
                detail: {
                  tags: ["User Management"],
                  summary: "Get all users (Admin Only)",
                },
              },
            )

            .get(
              "/me",
              async ({ user, userService }) => {
                if (!user || typeof user.id !== "number") {
                  throw new UnauthorizedError("Invalid user payload");
                }
                const currentUser = await userService.getUserById(user.id);
                return { user: currentUser };
              },
              {
                response: {
                  200: t.Object({
                    user: t.Omit(UserResponseSchema, ["password"]),
                  }),
                  401: ErrorSchema,
                  404: ErrorSchema,
                },
                detail: {
                  tags: ["User Management"],
                  summary: "Get current authenticated user",
                },
              },
            )

            .get(
              "/me/students",
              async ({ user, userService }) => {
                if (!user || typeof user.id !== "number") {
                  throw new UnauthorizedError("Invalid user payload");
                }
                // Allow parents to see their students.
                // Teachers/Admins might have different logic, but if a teacher is also a parent
                // they can see their own kids here.
                return userService.getStudentsForParent(user.id);
              },
              {
                response: {
                  200: t.Object({
                    students: t.Array(StudentSchema),
                  }),
                  401: ErrorSchema,
                },
                detail: {
                  tags: ["User Management"],
                  summary: "Get students linked to the current user (Parent)",
                },
              },
            )

            .post(
              "/parents/link",
              async ({ body, user, userService }) => {
                if (user?.role !== "admin") {
                  throw new ForbiddenError(
                    "Only admins can link parents to students",
                  );
                }
                return userService.linkParentToStudent(
                  body.parentId,
                  body.studentId,
                );
              },
              {
                body: t.Object({
                  parentId: t.Numeric(),
                  studentId: t.String(),
                }),
                response: {
                  200: t.Object({ message: t.String() }),
                  403: ErrorSchema,
                  404: ErrorSchema,
                },
                detail: {
                  tags: ["User Management"],
                  summary: "Link a parent to a student (Admin Only)",
                },
              },
            )

            .get(
              "/parents/links",
              async ({ user, userService }) => {
                if (user?.role !== "admin") {
                  throw new ForbiddenError(
                    "Only admins can view parent-student links",
                  );
                }
                return userService.getAllParentStudentLinks();
              },
              {
                response: {
                  200: t.Object({
                    links: t.Array(
                      t.Object({
                        parent_id: t.Number(),
                        student_id: t.String(),
                        first_name: t.String(),
                        last_name: t.String(),
                        class_id: t.Nullable(t.Number()),
                      }),
                    ),
                  }),
                  403: ErrorSchema,
                },
                detail: {
                  tags: ["User Management"],
                  summary: "Get all parent-student links (Admin Only)",
                },
              },
            )

            .get(
              "/:user_id",
              async ({ params, user, userService }) => {
                if (
                  user?.role !== "admin" &&
                  user?.id !== Number(params.user_id)
                ) {
                  throw new ForbiddenError(
                    "Only admins or the user themselves can access this information",
                  );
                }
                const foundUser = await userService.getUserById(params.user_id);
                return { user: foundUser };
              },
              {
                params: t.Object({ user_id: t.Numeric() }),
                response: {
                  200: t.Object({ user: SafeUserResponseSchema }),
                  403: ErrorSchema,
                  404: ErrorSchema,
                },
                detail: {
                  tags: ["User Management"],
                  summary: "Get user by ID",
                },
              },
            )

            .patch(
              "/:user_id",
              async ({ params, body, user, userService }) => {
                if (
                  user?.role !== "admin" &&
                  user?.id !== Number(params.user_id)
                ) {
                  throw new ForbiddenError(
                    "Only admins or the user themselves can update this information",
                  );
                }
                const updatedUser = await userService.updateUser(
                  params.user_id,
                  body,
                );
                return { user: updatedUser };
              },
              {
                params: t.Object({ user_id: t.Numeric() }),
                body: t.Partial(
                  t.Omit(SignUpSchema, [
                    "id",
                    "password",
                    "role",
                    "created_at",
                    "updated_at",
                  ]),
                ),
                response: {
                  200: t.Object({ user: SafeUserResponseSchema }),
                  404: ErrorSchema,
                },
                detail: {
                  tags: ["User Management"],
                  summary: "Partially update a user account information",
                },
              },
            )

            .delete(
              "/:user_id",
              async ({ params, user, userService }) => {
                if (
                  user?.role !== "admin" &&
                  user?.id !== Number(params.user_id)
                ) {
                  throw new ForbiddenError(
                    "Only admins or the user themselves can delete this account",
                  );
                }

                const result = await userService.deleteUser(params.user_id);
                return { message: result.message };
              },
              {
                params: t.Object({ user_id: t.Numeric() }),
                response: {
                  200: t.Object({ message: t.String() }),
                  404: ErrorSchema,
                },
                detail: {
                  tags: ["User Management"],
                  summary: "Delete a user",
                },
              },
            ),
      ),
  );

export type App = typeof usersPlugin;
