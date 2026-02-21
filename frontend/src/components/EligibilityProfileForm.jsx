/**
 * EligibilityProfileForm
 * A 5-step wizard for capturing a user's eligibility profile.
 * All fields are optional.  Only an anonymous session_id (from localStorage)
 * is required — no real names or emails are ever collected.
 */

import React, { useState, useCallback } from 'react';
import './EligibilityProfileForm.css';
import { submitEligibilityProfile } from '../services/api';

// ─── helpers ────────────────────────────────────────────────────────────────

function getOrCreateSessionId() {
  const KEY = 'cl_session_id';
  let id = localStorage.getItem(KEY);
  if (!id) {
    id = `sess_${crypto.randomUUID()}`;
    localStorage.setItem(KEY, id);
  }
  return id;
}

const US_STATES = [
  'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
  'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
  'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
  'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
  'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY', 'DC',
];

const STEPS = [
  { label: 'Financial', icon: 'blue' },
  { label: 'Demographics', icon: 'purple' },
  { label: 'Employment', icon: 'green' },
  { label: 'Location', icon: 'orange' },
  { label: 'Loans', icon: 'sky' },
];

// ─── sub-components ─────────────────────────────────────────────────────────

function ToggleRow({ id, label, hint, checked, onChange }) {
  return (
    <div className="epf-toggle-row">
      <div className="epf-toggle-row-text">
        <strong>{label}</strong>
        {hint && <span>{hint}</span>}
      </div>
      <label className="epf-switch" htmlFor={id}>
        <input
          id={id}
          type="checkbox"
          checked={checked}
          onChange={e => onChange(e.target.checked)}
          aria-checked={checked}
        />
        <span className="epf-slider" />
      </label>
    </div>
  );
}

/**
 * Tri-state select: Yes / No / Unknown (blank)
 * Maps to true / false / null for the backend.
 */
function TriStateSelect({ id, label, hint, value, onChange }) {
  return (
    <div className="epf-field">
      <label className="epf-label" htmlFor={id}>
        {label}
        <span className="epf-optional">(optional)</span>
      </label>
      {hint && <p style={{ fontSize: '0.8rem', color: '#64748b', margin: '0 0 6px' }}>{hint}</p>}
      <select
        id={id}
        className="epf-select"
        value={value}
        onChange={e => onChange(e.target.value)}
      >
        <option value="">— Unknown / Prefer not to say —</option>
        <option value="yes">Yes</option>
        <option value="no">No</option>
      </select>
    </div>
  );
}

function Field({ label, optional = true, error, children }) {
  return (
    <div className="epf-field">
      <label className="epf-label">
        {label}
        {optional && <span className="epf-optional">(optional)</span>}
      </label>
      {children}
      {error && <span className="epf-field-error">{error}</span>}
    </div>
  );
}

/**
 * Reveal — animated show/hide wrapper for progressive disclosure.
 * Children slide in with opacity + max-height when `open` is true,
 * and slide back out when false. Stale child state is cleared by the
 * parent before hiding (see update() in EligibilityProfileForm).
 */
function Reveal({ open, hint, children }) {
  return (
    <div className={`epf-reveal${open ? ' open' : ''}`}>
      {hint && (
        <p className="epf-disclosure-hint">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
          {hint}
        </p>
      )}
      {children}
    </div>
  );
}

// ─── step panels ─────────────────────────────────────────────────────────────

function StepFinancial({ data, update, errors }) {
  return (
    <>
      {/* Privacy notice – only on first step */}
      <div className="epf-privacy-notice" role="note">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
        </svg>
        <div>
          <strong>Your privacy matters.</strong> We use an anonymous session ID — no name, email,
          or identifying information is collected. Your answers help us match you with relevant
          government policies. You can leave any field blank.
        </div>
      </div>

      <div className="epf-fields">
        <Field label="Annual Household Income (USD)" error={errors.annual_income}>
          <input
            id="annual_income"
            type="number"
            min="0"
            step="1000"
            className={`epf-input ${errors.annual_income ? 'error' : ''}`}
            placeholder="e.g. 65000"
            value={data.annual_income}
            onChange={e => update('annual_income', e.target.value === '' ? '' : parseFloat(e.target.value))}
          />
        </Field>

        <Field label="Household Size">
          <input
            id="household_size"
            type="number"
            min="1"
            max="50"
            className="epf-input"
            placeholder="e.g. 3"
            value={data.household_size}
            onChange={e => update('household_size', e.target.value === '' ? '' : parseInt(e.target.value, 10))}
          />
        </Field>

        <Field label="Tax Filing Status" optional>
          <select
            id="filing_status"
            className="epf-select"
            value={data.filing_status}
            onChange={e => update('filing_status', e.target.value)}
          >
            <option value="">— Select —</option>
            <option value="single">Single</option>
            <option value="married_joint">Married Filing Jointly</option>
            <option value="married_separate">Married Filing Separately</option>
            <option value="head_of_household">Head of Household</option>
          </select>
        </Field>
      </div>
    </>
  );
}

function StepDemographics({ data, update }) {
  return (
    <div>
      <div className="epf-fields" style={{ marginBottom: 24 }}>
        <Field label="Age">
          <input
            id="age"
            type="number"
            min="0"
            max="130"
            className="epf-input"
            placeholder="e.g. 34"
            value={data.age}
            onChange={e => update('age', e.target.value === '' ? '' : parseInt(e.target.value, 10))}
          />
        </Field>

        <Field label="Citizenship / Immigration Status">
          <select
            id="citizenship_status"
            className="epf-select"
            value={data.citizenship_status}
            onChange={e => update('citizenship_status', e.target.value)}
          >
            <option value="">— Select —</option>
            <option value="citizen">U.S. Citizen</option>
            <option value="permanent_resident">Permanent Resident (Green Card)</option>
            <option value="visa_holder">Visa Holder</option>
            <option value="undocumented">Undocumented</option>
          </select>
        </Field>
      </div>

      <div className="epf-toggles">
        <ToggleRow
          id="is_veteran"
          label="Military Veteran"
          hint="Are you a veteran of the U.S. armed forces?"
          checked={data.is_veteran}
          onChange={v => update('is_veteran', v)}
        />
        <ToggleRow
          id="is_disabled"
          label="Has Qualifying Disability"
          hint="Do you have a disability recognised under federal or state programs?"
          checked={data.is_disabled}
          onChange={v => update('is_disabled', v)}
        />
        <ToggleRow
          id="has_dependents"
          label="Claims Dependents"
          hint="Do you claim any dependents on your tax return?"
          checked={data.has_dependents}
          onChange={v => update('has_dependents', v)}
        />
      </div>

      {/* ── Progressive disclosure: num_dependents ── */}
      <Reveal
        open={data.has_dependents}
        hint="How many dependents do you claim?"
      >
        <div className="epf-fields">
          <Field label="Number of Dependents" error={null}>
            <input
              id="num_dependents"
              type="number"
              min="0"
              className="epf-input"
              placeholder="e.g. 2"
              value={data.num_dependents}
              onChange={e => update('num_dependents', e.target.value === '' ? '' : parseInt(e.target.value, 10))}
            />
          </Field>
        </div>
      </Reveal>
    </div>
  );
}

// Employment statuses that have an employer (disclose employer type + tenure)
const HAS_EMPLOYER = new Set([
  'employed_full_time', 'employed_part_time', 'self_employed', 'military',
]);

function StepEmployment({ data, update }) {
  const hasEmployer = HAS_EMPLOYER.has(data.employment_status);

  return (
    <div>
      <div className="epf-fields" style={{ marginBottom: 24 }}>
        <Field label="Employment Status">
          <select
            id="employment_status"
            className="epf-select"
            value={data.employment_status}
            onChange={e => update('employment_status', e.target.value)}
          >
            <option value="">— Select —</option>
            <option value="employed_full_time">Employed Full-Time</option>
            <option value="employed_part_time">Employed Part-Time</option>
            <option value="self_employed">Self-Employed</option>
            <option value="unemployed">Unemployed</option>
            <option value="retired">Retired</option>
            <option value="student">Student</option>
          </select>
        </Field>

        <Field label="Highest Education Level">
          <select
            id="education_level"
            className="epf-select"
            value={data.education_level}
            onChange={e => update('education_level', e.target.value)}
          >
            <option value="">— Select —</option>
            <option value="less_than_hs">Less than High School</option>
            <option value="high_school">High School / GED</option>
            <option value="some_college">Some College</option>
            <option value="associates">Associate's Degree</option>
            <option value="bachelors">Bachelor's Degree</option>
            <option value="graduate">Graduate / Professional Degree</option>
          </select>
        </Field>
      </div>

      {/* ── Progressive disclosure: employer fields ── */}
      <Reveal
        open={hasEmployer}
        hint="Tell us about your employer — this matters for public-service programs."
      >
        <div className="epf-fields">
          <Field label="Employer Type">
            <select
              id="employer_type"
              className="epf-select"
              value={data.employer_type}
              onChange={e => update('employer_type', e.target.value)}
            >
              <option value="">— Select —</option>
              <option value="government">Government</option>
              <option value="nonprofit">Non-Profit</option>
              <option value="private">Private Sector</option>
              <option value="military">Military</option>
              <option value="education">Education</option>
            </select>
          </Field>

          <Field label="Years with Current Employer">
            <input
              id="years_employed"
              type="number"
              min="0"
              step="0.5"
              className="epf-input"
              placeholder="e.g. 5.5"
              value={data.years_employed}
              onChange={e => update('years_employed', e.target.value === '' ? '' : parseFloat(e.target.value))}
            />
          </Field>
        </div>
      </Reveal>

      <div className="epf-toggles" style={{ marginTop: 20 }}>
        <ToggleRow
          id="is_student"
          label="Currently Enrolled as Full-Time Student"
          hint="Are you currently enrolled in a college or university full-time?"
          checked={data.is_student}
          onChange={v => update('is_student', v)}
        />
      </div>
    </div>
  );
}

function StepLocation({ data, update }) {
  return (
    <div>
      <div className="epf-fields" style={{ marginBottom: 24 }}>
        <Field label="State">
          <select
            id="state"
            className="epf-select"
            value={data.state}
            onChange={e => update('state', e.target.value)}
          >
            <option value="">— Select state —</option>
            {US_STATES.map(s => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </Field>

        <Field label="Area Type">
          <select
            id="location_type"
            className="epf-select"
            value={data.location_type}
            onChange={e => update('location_type', e.target.value)}
          >
            <option value="">— Select —</option>
            <option value="urban">Urban (city)</option>
            <option value="suburban">Suburban</option>
            <option value="rural">Rural</option>
          </select>
        </Field>
      </div>

      <div className="epf-fields">
        <TriStateSelect
          id="has_health_insurance"
          label="Has Health Insurance"
          hint="Do you currently have any health insurance coverage?"
          value={data.has_health_insurance}
          onChange={v => update('has_health_insurance', v)}
        />
        <TriStateSelect
          id="owns_home"
          label="Homeowner"
          hint="Do you own your primary residence?"
          value={data.owns_home}
          onChange={v => update('owns_home', v)}
        />
      </div>
    </div>
  );
}

function StepLoans({ data, update }) {
  const hasLoans = data.has_federal_student_loans;

  return (
    <div>
      <div className="epf-toggles" style={{ marginBottom: 4 }}>
        <ToggleRow
          id="has_federal_student_loans"
          label="Has Federal Student Loans"
          hint="Do you currently hold federal student loan debt?"
          checked={data.has_federal_student_loans}
          onChange={v => update('has_federal_student_loans', v)}
        />
      </div>

      {/* ── Progressive disclosure: loan detail fields ── */}
      <Reveal
        open={hasLoans}
        hint="Great — a few more details will help us check forgiveness &amp; repayment eligibility."
      >
        <div className="epf-fields">
          <TriStateSelect
            id="loan_in_default"
            label="Loans Currently in Default"
            hint="Are any of your federal student loans in default status?"
            value={data.loan_in_default}
            onChange={v => update('loan_in_default', v)}
          />

          <TriStateSelect
            id="received_pell_grant"
            label="Ever Received a Pell Grant"
            hint="Did you receive a Federal Pell Grant as an undergraduate student?"
            value={data.received_pell_grant}
            onChange={v => update('received_pell_grant', v)}
          />

          <Field label="Years of Qualifying Loan Payments Made">
            <input
              id="years_of_loan_payments"
              type="number"
              min="0"
              step="0.5"
              className="epf-input"
              placeholder="e.g. 10"
              value={data.years_of_loan_payments}
              onChange={e => update('years_of_loan_payments', e.target.value === '' ? '' : parseFloat(e.target.value))}
            />
          </Field>
        </div>
      </Reveal>
    </div>
  );
}


// ─── section metadata ────────────────────────────────────────────────────────

const SECTION_META = [
  {
    title: 'Financial Information',
    subtitle: 'Help us understand your income and household.',
    iconColor: 'blue',
    iconPath: 'M12 1v22M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6',
  },
  {
    title: 'Demographics',
    subtitle: 'Basic personal characteristics for eligibility matching.',
    iconColor: 'purple',
    iconPath: 'M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2M12 3a4 4 0 100 8 4 4 0 000-8z',
  },
  {
    title: 'Employment & Education',
    subtitle: 'Your current work situation and education background.',
    iconColor: 'green',
    iconPath: 'M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6l2 2-4 4-4-4 2-2M12 3v10',
  },
  {
    title: 'Location',
    subtitle: 'Where you live affects which programs you qualify for.',
    iconColor: 'orange',
    iconPath: 'M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z M15 11a3 3 0 11-6 0 3 3 0 016 0z',
  },
  {
    title: 'Student Loans',
    subtitle: 'Federal loan details for forgiveness & repayment programs.',
    iconColor: 'sky',
    iconPath: 'M12 14l9-5-9-5-9 5 9 5zM12 14l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14z',
  },
];

// ─── main component ──────────────────────────────────────────────────────────

const INITIAL_DATA = {
  // Financial
  annual_income: '',
  household_size: '',
  filing_status: '',
  // Demographics
  age: '',
  citizenship_status: '',
  is_veteran: false,
  is_disabled: false,
  has_dependents: false,
  num_dependents: '',
  // Employment
  employment_status: '',
  employer_type: '',
  years_employed: '',
  education_level: '',
  is_student: false,
  // Location
  state: '',
  location_type: '',
  has_health_insurance: '',  // tri-state: '' | 'yes' | 'no'
  owns_home: '',             // tri-state: '' | 'yes' | 'no'
  // Loans
  has_federal_student_loans: false,
  loan_in_default: '',       // tri-state: '' | 'yes' | 'no'
  received_pell_grant: '',   // tri-state: '' | 'yes' | 'no'
  years_of_loan_payments: '',
};

/** Map tri-state string value to boolean or omit if unknown */
function triStateToBool(val) {
  if (val === 'yes') return true;
  if (val === 'no') return false;
  return undefined; // '' → omit from payload
}

function buildPayload(data, sessionId) {
  const payload = { session_id: sessionId };
  // Only include non-empty optional numeric fields
  const numFields = ['annual_income', 'household_size', 'age', 'num_dependents', 'years_employed', 'years_of_loan_payments'];
  const strFields = ['filing_status', 'citizenship_status', 'employment_status', 'employer_type', 'education_level', 'state', 'location_type'];
  for (const f of numFields) {
    if (data[f] !== '' && data[f] !== null && data[f] !== undefined) {
      payload[f] = Number(data[f]);
    }
  }
  for (const f of strFields) {
    if (data[f]) payload[f] = data[f];
  }
  // Standard booleans — always include (safe defaults)
  payload.is_veteran = data.is_veteran;
  payload.is_disabled = data.is_disabled;
  payload.has_dependents = data.has_dependents;
  payload.is_student = data.is_student;
  payload.has_federal_student_loans = data.has_federal_student_loans;
  // Tri-state fields — only include if user made a choice
  const triFields = ['loan_in_default', 'received_pell_grant', 'has_health_insurance', 'owns_home'];
  for (const f of triFields) {
    const mapped = triStateToBool(data[f]);
    if (mapped !== undefined) payload[f] = mapped;
  }
  return payload;
}

export default function EligibilityProfileForm() {
  const [sessionId] = useState(getOrCreateSessionId);
  const [step, setStep] = useState(0);         // 0-4
  const [data, setData] = useState(INITIAL_DATA);
  const [errors, setErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [submitResult, setSubmitResult] = useState(null); // {ok, message}

  // Child fields to clear when their disclosure gate is toggled off
  const CHILD_FIELDS = {
    has_dependents: { num_dependents: '' },
    has_federal_student_loans: { loan_in_default: '', received_pell_grant: '', years_of_loan_payments: '' },
  };

  // Disclosure gates keyed on employment_status change
  const EMPLOYER_FIELDS = ['employer_type', 'years_employed'];
  const HAS_EMPLOYER_SET = new Set([
    'employed_full_time', 'employed_part_time', 'self_employed', 'military',
  ]);

  const update = useCallback((field, value) => {
    setData(prev => {
      const next = { ...prev, [field]: value };

      // Clear dependent child fields when gate is toggled off
      if (field in CHILD_FIELDS && !value) {
        Object.assign(next, CHILD_FIELDS[field]);
      }

      // Clear employer sub-fields when switching to a non-employer status
      if (field === 'employment_status' && !HAS_EMPLOYER_SET.has(value)) {
        for (const f of EMPLOYER_FIELDS) next[f] = '';
      }

      return next;
    });
    setErrors(prev => ({ ...prev, [field]: undefined }));
  }, []);


  function validate() {
    const errs = {};
    if (step === 0) {
      if (data.annual_income !== '' && Number(data.annual_income) < 0) {
        errs.annual_income = 'Income must be 0 or more.';
      }
      if (data.household_size !== '' && Number(data.household_size) < 1) {
        errs.household_size = 'Household size must be at least 1.';
      }
    }
    if (step === 1) {
      if (data.age !== '' && (Number(data.age) < 0 || Number(data.age) > 130)) {
        errs.age = 'Age must be between 0 and 130.';
      }
      if (data.num_dependents !== '' && Number(data.num_dependents) < 0) {
        errs.num_dependents = 'Number of dependents cannot be negative.';
      }
    }
    if (step === 2) {
      if (data.years_employed !== '' && Number(data.years_employed) < 0) {
        errs.years_employed = 'Years employed cannot be negative.';
      }
    }
    if (step === 4) {
      if (data.years_of_loan_payments !== '' && Number(data.years_of_loan_payments) < 0) {
        errs.years_of_loan_payments = 'Years of payments cannot be negative.';
      }
    }
    setErrors(errs);
    return Object.keys(errs).length === 0;
  }

  function handleNext() {
    if (!validate()) return;
    setStep(s => Math.min(s + 1, STEPS.length - 1));
  }

  function handleBack() {
    setStep(s => Math.max(s - 1, 0));
  }

  async function handleSubmit() {
    if (!validate()) return;
    setSubmitting(true);
    setSubmitResult(null);
    try {
      const payload = buildPayload(data, sessionId);
      const result = await submitEligibilityProfile(payload);
      setSubmitResult({ ok: true, data: result });
    } catch (err) {
      setSubmitResult({ ok: false, message: err.message || 'Submission failed. Please try again.' });
      setSubmitting(false);
    }
  }

  const isLastStep = step === STEPS.length - 1;
  const meta = SECTION_META[step];

  // ── Success screen ────────────────────────────────────────────────────────
  if (submitResult?.ok) {
    return (
      <div className="epf-wrapper">
        <div className="epf-section-card epf-success-state">
          <div className="epf-success-icon">
            <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#16a34a" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="20 6 9 17 4 12" />
            </svg>
          </div>
          <h3>Profile Saved!</h3>
          <p>
            Your eligibility profile has been securely stored. Browse policies and click <strong>Check My Eligibility</strong> to see how you qualify.
          </p>
          <div>
            <span className="epf-session-tag">Session: {sessionId}</span>
          </div>
          <div style={{ marginTop: 28, display: 'flex', gap: 12, justifyContent: 'center', flexWrap: 'wrap' }}>
            <button
              className="epf-btn epf-btn-secondary"
              onClick={() => { setData(INITIAL_DATA); setStep(0); setSubmitResult(null); }}
            >
              ← Edit Profile
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ── Wizard ────────────────────────────────────────────────────────────────
  return (
    <div className="epf-wrapper">
      {/* Step progress bar */}
      <div className="epf-progress" role="progressbar" aria-valuenow={step + 1} aria-valuemax={STEPS.length}>
        {STEPS.map((s, i) => (
          <React.Fragment key={s.label}>
            {i > 0 && <div className={`epf-step-connector ${i <= step ? 'done' : ''}`} />}
            <div className={`epf-step-bubble ${i < step ? 'done' : i === step ? 'active' : ''}`}>
              <div className="epf-step-bubble-circle">
                {i < step ? (
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                ) : (
                  i + 1
                )}
              </div>
              <span className="epf-step-bubble-label">{s.label}</span>
            </div>
          </React.Fragment>
        ))}
      </div>

      {/* Section card */}
      <div className="epf-section-card">
        {/* Header */}
        <div className="epf-section-header">
          <div className={`epf-section-icon ${meta.iconColor}`}>
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <path d={meta.iconPath} />
            </svg>
          </div>
          <div>
            <h2 className="epf-section-title">{meta.title}</h2>
            <p className="epf-section-subtitle">{meta.subtitle}</p>
          </div>
        </div>

        {/* Error banner from submit */}
        {submitResult && !submitResult.ok && (
          <div className="epf-banner error" role="alert">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10" /><line x1="15" y1="9" x2="9" y2="15" /><line x1="9" y1="9" x2="15" y2="15" />
            </svg>
            <span>{submitResult.message}</span>
          </div>
        )}

        {/* Step content */}
        {step === 0 && <StepFinancial data={data} update={update} errors={errors} />}
        {step === 1 && <StepDemographics data={data} update={update} />}
        {step === 2 && <StepEmployment data={data} update={update} />}
        {step === 3 && <StepLocation data={data} update={update} />}
        {step === 4 && <StepLoans data={data} update={update} />}

        {/* Navigation */}
        <div className="epf-nav">
          <button
            className="epf-btn epf-btn-secondary"
            onClick={handleBack}
            disabled={step === 0}
            style={{ visibility: step === 0 ? 'hidden' : 'visible' }}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="15 18 9 12 15 6" />
            </svg>
            Back
          </button>

          <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>
            Step {step + 1} of {STEPS.length}
          </span>

          {!isLastStep ? (
            <button className="epf-btn epf-btn-primary" onClick={handleNext}>
              Next
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="9 18 15 12 9 6" />
              </svg>
            </button>
          ) : (
            <button
              className="epf-btn epf-btn-primary epf-btn-submit"
              onClick={handleSubmit}
              disabled={submitting}
            >
              {submitting ? (
                <>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" style={{ animation: 'spin 1s linear infinite' }}>
                    <path d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" opacity=".25" /><path d="M12 3a9 9 0 019 9" />
                  </svg>
                  Saving…
                </>
              ) : (
                <>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M19 21H5a2 2 0 01-2-2V5a2 2 0 012-2h11l5 5v11a2 2 0 01-2 2z" /><polyline points="17 21 17 13 7 13 7 21" /><polyline points="7 3 7 8 15 8" />
                  </svg>
                  Save Profile
                </>
              )}
            </button>
          )}
        </div>
      </div>

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
