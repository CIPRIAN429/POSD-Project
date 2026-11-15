# Permissions and policies

Every allowed action requires an active account and the same organization as the resource. An organization administrator has no access to another organization's data. Unknown actions are denied.

| Action | Student | Instructor | Organization Administrator |
|---|---|---|---|
| Dashboard and published catalog | Own organization | Own organization | Own organization |
| Read a published course description | Own organization | Own organization | Own organization |
| Read drafts | No | Own courses | All organization courses |
| Read archived course details | Participation history | Own courses | All organization courses |
| Create courses | No | Assigned to self | Assign organization instructor |
| Edit, archive and manage materials | No | Own courses | All organization courses |
| View participants / mark completed | No | Own courses | All organization courses |
| Enroll / withdraw | Own enrollment | No | No |
| Read text or download PDF | Enrolled/completed; published/archived | Own courses | All organization courses |
| Manage accounts and roles | No | No | Own organization |
| Read policies and audit log | No | No | Own organization |

The platform superadministrator is a separate technical account for Django Admin. It is not an additional course-application role.

For a visual walkthrough, see [roles and pages](visual-guide.md#2-roles-and-pages), [authorization and audit](visual-guide.md#4-authorization-and-audit) and the [course lifecycle](visual-guide.md#7-course-lifecycle).

## Named policy gates

| Policy ID | Question answered |
|---|---|
| `active_account` | Is the authenticated account enabled? |
| `tenant_isolation` | Do known subject and resource organizations match? |
| `role_permissions` | Does the role explicitly permit this action? |
| `course_ownership` | Is this instructor assigned to this course? |
| `course_visibility` | Can the role see a course in this state? |
| `material_membership` | Does the student have enrolled or completed access? |
| `published_enrollment` | Is the course open for enrollment? |
| `enrollment_transition` | Does the current enrollment support withdrawal or completion? |

`matched_rules` records the gates considered, including a rejecting gate. A reason such as `TENANT_MISMATCH`, `COURSE_OWNER_REQUIRED` or `ENROLLMENT_REQUIRED` explains a refusal in the audit log. Internal identifiers remain stable while the interface presents English labels.

## Business rules after authorization

Enrollment also requires completed prerequisites. If capacity is exhausted, the application creates a waitlist entry rather than treating it as a permission denial. Completion, withdrawal and promotion happen inside the same course-locking convention. Waitlisted and cancelled students cannot open materials.

Policy decisions are made on the server for direct URLs as well as normal navigation. Hiding a button is a usability feature, not an access-control mechanism. List filtering, form choices and protected download routes are additional enforcement surfaces.

## Suggested verification pairs

- Same role, different organization: Atlas administrator cannot open a Nova course.
- Same organization and role, different owner: an instructor can edit their assigned course but not another instructor's course.
- Same student and course, different enrollment: waiting denies a PDF; promotion allows it.
- Same resource, different state: a published course accepts new enrollment; an archived course does not.
- Same account, different active flag: a disabled account cannot continue protected activity.
- Same request, policy service unavailable: return an unavailable response without a successful mutation.

These cases are project acceptance scenarios, not a claim of exhaustive formal verification.
