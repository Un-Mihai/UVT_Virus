/** Realm roles (infra/keycloak/realm-app.json). The API enforces them; the UI only adapts. */
export type Role = "client" | "reviewer" | "admin";

export function hasRole(user: { roles: string[] } | null, role: Role): boolean {
  return user?.roles.includes(role) ?? false;
}
