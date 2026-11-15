# Individual essay preparation

These are research outlines and reading lists, not completed individual essays. Each student must read the course's separate essay instructions and the papers they cite, then write their own analysis of the implementation and evidence they have reviewed.

Requirements supplied in the assignment: **1.5-2 pages per student, including 3-5 research references**, scientific report structure and academic citations. Use IEEE numbering consistently. Figures, equations, tables and algorithms together occupy at most 10% of the essay; number each item and refer to it in the text. A text-only essay is acceptable under these requirements.

Chosen formatting: A4, 2 cm margins, Times New Roman 12 pt, 1.15 line spacing, 14 pt bold title and 12 pt bold section headings. The three essays will later be combined into one PDF, giving 4.5-6 pages before any separately required cover material. Final PowerPoint and essays are not part of this initial code delivery.

The sources below were checked against publisher, author or institutional primary pages on **15 October 2026**. Paper titles, authors and publication details should still be checked against the downloaded paper when producing the final reference list. Source suggestions are not a claim that any student has already read them.

## Essay 1: Combining RBAC and ABAC in a multi-tenant course platform

**Research question:** How can a small role model remain manageable while enforcing organization, ownership and enrollment restrictions?

Suggested structure:

1. **Problem and background:** contrast role permission assignment with contextual attribute evaluation. Introduce the two organizations and three roles.
2. **Design:** explain the policy decision/enforcement boundary, server-derived attributes and default denial. Use the same-role/different-owner case.
3. **Evaluation:** describe a small paired set of allow/deny requests, varying one attribute at a time. Report actual results from policy and integration tests.
4. **Discussion:** explain why code-defined policies suit this limited scope; discuss the synchronous service dependency and absence of decision caching.
5. **Conclusion:** state what the demonstrated design supports and what the tests establish.

Use three or four of these sources:

- **[A1]** D. F. Ferraiolo and D. R. Kuhn, "Role-Based Access Controls," *15th National Computer Security Conference*, pp. 554-563, 1992. [NIST publication](https://www.nist.gov/publications/role-based-access-controls) / [paper](https://csrc.nist.gov/CSRC/media/Projects/Role-Based-Access-Control/documents/ferraiolo-kuhn-92.pdf). Use for the role-based authorization foundation.
- **[A2]** R. S. Sandhu, E. J. Coyne, H. L. Feinstein and C. E. Youman, "Role-Based Access Control Models," *Computer*, vol. 29, no. 2, pp. 38-47, 1996. [Author paper hosted by NIST](https://csrc.nist.gov/csrc/media/projects/role-based-access-control/documents/sandhu96.pdf). Use for the relation between users, roles and permissions; do not claim that this project implements every model or role hierarchy in the paper.
- **[A3]** V. C. Hu et al., *Guide to Attribute Based Access Control (ABAC) Definition and Considerations*, NIST SP 800-162, 2014, updated 2019. [Official publication and DOI](https://csrc.nist.gov/pubs/sp/800/162/upd2/final). A primary technical report for attribute categories and policy components. If the course requires conference/journal papers exclusively, use A4 as the third research paper and keep A3 only as supplementary reading.
- **[A4]** V. C. Hu, E. Martin, J. Hwang and T. Xie, "Conformance Checking of Access Control Policies Specified in XACML," *First IEEE International Workshop on Security in Software Engineering*, pp. 275-280, 2007. [NIST-hosted paper](https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=51160). Use for the distinction between intended policy and implemented decisions. The project uses Python rules, not XACML.

## Essay 2: Consistent enrollment and waitlist transitions

**Research question:** How does a common transaction and locking protocol prevent oversubscription when separate requests compete for the last seat?

Suggested structure:

1. **Problem:** show the read-count/write race and the invariant that active enrollment does not exceed capacity.
2. **Method:** explain the shared course-row lock, atomic transitions and uniqueness constraint. Clarify why a uniqueness constraint alone cannot enforce total capacity.
3. **Evaluation:** describe the PostgreSQL concurrent-request test and assertions: one enrolled, one waitlisted, no duplicate student/course records. Add withdrawal/promotion evidence.
4. **Discussion:** distinguish transaction isolation in a single PostgreSQL service from consistency across replicated databases. Discuss throughput for a heavily contested course and the cost of waiting for a lock.
5. **Conclusion:** connect the observed result to the locking convention and its assumptions.

Use these three sources:

- **[B1]** J. Gray, "The Transaction Concept: Virtues and Limitations," *Proceedings of the 7th International Conference on Very Large Data Bases*, pp. 144-154, 1981. [Author's publication record](https://jimgray.azurewebsites.net/jimgraypublications.htm) / [paper](https://jimgray.azurewebsites.net/papers/theTransactionConcept.pdf). Use for atomic state transformations and transaction boundaries.
- **[B2]** H. Berenson, P. Bernstein, J. Gray, J. Melton, E. O'Neil and P. O'Neil, "A Critique of ANSI SQL Isolation Levels," *Proceedings of ACM SIGMOD*, pp. 1-10, 1995. [Microsoft Research paper](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/tr-95-51.pdf). Use to explain why the word "transaction" alone is insufficient to establish the needed concurrency behavior.
- **[B3]** P. Bailis, A. Davidson, A. Fekete, A. Ghodsi, J. M. Hellerstein and I. Stoica, "Highly Available Transactions: Virtues and Limitations," *Proceedings of the VLDB Endowment*, vol. 7, no. 3, pp. 181-192, 2013. [Publisher paper](https://www.vldb.org/pvldb/vol7/p181-bailis.pdf). Use for the distinction between isolation and availability in distributed settings. The article was presented at VLDB 2014; the journal publication is 2013. Do not claim that Access Granted implements the paper's distributed transaction system.

PostgreSQL and Django documentation can explain the APIs used, but should supplement rather than replace the three research sources. Report timings only if you measure them under documented conditions.

## Essay 3: Organization isolation and authorization testing

**Research question:** How can an application check that organization boundaries hold across normal navigation, direct URLs, forms and private files?

Suggested structure:

1. **Threat model:** an authenticated organization user changes a resource identifier or submits a crafted request. State the protected resources and trusted server components.
2. **Controls:** organization-scoped queries and form choices, centralized authorization and protected file delivery. Explain why hiding a button is insufficient.
3. **Evaluation:** organize tests by entry point and compare allowed and denied identities. Include policy-service unavailability and an already-copied PDF URL after withdrawal.
4. **Discussion:** explain the limits of selected tests and distinguish functional evidence from exhaustive verification. Describe the audit log's explanatory role without claiming tamper resistance.
5. **Conclusion:** link each tested boundary to a control and a repeatable observation.

Use these three sources (A2 and A4 are intentionally shared background, while this essay's analysis is distinct):

- **[C1]** J. H. Saltzer and M. D. Schroeder, "The Protection of Information in Computer Systems," *Proceedings of the IEEE*, vol. 63, no. 9, pp. 1278-1308, 1975. [Author-hosted text](https://web.mit.edu/Saltzer/www/publications/protection/) / [publication record](https://web.mit.edu/saltzer/www/publications/). Use for complete mediation, least privilege and fail-safe defaults.
- **[C2]** R. S. Sandhu, E. J. Coyne, H. L. Feinstein and C. E. Youman, "Role-Based Access Control Models," *Computer*, vol. 29, no. 2, pp. 38-47, 1996. [NIST-hosted paper](https://csrc.nist.gov/csrc/media/projects/role-based-access-control/documents/sandhu96.pdf). Use for the role matrix that the tests exercise.
- **[C3]** V. C. Hu, E. Martin, J. Hwang and T. Xie, "Conformance Checking of Access Control Policies Specified in XACML," *First IEEE International Workshop on Security in Software Engineering*, pp. 275-280, 2007. [NIST-hosted paper](https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=51160). Use for testing conformance between intended rules and decisions. Discuss transfer of the testing idea without implying that this implementation uses their tool.

## Evidence to gather before writing

Save the commit or revision identifier, test command and actual result. Select only the screenshots or compact tables that fit the 10% allowance. State the fixture accounts and initial states so another person can repeat the experiment. Separate claims from the cited literature, implementation choices made by the team, and observations from the tests. Replace the outline identifiers A1/B1/C1 with each essay's own consecutive IEEE citation numbers.
