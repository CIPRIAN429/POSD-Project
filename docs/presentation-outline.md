# Seven-minute presentation outline

This is a slide plan, not the final PowerPoint. Add actual team names, verified screenshots and the test result from the revision being presented.

| Slide | Duration | Content and speaking point |
|---|---:|---|
| 1. Access Granted | 0:35 | Problem: several organizations share a course platform but require different access to courses, materials and management actions. State the team and project topic. |
| 2. Users, resources and requirements | 0:55 | Three roles; courses, materials, enrollments; multi-tenancy, prerequisites, capacity and waiting lists. Keep one compact role matrix. |
| 3. Three-service architecture | 1:05 | Show the [architecture diagram](diagrams/01-architecture.svg): browser, Django, policy service and PostgreSQL. Explain decision point, enforcement point and the trusted source of attributes. |
| 4. RBAC + ABAC in one request | 1:15 | An instructor can edit courses only in their organization and only when assigned as owner. A student needs enrolled/completed status for materials. Show one allow/deny pair with the [authorization sequence](diagrams/04-authorization.svg). |
| 5. Enrollment consistency | 1:10 | Two requests, one seat. A course-row lock serializes occupancy changes; the unique enrollment constraint prevents duplicates. Use the [last-seat sequence](diagrams/06-last-seat.svg) and [enrollment states](diagrams/05-enrollment-states.svg) to explain queue promotion. |
| 6. Verification and failure handling | 1:10 | Present actual passing test output, organization-boundary checks, protected PDF checks and a policy outage. Explain that unavailable authorization stops protected operations. |
| 7. Results and limitations | 0:50 | One-command startup, English UI and reproducible synthetic data. Single database and synchronous evaluator. Introduce the eight-minute live demonstration. |
| **Total** | **7:00** | Rehearse against this budget. |

All three members should speak and be able to explain the full request path. A suggested split is slides 1-3, slides 4-5 and slides 6-7; adjust it to the team's actual contributions and speaking pace.

Use screenshots from the final application, not design mockups. Do not report a performance gain, coverage percentage, latency or test count unless it was measured for the presented revision. The reading list and essay outlines provide references for the concepts; cite only the sources actually used.
