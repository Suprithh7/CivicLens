"""
Standalone verification script for the PSLF eligibility rule engine.
Runs without pytest (avoids eth_typing blockchain package incompatibility).
"""
from types import SimpleNamespace
from app.services.eligibility_rules.pslf import check_pslf
from app.services.eligibility_rules.engine import run_eligibility_check, UnsupportedPolicyError


def p(**kw):
    defaults = dict(
        has_federal_student_loans=True,
        loan_in_default=False,
        employment_status="employed_full_time",
        employer_type="government",
        years_of_loan_payments=10.0,
        citizenship_status="citizen",
    )
    defaults.update(kw)
    return SimpleNamespace(**defaults)


cases = [
    ("Full eligible",        p(),                                                       "eligible"),
    ("No federal loans",     p(has_federal_student_loans=False),                        "not_eligible"),
    ("Loan in default",      p(loan_in_default=True),                                  "not_eligible"),
    ("Part-time work",       p(employment_status="employed_part_time"),                 "not_eligible"),
    ("Private employer",     p(employer_type="private"),                                "not_eligible"),
    ("Only 5yr payments",    p(years_of_loan_payments=5.0),                            "partial"),
    ("Visa holder",          p(citizenship_status="visa_holder"),                       "not_eligible"),
    ("Missing loans field",  p(has_federal_student_loans=None),                         "needs_more_info"),
    ("Missing employer",     p(employer_type=None),                                     "needs_more_info"),
    ("Nonprofit employer",   p(employer_type="nonprofit"),                              "eligible"),
    ("Perm resident",        p(citizenship_status="permanent_resident"),                "eligible"),
    ("Blank profile",        SimpleNamespace(
        has_federal_student_loans=None, loan_in_default=None,
        employment_status=None, employer_type=None,
        years_of_loan_payments=None, citizenship_status=None,
    ),                                                                                  "needs_more_info"),
]

all_pass = True
for name, profile, expected in cases:
    r = check_pslf(profile)
    ok = r.result == expected
    if not ok:
        all_pass = False
    tag = "PASS" if ok else "FAIL"
    print(f"  [{tag}] {name}: got={r.result}  expected={expected}")

# Engine dispatcher tests
try:
    run_eligibility_check(p(), "medicaid")
    print("  [FAIL] UnsupportedPolicyError not raised")
    all_pass = False
except UnsupportedPolicyError:
    print("  [PASS] UnsupportedPolicyError raised for unknown slug")

r2 = run_eligibility_check(p(), "PSLF")
tag2 = "PASS" if r2.result == "eligible" else "FAIL"
print(f"  [{tag2}] Case-insensitive slug: got={r2.result}")
if r2.result != "eligible":
    all_pass = False

print()
print("ALL TESTS PASSED" if all_pass else "SOME TESTS FAILED")
