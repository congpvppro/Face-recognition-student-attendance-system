import { db, dbPath } from "../sqlite";

const emailToUpdate = process.argv[2] || "admin@a.b";

interface User {
  id: number;
  email: string;
  role: string;
}

const updateUserRole = () => {
  console.log(`📁 Using database at: ${dbPath}`);
  console.log(`🔍 Looking for user with email: ${emailToUpdate}`);

  try {
    const query = db.query<User, { $email: string }>(
      "SELECT id, email, role FROM users WHERE email = $email",
    );
    const user = query.get({ $email: emailToUpdate });

    if (!user) {
      console.log(`❌ User with email ${emailToUpdate} not found.`);
      console.log("\nAvailable users:");
      const allUsers = db
        .query<
          { email: string; role: string },
          []
        >("SELECT email, role FROM users LIMIT 10")
        .all();
      allUsers.forEach((u) => console.log(`  - ${u.email} (${u.role})`));
      return;
    }

    if (user.role === "admin") {
      console.log(`✅ User ${emailToUpdate} is already an admin.`);
      return;
    }

    const updateQuery = db.query(
      "UPDATE users SET role = $role, updated_at = CURRENT_TIMESTAMP WHERE email = $email",
    );
    updateQuery.run({ $role: "admin", $email: emailToUpdate });

    console.log(`✅ User ${emailToUpdate} has been updated to admin role.`);
  } catch (error) {
    console.error("❌ Failed to update user role:", error);
  }
};

updateUserRole();
