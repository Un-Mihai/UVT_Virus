# Sign-in (Keycloak)

Every page and every `/api` call needs a signed-in user. [Keycloak](https://www.keycloak.org)
26 is the identity provider: it runs in Docker locally and as a Container App on Azure, and it
can later hand sign-in over to a company directory (below).

## Accounts

| Where | App users | Keycloak admin console |
|---|---|---|
| Local | `client` (role client), `reviewer` (role reviewer) and `admin` (roles reviewer, admin), password `demo` | http://localhost:8080/admin, `keycloak` / `keycloak` |
| Azure | The same three users; password from `terraform -chdir=infra/terraform output -raw demo_password` | `<keycloak_url>/admin/`, user `keycloak`, password from `terraform -chdir=infra/terraform output -raw keycloak_admin_password` |

Users, roles and the web app's client are defined in `infra/keycloak/realm-app.json`.

## How it works

1. A request without a session: `web/src/proxy.ts` redirects to `/auth/login`, which sends the
   browser to Keycloak (authorization code flow with PKCE).
2. Keycloak sends the browser back to `/auth/callback`. The web server exchanges the code for
   tokens with its client secret and keeps them in encrypted httpOnly cookies. Browser
   JavaScript never sees a token.
3. Server code (`@/lib/api/server`) and the `/api/*` proxy send the access token to FastAPI as
   `Authorization: Bearer`. `proxy.ts` refreshes it shortly before it expires (15 minutes).
4. FastAPI checks the token's signature against Keycloak's published keys, its issuer, its
   audience (`api`) and its expiry (`api/app/auth.py`). Only `/health` is public.
5. **Sign out** (`POST /auth/logout`) clears the cookies and ends the Keycloak session.

`/status` shows a Sign-in row: "Verified" means the API accepted your token.

## In code

API routes take the user as a parameter, and roles are enforced there, not only by hiding
buttons:

```python
from typing import Annotated

from fastapi import APIRouter, Depends

from app.auth import Role, User, require_roles

router = APIRouter(prefix="/api/files", tags=["files"])
Admin = Annotated[User, Depends(require_roles(Role.ADMIN))]


@router.post("/{file_id}/approve")
async def approve(file_id: int, admin: Admin) -> None:
    ...  # 403 for anyone without the admin role; admin.id is Keycloak's stable user id
```

`require_roles(Role.CLIENT, Role.REVIEWER)` lets either role through; a whole router can take it in
`dependencies=[...]`. Which projects and findings a role sees is decided in one place each:
`app/projects/access.py` (clients see their own projects, reviewers the submitted ones) and
`app/verification/scope.py` (the scope and confidence threshold of each role).

| Role | May |
|---|---|
| `client` | Create projects, fill in the form, upload documents, submit; run the Client Verification Process and see client-scope findings at or above `CLIENT_CONFIDENCE_THRESHOLD` |
| `reviewer` | Read submitted projects; run the Reviewer Verification Process and see reviewer-scope findings at or above `REVIEWER_CONFIDENCE_THRESHOLD`; confirm or dismiss them; approve a project or send it back with a note |
| `admin` | Manage project types, regulation documents and rule sets of both scopes |

A router whose routes all need a user can say so once:
`APIRouter(prefix="/api/ai", dependencies=[Depends(current_user)])`, as `app/routes/ai.py` does.

The web app reads the user on the server from the session cookie, as `src/app/account-bar.tsx`
does, or asks the API with `api.GET("/api/me")`.

API tests sign their own tokens (`api/tests/conftest.py`): `make_client()` is a signed-in
reviewer, `make_client(token=None)` is signed out, and
`make_client(token=make_token(realm_access={"roles": ["admin"]}))` is an admin.

## Adding roles and users

Edit `infra/keycloak/realm-app.json` (`roles.realm` and `users`), then run `make reset-auth`.
Keycloak imports the realm only when it does not exist yet, so the reset deletes the local
Keycloak database and imports the file again; users and changes made in the admin console are
lost. For a quick experiment, use the admin console instead.

On Azure the realm is imported on the first deploy. After that, change it in the admin console.

## Company accounts

Keycloak can delegate sign-in to Microsoft Entra ID, Google or any OpenID Connect or SAML
directory (admin console → Identity providers), and map the directory's groups to the app's
roles. The app does not change: it keeps trusting Keycloak's tokens. In the pitch: "bank staff
sign in with their usual account, and roles decide who may approve".

## Settings

`compose.yaml` sets these for the local stack, Terraform (`infra/terraform/auth.tf` and
`apps.tf`) for Azure.

| Variable | Read by | Meaning |
|---|---|---|
| `AUTH_ISSUER` | api, web | The realm URL as browsers see it; tokens carry it as `iss` |
| `AUTH_JWKS_URL` | api | Where the API fetches Keycloak's keys when the issuer URL is not reachable from it (Docker) |
| `AUTH_AUDIENCE` | api | Required `aud` claim, default `api` (added by the realm's audience mapper) |
| `AUTH_INTERNAL_URL` | web | Keycloak's address from the web server when the issuer URL is not reachable from it (Docker) |
| `APP_URL` | web | The app's public URL, for the callback and the return after sign-out |
| `AUTH_CLIENT_ID`, `AUTH_CLIENT_SECRET` | web | The `web` client in the realm |
| `AUTH_SECRET` | web | Key that encrypts the session cookies; required in production |
| `KEYCLOAK_PORT` | Compose | Keycloak's port on your machine, default 8080 |

In Docker, `localhost:8080` means the container itself, so the API and the web server call
Keycloak at `keycloak:8080` while still checking the public issuer.

## Troubleshooting

| Symptom | Fix |
|---|---|
| Keycloak shows "Invalid parameter: redirect_uri" | `WEB_PORT` changed after the realm was imported: `make reset-auth`. |
| Sign-in row "Rejected", the API cannot reach Keycloak's signing keys | `docker compose ps keycloak`; check `AUTH_JWKS_URL`. |
| Sign-in row "Rejected", the API rejected the token | `AUTH_ISSUER` differs between the web app, the API and `KC_HOSTNAME`; restart with `make up`. |
| Signed out after `make reset-db` or `make reset-auth` | Expected: sessions live in Keycloak's database. |
| Azure: the first sign-in takes 30 seconds or fails once | Keycloak had scaled to zero. Try again, or set `keep_warm = true` for the demo. |
