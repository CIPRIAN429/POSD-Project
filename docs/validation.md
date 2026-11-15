# Initial-version validation

## Interface and documentation revision — 16 October 2026

The revised version includes an English user guide covering all menus, roles, forms, enrollment states, waitlists, materials, administration and troubleshooting. Its 24 sections are shared by the in-app page and the downloadable Markdown manual. `scripts/export-guide.py --check` verifies that the manual matches the source content.

Automated checks passed: **207 policy tests and 48 Django tests (255 total)**, documentation consistency, Django system checks and migration consistency. The four added checks cover public help and download access without the policy service, plus guide rendering for each organization role.

Browser checks used the Codex in-app browser at 1440 px, 390 px and 303 px. The catalog, overview, sign-in page, course details, text lesson, course form, My courses, participants, organization users, access policies, audit log and user guide were inspected across administrator, instructor and student accounts. No horizontal page overflow was found on the inspected narrow layouts, and no JavaScript errors were observed. The guide was also opened without signing in.

Guide search, its no-results state, clearing the search and downloading the Markdown file were exercised. The mobile menu was checked for navigation, Escape dismissal and returning keyboard focus to Menu. The Archive confirmation dialog was opened and cancelled; the course remained Published. Existing demo enrollments and account records were preserved. This revision did not repeat the original destructive workflow tests in the live demo.

The interface now uses compact course cards, readable type, a responsive navigation drawer, stacked table records on narrow screens, styled scrollbars and in-page confirmation dialogs. Print guide is available through the browser's native print dialog; no exported PDF is part of this revision.

- [Desktop catalog](screenshots/catalog-desktop-v2.jpg)
- [Mobile audit log](screenshots/audit-mobile-v2.jpg)
- [User guide in the application](screenshots/user-guide-v2.jpg)
- [Complete user manual](user-guide.md)

## Original implementation checks

Verified on 15 October 2026 using Ubuntu 24.04 in WSL, native Ubuntu Docker, PostgreSQL 17 and headless Chromium.

## Automated checks

`bash scripts/test.sh` completed successfully:

| Check | Result |
|---|---|
| Policy evaluator tests | 207 passed |
| Django integration and domain tests | 44 passed |
| Django system checks | No issues |
| Migration consistency | No changes detected |

The Django tests use a separate PostgreSQL test database. Coverage includes tenant boundaries, role and ownership checks, protected PDF routes, enrollment-state access, prerequisite graphs, FIFO promotion, simultaneous requests for the final seat, role changes, outages and repeatable seeding. Policy tests cover the action/role matrix, attributes, invalid requests and internal API authentication.

The policy suite emits one third-party deprecation warning about Starlette's AnyIO `BlockingPortal` import. It does not affect the passing results.

## Browser checks

The main application was checked with Atlas Student, Atlas Instructor, Atlas Administrator, Nova Administrator and technical superadministrator accounts. Their permitted pages rendered in English without JavaScript errors. Catalogs were scoped to the organization. Protected PDF downloads returned PDF content. Desktop and 390-pixel mobile layouts were visually inspected; no horizontal page overflow was observed on the checked mobile catalogs.

The following end-to-end actions were also exercised through the interface in an isolated, disposable Compose project:

- Missing prerequisite rejected an enrollment.
- One student occupied the final seat; another joined the waitlist and could not read protected materials.
- Withdrawal promoted the waiting student and unlocked the material.
- Completion released capacity while preserving the completed student's access.
- Archiving cancelled the remaining waitlist and preserved existing participants' material access.
- An instructor created a course and added, edited and deleted a text lesson.
- An organization administrator created a user, changed their role and deactivated the account. Subsequent requests enforced both changes.
- Another instructor was refused access to editing a course they did not own; a different organization's administrator received a 404 for its detail URL.
- Stopping the real policy container caused an enrollment request to return HTTP 503. After recovery, the student still had no enrollment from the failed attempt.
- Running startup again preserved the archived course and the edited, inactive user. Fresh initialization generated the expected demo dataset.

The disposable test services and volumes were removed after verification. The main demo retains its initial courses, users and enrollments; ordinary browser access checks add audit events.

## Evidence and reproduction

- [Desktop overview](screenshots/overview.png)
- [Mobile catalog](screenshots/mobile-catalog.png)
- Run `bash scripts/test.sh` for the repeatable automated suite.
- Follow [the demo script](demo.md) for the interface and service-failure walkthrough.

These checks establish the initial local teaching version. They are not a production security certification or an exhaustive proof of every concurrent execution.
