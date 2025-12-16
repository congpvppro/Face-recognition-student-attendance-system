import ky from "ky";
import { env } from "$env/dynamic/public";
import { dev } from "$app/environment";

const DEFAULT_PROD_API = "https://api.attendde.com"; // Replace with actual prod URL if known

const ensureTrailingSlash = (u: string) => (u.endsWith("/") ? u : `${u}/`);

// 3. Logic to determine URL
// Note: You must rename your Vercel Env Var to start with "PUBLIC_"
const defaultPrefix = ensureTrailingSlash(
  (env.PUBLIC_API_URL as string | undefined) ??
    (dev ? "http://localhost:3000" : DEFAULT_PROD_API),
);

export const api = ky.create({
  prefixUrl: defaultPrefix, // 4. Fixed: You were ignoring defaultPrefix in your snippet
  credentials: "include",
  timeout: 10000,
  retry: 0,
});
