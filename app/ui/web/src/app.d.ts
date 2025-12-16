// See https://svelte.dev/docs/kit/types#app.d.ts
// for information about these interfaces

declare global {
  namespace App {
    // interface Error {}
    interface Locals {
      user: User | null;
    }
    // interface Platform {}
    interface PageData {
      user?: User; // Available in +page.svelte and components
    }

    interface User {
      id: number;
      username: string;
      email: string;
      first_name: string;
      last_name: string;
      role: "admin" | "teacher" | "parent" | "student";
      dob: string | null;
      created_at: string;
      updated_at: string;
    }
  }
}

export {};
