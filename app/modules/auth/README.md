# Auth (SCRUM-90 / SCRUM-91)

Untuk FE, QA, dan BE yang mau login. Variabel: repo root `.env.example`.

Zitadel hanya membuktikan identitas. Login looks up `users.zitadel_sub`, then `users.email` if `sub` is still empty, and stores `sub` on that first success. We don't make user baru. Cookie: `veritask_session` (UUID sesi), HttpOnly, SameSite=Lax, Path=/. Pakai host `localhost`, bukan `127.0.0.1`.

`expires_at` is set once at login to `ABSOLUTE_SESSION_LIFETIME_MINUTES` (default 720, 12 hours). That number is a proposal and still needs client confirmation. Idle (`IDLE_TIMEOUT_MINUTES`, default 30) is a separate clock and is enforced in SCRUM-91.

Server nyala (`AUTH_OIDC_MODE=zitadel`, port 8000):

- Login: http://localhost:8000/auth/login
- After Zitadel: http://localhost:8000/auth/done (needs `AUTH_DONE_URL_OVERRIDE` in `.env`; otherwise `{FE}/auth/done`)
- Profile: http://localhost:8000/me
- Docs: http://localhost:8000/docs

Jangan `127.0.0.1` (cookie tidak ikut). Jangan refresh URL `/auth/callback?code=...` yang lama.

Logout is **POST** with the session cookie, not a URL you open in the address bar (GET will 405 / do nothing useful). Browser sends `veritask_session` automatically on same-origin POST (`credentials: 'include'`). Example: `POST http://localhost:8000/auth/logout`.

Idle timeout (default 30 menit, `IDLE_TIMEOUT_MINUTES`): setiap request yang lolos `get_current_user` / `require_role` memperbarui `sessions.last_activity_at` dan me-refresh `max-age` cookie. Idle terlampaui → baris sesi dihapus, cookie dibersihkan, `401 SESSION_EXPIRED`. Request berikutnya tanpa cookie → `401 UNAUTHENTICATED`. Idle **tidak** memanggil Zitadel `end_session`.

`require_role(*roles)` (alias `require_roles`): tanpa sesi `401 UNAUTHENTICATED`; peran salah `403 FORBIDDEN`. SCRUM-91 hanya mengirimkan dependency ini. Modul lain memasangnya di router mereka. Jangan `dependency_overrides[get_current_user]` di test — pakai `complete_login` di `tests/login.py` + seed `zitadel_sub` (`AUTHOR_SUB`, `REVIEWER_SUB`, `ADMIN_SUB`, `VIEWER_SUB`).

**PBI-1 AC2 (sebagian).** SCRUM-91 memenuhi AC2 untuk penjaga sesi/peran (`UNAUTHENTICATED` / `FORBIDDEN` / idle). AC2 tingkat story — setiap halaman dan aksi hanya untuk peran yang berwenang — **belum tuntas** sampai PBI-2 (`/suites`), SCRUM-92 (`/admin/users`), PBI-3 (`/cases`), dan PBI-10 (`/providers`) memasang `require_role` sesuai matriks PBI-1-SA-1. `/suites*` saat ini masih bisa dipanggil tanpa sesi. Itu disengaja: bukan cakupan subtask ini.

Matriks Sprint 1 (spec untuk ticket konsumen, belum dipasang di router selain auth):

| Route | Allow | Ticket |
|---|---|---|
| `GET /suites`, `GET /suites/{id}` | author, reviewer, admin | PBI-2 |
| `POST /suites`, `PATCH /suites/{id}`, `DELETE /suites/{id}`, `POST /suites/{id}/archive` | author, admin | PBI-2 |
| `/admin/users*` | admin | SCRUM-92 |
| `/cases*` write | author, admin | PBI-3 |
| `/providers*` | admin | PBI-10 |

Health, `/auth/login`, `/auth/callback` tidak butuh sesi. `/me` butuh sesi, semua peran.

| Method | Path | Sukses | Error |
|---|---|---|---|
| GET | `/auth/login` | 302 ke IdP (PKCE, state, nonce) | — |
| GET | `/auth/callback?code&state` | 302 ke `{FE}/auth/done` + cookie (lokal: `/auth/done` di API) | 403 `USER_NOT_REGISTERED`, 403 `USER_DEACTIVATED`, 400 `INVALID_OIDC_STATE` / `OIDC_EXCHANGE_FAILED` |
| POST | `/auth/logout` | 302 ke IdP `end_session` (cookie required) | GET in the address bar will not log you out |
| GET | `/me` | 200 `{id, name, email, role}` | 401 `UNAUTHENTICATED`, 401 `SESSION_EXPIRED` |

Error body: `{ "code": "USER_NOT_REGISTERED", "message": "..." }`. Kode 401/403 yang dipakai FE: `UNAUTHENTICATED`, `SESSION_EXPIRED`, `FORBIDDEN` (huruf besar; bukan `forbidden` / `unauthorized`). pytest memakai `AUTH_OIDC_MODE=fake`. `APP_ENV=staging` or `production` refuses fake (boot fails; no `/_fake/oidc`). Staging/prod must use `zitadel`.

Refer to https://kelompok4pplxpropensi.atlassian.net/browse/SCRUM-91 for RBAC/idle updates.
