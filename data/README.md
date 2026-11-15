# Synthetic demonstration dataset

`demo.json` contains original fictional data created for this project. It contains no collected personal information and uses reserved `example.test` email addresses. Organization and person names are fictional. Course texts and exercises are original teaching material.

## Contents

- Atlas University and Nova Academy.
- Five organization users each: one administrator, one instructor and three students.
- Six published courses: three per organization.
- Two text lessons and one generated PDF handout per course.
- Four initial enrollments: Student 1 completed the introductory course and Student 2 is actively enrolled, in each organization.
- One separate technical superadministrator is created by the seed command.

| Organization | Introductory course | Course requiring the introduction | One-seat workshop |
|---|---|---|---|
| Atlas University | Python Foundations | Distributed Systems Lab | Concurrency Workshop |
| Nova Academy | Security Essentials | Policy Design Studio | Tenant Isolation Workshop |

The one-seat workshops start without enrollments. Enroll Student 1 and then Student 2 to produce an occupied seat and a waitlist entry. This makes the full transition visible during the demonstration.

## Generation

`python manage.py seed_demo` reads the fixture and uses ReportLab to generate the six PDF handouts from each course's objective, lessons and exercise. The startup script invokes this command automatically. Handouts are stored in private media, not in a public static directory.

The command creates `DemoState(key="initial-v1")` after a successful transaction. Subsequent runs do not change existing data or passwords. On PostgreSQL an advisory transaction lock prevents concurrent seed attempts. If file generation fails, the command removes files created by that failed attempt.

Edit the fixture before creating a fresh demonstration. To intentionally regenerate an existing demonstration, use `bash scripts/reset-demo.sh` and confirm with `RESET`; this removes all application data, including user modifications.

## Dataset link for the course submission

After publishing the team's repository, use the actual public URL of its `data/` directory and check that it opens without authentication. Include `demo.json`, this provenance note and the seeding source in the repository. There is no external dataset to download, no claimed observational study and no fabricated measurement data.
