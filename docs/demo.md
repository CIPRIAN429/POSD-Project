# Eight-minute demonstration

Use a fresh demo for a predictable walkthrough. Only run `bash scripts/reset-demo.sh` and type `RESET` when you intend to erase existing application data. Start with `bash scripts/start.sh` and keep a WSL terminal in the project directory.

Use separate browser profiles/private windows to retain different accounts. Prepare Atlas administrator, Atlas instructor, Atlas Student 1, Atlas Student 3 and Nova administrator sessions. The default password is `LearnTogether2026!` unless changed at initialization.

## Preparation outside the eight minutes

1. Run `bash scripts/test.sh` and keep the real result available for the concurrency discussion.
2. As `atlas.admin`, create `atlas.instructor2` with the Instructor role in Atlas University. This additional account demonstrates ownership within the same tenant; the default fixture intentionally contains only one instructor per organization.
3. Copy the Python Foundations course detail URL and a protected PDF link while signed in as `atlas.student1`, who has completed that course.
4. Confirm that Concurrency Workshop is empty. It has one seat and no prerequisites.
5. Keep the policy-stop and policy-start commands ready in the terminal. Complete startup before the presentation; avoid image downloads during the demo.

## Timed walkthrough

| Time | Action | Expected observation and explanation |
|---|---|---|
| 0:00-0:55 | Show the Atlas catalog, then open the copied Atlas course URL as `nova.admin` | Nova sees its own courses; the direct Atlas URL does not disclose the resource. A privileged role remains bounded by tenant attributes. |
| 0:55-1:45 | As `atlas.instructor`, open course editing. Try the same edit URL as `atlas.instructor2` | The assigned instructor may edit; another instructor in the same organization is denied. This isolates ownership from role and tenant. |
| 1:45-2:35 | As `atlas.student3`, attempt to enroll in Distributed Systems Lab | Enrollment is rejected because Python Foundations has not been completed. Show Student 1's completed foundation as the contrasting eligible state. |
| 2:35-3:50 | Enroll `atlas.student1` in Concurrency Workshop. Enroll `atlas.student3` in the same course | Student 1 is enrolled and Student 3 is waitlisted. The instructor's Participants & Waitlist page shows the states. |
| 3:50-4:55 | Copy a workshop material link as Student 1; try it as Student 3. Withdraw Student 1, then refresh Student 3 | The waitlisted student is denied, then is promoted and gains access. No database editing is needed. |
| 4:55-5:55 | Show a PDF download and the Atlas administrator's Audit Log | Private files follow the same authorization path. Connect one allow/deny event to its reason and resource. |
| 5:55-7:10 | Run `docker compose stop policy`; refresh a protected page or submit an enrollment. Run `docker compose up -d policy` and retry after health recovers | The protected operation fails closed during the outage. Restoration allows normal requests again. |
| 7:10-8:00 | Show the policy catalog and the saved test result | Explain explicit role actions, attribute checks and the automated two-request last-seat test. Mention the single database and synchronous policy-service limitations. |

Commands for the failure demonstration:

```bash
docker compose stop policy
docker compose up -d policy
docker compose ps
```

Use an eligible student and a published course with no existing enrollment if demonstrating a failed write. After recovery, verify that the outage attempt did not create an enrollment before making a new request.

## Optional follow-up checks

- Mark a currently enrolled introductory student as completed, then show that the dependent course becomes available.
- Archive a course with enrolled and waiting students. Existing participants retain materials; the queue is cancelled and new enrollment stops.
- Disable a user as organization administrator and verify the next protected request cannot continue.
- Run the actual concurrency test rather than simulating simultaneity with manual clicks.

For each result, distinguish an observation from an implementation claim. The demo shows selected scenarios; the tests provide repeatable evidence for additional cases.
