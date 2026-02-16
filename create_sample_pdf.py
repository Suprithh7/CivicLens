from fpdf import FPDF

# Create PDF
pdf = FPDF()
pdf.add_page()
pdf.set_font("Arial", "B", 16)

# Title
pdf.cell(0, 10, "Federal Student Loan Forgiveness Program 2024", 0, 1, "C")
pdf.ln(5)

# Content
pdf.set_font("Arial", "", 11)

sections = [
    ("OVERVIEW", "This policy outlines the eligibility criteria, application process, and benefits for the Federal Student Loan Forgiveness Program established in 2024."),
    
    ("SECTION 1: ELIGIBILITY REQUIREMENTS", "To qualify for student loan forgiveness under this program, applicants must meet ALL of the following criteria:"),
    
    ("1.1 Income Requirements", "- Annual household income below $125,000 for individual filers\n- Annual household income below $250,000 for married couples filing jointly\n- Income verified through most recent federal tax return"),
    
    ("1.2 Loan Requirements", "- Federal student loans obtained before July 1, 2022\n- Loans must be in good standing (not in default)\n- At least 10 years of qualifying payments made\n- Includes Direct Loans, FFEL Program loans, and Perkins Loans"),
    
    ("1.3 Employment Requirements", "- Full-time employment in public service sector, OR\n- Full-time employment in qualifying non-profit organization, OR\n- Teaching in low-income school district for minimum 5 years"),
    
    ("1.4 Citizenship Requirements", "- U.S. citizenship or permanent residency status\n- Valid Social Security number\n- No outstanding federal debts or tax liens"),
    
    ("SECTION 2: FORGIVENESS AMOUNTS", "The program offers tiered forgiveness based on income level and loan balance:"),
    
    ("2.1 Standard Forgiveness Tiers", "- Income under $75,000: Up to $20,000 forgiveness\n- Income $75,000-$100,000: Up to $15,000 forgiveness\n- Income $100,000-$125,000: Up to $10,000 forgiveness"),
    
    ("2.2 Enhanced Forgiveness for Pell Grant Recipients", "- Pell Grant recipients receive an additional $5,000\n- Must provide proof of Pell Grant award\n- Applies to all income tiers"),
    
    ("2.3 Public Service Bonus", "- Additional $3,000 for qualifying public service employees\n- Requires 5+ years of continuous public service\n- Must be employed at time of application"),
    
    ("SECTION 3: APPLICATION PROCESS", "Follow these steps to apply for loan forgiveness:"),
    
    ("3.1 Account Creation", "- Visit StudentAid.gov\n- Create Federal Student Aid (FSA) ID if you don't have one\n- Link existing student loan accounts"),
    
    ("3.2 Application Submission", "- Complete online application form\n- Provide employment verification\n- Upload required documentation\n- Review and submit application"),
    
    ("3.3 Documentation Requirements", "- Most recent federal tax return (1040 form)\n- Proof of employment (pay stubs or employer letter)\n- Student loan account statements\n- Social Security card or number\n- Valid government-issued photo ID\n- Pell Grant award letter (if applicable)"),
    
    ("3.4 Review Process", "- Initial review: 2-3 weeks\n- Document verification: 1-2 weeks\n- Final approval: 1-2 weeks\n- Total processing time: 4-6 weeks"),
    
    ("SECTION 4: IMPORTANT DATES", "Key dates and deadlines:"),
    
    ("4.1 Program Timeline", "- Application Period Opens: January 1, 2024\n- Application Deadline: December 31, 2024\n- First Disbursements Begin: March 2024\n- Final Disbursements: June 2025\n- Program End Date: December 31, 2025"),
    
    ("SECTION 5: FREQUENTLY ASKED QUESTIONS", ""),
    
    ("Q: Can I apply if I'm currently in school?", "A: No, you must have completed your education and be in repayment status."),
    
    ("Q: Will this forgiveness affect my credit score?", "A: No, loan forgiveness does not negatively impact credit scores."),
    
    ("Q: Is the forgiven amount taxable?", "A: Under current federal law, forgiven amounts are not considered taxable income through 2025."),
    
    ("Q: Can I apply if I refinanced my federal loans?", "A: No, only federal student loans qualify for this program."),
    
    ("SECTION 6: CONTACT INFORMATION", "For questions or assistance:\n- Federal Student Aid Information Center: 1-800-433-3243\n- TTY for hearing impaired: 1-800-730-8913\n- Website: StudentAid.gov\n- Email: FederalStudentAidCustomerService@ed.gov\n- Hours: Monday-Friday, 8:00 AM - 8:00 PM ET"),
]

for title, content in sections:
    pdf.set_font("Arial", "B", 12)
    pdf.multi_cell(0, 6, title)
    pdf.ln(2)
    
    if content:
        pdf.set_font("Arial", "", 10)
        pdf.multi_cell(0, 5, content)
        pdf.ln(4)

# Save PDF
pdf.output("Sample_Student_Loan_Policy.pdf")
print("PDF created successfully!")
