# Access Granted — User guide

A practical reference for every menu, account role and course workflow.

## Contents

- [Start here](#start)
- [Sign in and switch accounts](#sign-in)
- [Roles and organization boundaries](#roles)
- [Navigation and menu reference](#menus)
- [Overview](#overview)
- [Course catalog and search](#catalog)
- [Course details and publication states](#course-details)
- [Enroll in a course](#enrollment)
- [Enrollment status reference](#enrollment-states)
- [Waitlist order and automatic promotion](#waitlist)
- [Withdraw or leave the waitlist](#withdrawal)
- [My courses](#my-courses)
- [Read lessons and download PDFs](#reading)
- [Manage courses: create and publish](#create-course)
- [Edit course details and prerequisites](#edit-course)
- [Add, edit and delete materials](#manage-materials)
- [Participants & waitlist and completion](#participants)
- [Archive a course](#archive)
- [Organization users: accounts and roles](#organization-users)
- [Access policies](#policies)
- [Audit log and decision reasons](#audit)
- [System administration](#system-administration)
- [Messages and troubleshooting](#troubleshooting)
- [A short demonstration to try](#demo)

<a id="start"></a>

## Start here

For: All users

Access Granted is a course platform shared by separate organizations. Each account belongs to one organization and has one role. Courses are free. Your role and the state of a course or enrollment determine which actions are available.

The guide contains general instructions only. It is available before sign-in and while access checks are temporarily unavailable. It never grants access to a protected course.

1. Sign in with the username and password supplied by your organization administrator.
2. Open Course catalog to find a course, or Manage courses if you teach or administer courses.
3. Open a course to see its description, prerequisites, available places and your enrollment status.
4. Use the User guide link in the navigation or page header whenever you need an explanation.

- On narrow screens, open Menu to display the full navigation. Close it with the close button, Escape, or by tapping outside it.
- Search this guide by a word or phrase, clear the search to restore all sections, or use the contents links.
- Download guide provides a Markdown copy. Print guide opens your browser's print dialog; you can choose Save as PDF there.

<a id="sign-in"></a>

## Sign in and switch accounts

For: All users

1. Enter your username and password on Sign In, then select Sign in.
2. The organization and permitted menus are selected automatically from your account.
3. Select Sign out when finished, especially on a shared computer.

- There is no public sign-up or self-service password reset. Ask your organization administrator to create an account or change its password.
- An inactive account cannot sign in. Disabling an account also prevents it from continuing on the next protected request.
- Browser tabs normally share one session. To compare students or organizations at the same time, use separate browser profiles or separate browsers. Otherwise, sign out before changing accounts.
- A superadministrator is redirected to System administration instead of the course overview.

<a id="roles"></a>

## Roles and organization boundaries

For: All users

| Role | What the role allows |
| --- | --- |
| Student | Browse published courses in the organization, request enrollment, withdraw, review My courses and read authorized materials. |
| Instructor | Create courses, manage courses assigned to you, manage their materials, view their participants and record completion. |
| Organization Administrator | Manage the organization's courses, accounts and roles; assign instructors; inspect Access policies and Audit log. |
| Technical superadministrator | Use Django System administration to manage organizations and technical account records. This account is separate from normal course use. |

- An administrator in one organization cannot access another organization's courses or users.
- An instructor cannot edit a colleague's course simply because both belong to the same organization.
- You cannot switch organizations by changing a URL or submitting a different organization in a form.
- There is no organization-switching menu: every normal account belongs to exactly one organization.

<a id="menus"></a>

## Navigation and menu reference

For: All users

| Menu or page | Available to | Purpose |
| --- | --- | --- |
| Overview | All organization roles | See course counts and recent enrollment activity. |
| Course catalog | All organization roles | Search visible courses and open course details. |
| My courses | Students | Review your enrolled, waitlisted, completed and cancelled records. |
| Manage courses | Instructors and organization administrators | Create courses and open the courses you may manage. |
| Course details | Authorized users | Read the description, prerequisites, occupancy and enrollment status. Access materials or management actions when permitted. |
| Participants & waitlist | Assigned instructor or organization administrator | Review the course's enrollment records and mark active enrollments as completed. |
| Organization users | Organization administrators | Create and edit accounts, roles, passwords and active status. |
| Access policies | Organization administrators | Read the active role permissions and attribute rules. |
| Audit log | Organization administrators | Search access decisions and changes within your organization. |
| User guide | Everyone | Read, search, print or download these instructions. |
| System administration | Technical superadministrator | Manage organizations and technical users in Django Admin. |


<a id="overview"></a>

## Overview

For: All organization roles

Catalog courses counts the courses visible to your account. Students see published courses. Instructors can also see their own draft and archived courses. Organization administrators can see all courses in their organization.

Active enrollments, Completed and Waitlisted count your own records as a student, records in courses you teach as an instructor, or organization-wide records as an administrator. Completed learners no longer occupy a seat.

Recent enrollments are ordered by their latest update. In the catalog shows a short list of visible courses. Use All courses to open the complete catalog.


<a id="catalog"></a>

## Course catalog and search

For: All organization roles

1. Open Course catalog.
2. Enter part of a title and select Search. Select Clear to remove the filter.
3. Select a course title or View course to open its details.
4. Use Next or Previous at the bottom when results span several pages.

- Search is case-insensitive and matches course titles, not lesson content.
- The card shows a stable course number, publication status, instructor and active places filled.
- A full course can still accept waitlist requests. The displayed occupancy may change before your enrollment request is processed.
- Lists are paginated. Course and enrollment lists show up to 12 records per page; participants show 20, and audit events show 30.

<a id="course-details"></a>

## Course details and publication states

For: Authorized course viewers

A course page combines its description, prerequisites, materials and enrollment information. On a narrow screen, the enrollment panel appears before the description so the current status and actions are easy to find.

| Course state | Meaning |
| --- | --- |
| Draft | Not open for student enrollment. The owner and organization administrator can prepare the course and materials. |
| Published | Visible to students in the organization and open for enrollment or waitlisting, subject to prerequisites. |
| Archived | Closed to new enrollment. Existing enrolled and completed students retain material access; waiting entries are cancelled. The course content is read-only. |

- Only active Enrolled records count toward capacity. Completed, Waitlisted and Cancelled records do not.
- The prerequisites section links to required courses. A linked draft or archived course may itself be unavailable to your account.
- Instructors and administrators see course management actions where their permissions allow them. Students see enrollment actions.

<a id="enrollment"></a>

## Enroll in a course

For: Students

1. Open a published course in your organization's catalog.
2. Check its prerequisites. Each required course must have a Completed enrollment for your account.
3. Select Enroll in course if there is a place, or Join waitlist when the course is full.
4. Read the confirmation and your updated enrollment status.

- The server checks eligibility and capacity when processing the request. A place shown earlier is not a reservation.
- Repeated requests do not create duplicate enrollments.
- Completing a prerequisite requires an instructor or administrator to mark it completed. Reading every lesson does not change your status automatically.
- You cannot request a new enrollment in an archived or draft course.

<a id="enrollment-states"></a>

## Enrollment status reference

For: Students and course managers

| Status | Seat occupied? | Material access | Next action |
| --- | --- | --- | --- |
| Enrolled | Yes | Yes, including after course archival | Study, withdraw, or have completion recorded by the instructor. |
| Waitlisted | No | No | Wait for promotion or choose Leave waitlist. |
| Completed | No | Yes, including after course archival | Keep reading materials. This is a completed record, not a new enrollment. |
| Cancelled | No | No | If the course is published, request enrollment again. A new waitlist position will apply. |


<a id="waitlist"></a>

## Waitlist order and automatic promotion

For: Students and course managers

Students are considered in the order they joined the waitlist. If joining times tie, the enrollment identifier provides a stable order.

When a place becomes available through withdrawal or completion, the first currently eligible student is enrolled automatically. Eligibility includes an active Student account in the same organization and completed prerequisites. Ineligible students are skipped and stay on the waitlist.

- Increasing a published course's capacity also offers free places to eligible waiters.
- When a new student requests enrollment, existing eligible waiters have priority.
- The queue is reconsidered during enrollment and occupancy-changing operations. Reactivating an account alone does not trigger a background promotion job.
- Refresh the course page or My courses to see a changed status. This version has no email or push notifications.
- Leaving and rejoining a waitlist gives you a new joining time; you do not retain your earlier position.

<a id="withdrawal"></a>

## Withdraw or leave the waitlist

For: Students

1. Open the course from My courses or the catalog.
2. Choose Withdraw from course for an active enrollment, or Leave waitlist for a waiting entry.
3. Review the confirmation. Confirm using the named action, or select Cancel to keep the current enrollment.

- A confirmed withdrawal changes your record to Cancelled and removes material access.
- Withdrawing from an active course releases a place and may promote the next eligible waiter.
- The record is kept in My courses as history. There is no withdrawal action for a Completed record.
- Existing active participants can still withdraw after a course has been archived.

<a id="my-courses"></a>

## My courses

For: Students

My courses contains your own enrollment records, including waitlisted, completed and cancelled entries. Records are sorted by their latest update.

Each row shows the course, instructor, last update and enrollment status. Completed records also show the completion date. Open a course to read available materials or use enrollment actions.

A cancelled record for an archived course remains in your history, but its course link may be denied because you are no longer an active or completed participant.


<a id="reading"></a>

## Read lessons and download PDFs

For: Authorized course participants and managers

1. Open the course and find Course materials.
2. Select a text lesson to read it in the application.
3. Select a PDF handout and use Download PDF to save the document.
4. Use Back to course materials to return to the course.

- Students need an Enrolled or Completed record. Waitlisted and Cancelled records do not grant access.
- The assigned instructor and organization administrator can also read the materials.
- A copied lesson or download address still checks the current account. Files have no public download URL.
- Archived courses retain material access for existing enrolled and completed students.
- Saving a PDF creates a local copy. Later changes to account permissions do not remove an already downloaded copy from your device.

<a id="create-course"></a>

## Manage courses: create and publish

For: Instructors and organization administrators

1. Open Manage courses and select Create course.
2. Enter a title, description and a capacity of at least one.
3. As an administrator, select an active instructor from your organization. Instructor accounts are assigned their own newly created courses automatically.
4. Select any prerequisites from the same organization.
5. Choose Draft to prepare the course, or Published to open enrollment. Select Create course to save.

- Instructors see their assigned courses in Manage courses; administrators see all organization courses.
- A course is not required to contain materials before publication. Add the intended materials before sharing it with students.
- A course cannot require itself or create a circular dependency. Cross-organization prerequisites are not allowed.

<a id="edit-course"></a>

## Edit course details and prerequisites

For: Assigned instructor or organization administrator

1. Open the course, then select Edit course.
2. Update the fields and select Save changes. Cancel returns without saving.

- Capacity cannot be reduced below the current number of active enrollments. Increasing it can promote eligible waiters.
- A course with non-cancelled enrollment records cannot be returned to Draft. Use Archive course when it should close.
- An organization administrator can assign a different active instructor from the same organization.
- Use Ctrl on Windows/Linux or Command on macOS to select multiple prerequisites in the list. Touch devices use their native selection control.
- Changed prerequisites affect new enrollment requests and waitlist eligibility. Existing enrolled and completed records are retained.
- Archived courses are read-only and cannot be republished from the application.

<a id="manage-materials"></a>

## Add, edit and delete materials

For: Assigned instructor or organization administrator

1. Open a course and choose Add material.
2. Enter a title, choose Text lesson or PDF handout, and set its position in the course.
3. For a text lesson, enter its body. For a PDF, choose a PDF file no larger than 10 MB.
4. Select Add material. Existing materials have an Edit link for changing the title, content, file or position.
5. To remove a material, open Edit, choose Delete material and confirm. Cancel closes the confirmation without deleting it.

- Materials are ordered by position, then identifier. Position changes affect their display order.
- A text lesson must have content. A PDF handout must have a PDF file; upload checks include the file extension and PDF signature.
- The optional body of a PDF handout can provide instructions or a summary above its download link.
- Deleting a material is permanent in this interface. Keep an original copy if you may need it later.
- Archived course materials can be read by permitted users, but cannot be added, edited or deleted.

<a id="participants"></a>

## Participants & waitlist and completion

For: Assigned instructor or organization administrator

1. Open the course and select Participants & waitlist.
2. Review the active, waiting, completed and cancelled counts and individual records.
3. For an Enrolled student, select Mark completed and confirm.

- Completion records the current time, releases the student's place and offers it to the first eligible waiter.
- The completed student keeps material access. The Completed record can satisfy prerequisites for other courses.
- Only active enrollments can be marked completed. Waiting and cancelled students have no completion action.
- There is no automatic completion based on reading, quiz, certificate, grading or undo-completion feature in this version.
- Inactive accounts are labelled in the participant list.

<a id="archive"></a>

## Archive a course

For: Assigned instructor or organization administrator

1. Open the course and choose Archive course.
2. Read the effects listed in the confirmation and confirm, or select Cancel.

- The course becomes Archived and stops accepting new enrollment requests.
- Waitlisted records become Cancelled. Active and completed records are retained.
- Enrolled and completed students retain material access. The owner and administrator can inspect the course and participants.
- Course details and materials become read-only. Managers can still record completion for existing active participants.
- Archival is used to preserve history. There is no course deletion or restore-from-archive action in the course interface.

<a id="organization-users"></a>

## Organization users: accounts and roles

For: Organization administrators

1. Open Organization users. Search by username or first/last name if needed.
2. Select Create user or the Edit action beside an existing account.
3. Set the username, optional name/email fields, role and Active status.
4. For a new account, set an initial password. When editing, leave Password blank to keep the existing password.
5. Select Save changes or Create user. Give new account credentials to the intended user through your usual channel.

- The organization is assigned automatically. This form cannot create technical superadministrators or change organization membership.
- Usernames must be unique across the platform. Passwords must pass the application's password checks.
- Changes of role apply on the next protected request. Deactivating an account stops further access on the next request.
- You cannot deactivate your own administrator account or remove your own administrator role.
- Before changing an instructor to another role, reassign all courses owned by that instructor, including archived courses. Archived courses cannot be reassigned through the course interface; a technical administrator would need to handle such a correction.
- Deactivating a student does not automatically cancel existing active enrollment records. Waitlist promotion skips inactive accounts.
- This version has no user deletion button in the organization interface. Deactivate an account when access should stop.

<a id="policies"></a>

## Access policies

For: Organization administrators

Access policies displays the evaluator's policy version, permitted actions for each role and the named attribute rules.

RBAC defines the actions a role may request. ABAC checks the active account, organization, course owner, course state and enrollment state. The page is explanatory; it is not a policy editor.

User roles can be changed in Organization users. Changing the ABAC rule definitions requires a code change and application/service rebuild. No decision cache is used.

A permitted role does not bypass course prerequisites, capacity or organization boundaries. Protected operations require a successful authorization result each time.


<a id="audit"></a>

## Audit log and decision reasons

For: Organization administrators

Audit log shows events for your organization, newest first. Each entry contains a time, actor/action, resource identifier, result and reason. Access decisions also include the policy version.

Search matches usernames, action names and reason codes. The All decisions / Allowed / Denied filter can be combined with search. Clear restores the unfiltered view.

ACCESS events describe authorization decisions. CHANGE events describe completed changes. WORKFLOW events can record a business-rule refusal after authorization, such as a missing prerequisite. An Allowed access decision is therefore not proof that an enrollment succeeded.

Material-read authorization is logged against the parent course. A waitlist_promoted event records the enrollment identifier; its actor is the account whose operation triggered promotion, which can differ from the promoted student.

| Example reason or action | How to read it |
| --- | --- |
| ACCESS_GRANTED | The role and attribute checks allowed this request. |
| ENROLLMENT_REQUIRED | The account did not have the enrollment needed to read this material. |
| TENANT_MISMATCH | The requested resource belongs to a different organization. |
| ELIGIBILITY_NOT_MET | The enrollment workflow rejected the request, for example because a prerequisite is incomplete. |
| POLICY_UNAVAILABLE | The evaluator could not provide a valid decision; the protected operation was stopped. |
| waitlist_promoted | An existing waiting enrollment was moved into an available place. |

- No passwords or complete document bodies are written to audit entries.
- The interface is read-only. Logs are stored in the application database, not an external tamper-proof system.
- Displayed timestamps use Europe/Bucharest.

<a id="system-administration"></a>

## System administration

For: Technical superadministrator

The separate superadministrator account uses /admin/ and Django Admin. It manages organizations and technical user records. Normal organization administrators use Organization users instead.

Use the course application for course content and enrollment workflows. Courses are not edited through Django Admin.

Technical account edits require care: changing an organization or deleting a user can affect related records. Prefer creating the correct organization account and deactivating an old account when appropriate.


<a id="troubleshooting"></a>

## Messages and troubleshooting

For: All users

| What you see | Meaning and next step |
| --- | --- |
| Sign-in failed | Check the username/password. Ask the organization administrator whether the account is active; there is no public reset form. |
| Complete the required courses before enrolling. | At least one prerequisite has no Completed record. Ask the relevant instructor to record completion if you have finished the course. |
| Permission required / 403 | Your current role, ownership or enrollment does not permit this action. A direct link does not override these checks. |
| Page not found / 404 | The address may be incorrect, the resource may have been removed, or it may belong to a different organization. |
| Access checks are temporarily unavailable / 503 | The policy evaluator could not be reached or returned an invalid decision. No protected mutation is performed. Retry after the service recovers; the local project maintainer can inspect the Docker services. |
| Archived course is read-only | The course cannot be edited or reopened from the course interface. |
| Capacity cannot be lower than the active enrollment count. | Keep enough capacity for existing active enrollments. |
| A file upload is rejected | Check that it is a PDF, no larger than 10 MB, with a .pdf filename. A renamed non-PDF file is still invalid. |
| Form validation errors | Correct the fields marked in the form, then save again. Unsaved edits have not been applied. |
| A page looks out of date after editing the source code | The local maintainer must rebuild through scripts/start.sh, then reload the browser. The app does not automatically load host-file edits. |


<a id="demo"></a>

## A short demonstration to try

For: Project team

Use synthetic demo accounts. Atlas and Nova each start with an administrator, one instructor and three students. Student 1 has completed the introductory course; Student 2 is enrolled in it; Student 3 starts without an enrollment. Later demonstrations may have changed these records.

1. As atlas.student3, try to enroll in Distributed Systems Lab without the required Python Foundations completion.
2. If Concurrency Workshop has a free place, enroll atlas.student1, then request enrollment as atlas.student3 to demonstrate the waitlist.
3. Try to read a workshop material as the waiting student; access is refused.
4. Withdraw the enrolled student and refresh the waiting student's course page. The first eligible waiter is promoted and can read materials.
5. As atlas.admin, open Participants & waitlist and Audit log to inspect the recorded changes.

- This walkthrough changes demo records. The separate reset script erases application data and should be used only when the team deliberately wants a fresh demo; see README.md.
- All courses are free. Payments, email notifications, quizzes, grades and certificates are outside this version.
- Technical startup, testing, recovery and dataset regeneration instructions are in README.md and the docs directory.
