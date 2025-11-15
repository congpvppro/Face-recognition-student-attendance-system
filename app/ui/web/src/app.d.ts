// See https://svelte.dev/docs/kit/types#app.d.ts
// for information about these interfaces

declare global {
	namespace App {
		// interface Error {}
		interface Locals {
			user: User | null;
		}
		// interface PageData {}
		// interface Platform {}

		interface User {
			id: number;
			username: string;
			email: string;
			first_name: string;
			last_name: string;
			role: "user" | "admin";
		}
	}
}

export {};
