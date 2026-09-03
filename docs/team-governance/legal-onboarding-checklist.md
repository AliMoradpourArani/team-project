# ForgeFlow Legal Onboarding Checklist

Use this checklist before or during a person's first private ForgeFlow Core contribution. It is an operational record template and does not replace legal advice.

Current intended governing-law baseline: **laws of the Islamic Republic of Iran**. See `iran-legal-basis.md`.

## A. Engagement record

- [ ] Full legal name recorded privately where appropriate
- [ ] Contact email recorded privately where appropriate
- [ ] Role/scope documented
- [ ] Start date recorded
- [ ] Employment/contractor status reviewed under Iranian law
- [ ] If the relationship is employment, required Iranian Labour Law employment documentation is completed
- [ ] Governing law is stated as the laws of the Islamic Republic of Iran

## B. Automated Legal Pack

- [ ] Developer's GitHub username verified
- [ ] Current `.github/legal/AGREEMENT_VERSION` recorded
- [ ] Developer/IP/Confidentiality Agreement read and accepted through `ForgeFlow Legal Gate`
- [ ] Engineering Access & Security Policy included in the accepted Legal Pack
- [ ] Offboarding/return/deletion obligations included in the accepted Legal Pack
- [ ] Developer selected `Pre-Existing IP: NONE` or `DISCLOSED SEPARATELY`
- [ ] If `DISCLOSED SEPARATELY`, detailed disclosure was received privately
- [ ] If `DISCLOSED SEPARATELY`, `@HoosseinRahimi` posted the exact Legal Gate owner-approval statement only after reviewing the disclosure
- [ ] `ForgeFlow Legal Gate` commit status is green before merge
- [ ] No promised equity, ownership, partnership or revenue share exists unless separately documented in writing

## C. Stronger e-signature layer when appropriate

For higher-value or sensitive engagements, also use a dedicated e-signature provider and retain:

- the final signed agreement;
- signer identity/contact evidence appropriate to the process;
- effective date;
- agreement/Legal Pack version;
- provider certificate/audit trail;
- later amendments.

The GitHub Legal Gate is useful authenticated electronic evidence but is not represented as automatically satisfying every higher secure-electronic-signature standard under Iranian law.

## D. IP chain-of-title record

For each contributor, keep a private record outside the code repository as appropriate containing:

- contributor legal identity;
- GitHub username;
- Legal Pack acceptance comment URL and timestamp;
- effective/version date;
- work scope;
- pre-existing IP list when one exists;
- licences granted for retained pre-existing IP;
- third-party approvals;
- later amendments;
- termination/offboarding record.

Do not place identity documents, home addresses, payment data, detailed confidential IP disclosures or signed HR records in this Git repository.

## E. Access authorization

- [ ] Default repository role set to Write unless a documented exception exists
- [ ] No Admin/Maintain role granted without explicit approval
- [ ] Production/deployment access separately justified
- [ ] Shared credentials avoided
- [ ] MFA enabled where supported/required
- [ ] Developer understands branch/PR workflow

## F. First contribution checks

- [ ] Feature branch used
- [ ] PR opened to `main`
- [ ] `ForgeFlow Legal Gate` passes
- [ ] CI/Security checks pass
- [ ] CODEOWNER review completed where enforced
- [ ] No secrets or personal data committed
- [ ] Third-party/AI-assisted material reviewed
- [ ] Pre-existing IP disclosure updated if needed

## G. Offboarding trigger

Create an offboarding task immediately when the engagement ends or access is no longer needed. Revoke access first, rotate affected credentials as appropriate, then complete the return/deletion record described in `.github/legal/FORGEFLOW_OFFBOARDING_RETURN_DELETION_ACKNOWLEDGEMENT.md` and `developer-access-policy.md`.

## H. Future company incorporation

When ForgeFlow is incorporated:

- [ ] Founder-to-company IP assignment executed
- [ ] Historical contributor Legal Pack/e-sign records preserved as chain-of-title evidence
- [ ] New Legal Pack version names the company directly
- [ ] GitHub organization/repository ownership reviewed
- [ ] Access register and policies updated