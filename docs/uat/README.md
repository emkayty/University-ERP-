# UAT Test Scripts for Nigerian University MIS

## Student UAT Script

### Preconditions
- Test student account created
- Test JAMB record in staging environment

### Test Steps

#### 1. Registration & Application
- [ ] Navigate to `/apply/`
- [ ] Fill application form with test data
- [ ] Submit application
- [ ] Verify SMS notification received (check logs)
- [ ] Verify application shows "Pending JAMB Verification" status

#### 2. Admission & Clearance
- [ ] Login as Registrar
- [ ] Find test application
- [ ] Set status to "JAMB Verified" → "Offered" → "Accepted"
- [ ] Login as test student
- [ ] Accept offer
- [ ] Complete clearance steps
- [ ] Verify matric number generated and displayed

#### 3. Fee Payment
- [ ] Navigate to `/student/fees/`
- [ ] Select fee type
- [ ] Generate Remita RRR
- [ ] Process payment via test gateway
- [ ] Verify receipt generation
- [ ] Verify "Payment Successful" SMS (check logs)

#### 4. Course Registration
- [ ] Navigate to `/student/registration/`
- [ ] Add courses to cart (max 24 credits)
- [ ] Submit registration
- [ ] Verify confirmation
- [ ] Attempt exceeding credit limit → verify error

#### 5. Results
- [ ] Login as Lecturer → enter scores
- [ ] Login as HOD → approve
- [ ] Login as Dean → approve
- [ ] Login as Exam Officer → compile
- [ ] Login as VC → ratify (senate ratification)
- [ ] Login as test student → view results
- [ ] Verify CGPA calculation

#### 6. Transcript
- [ ] Navigate to `/student/transcript-request/`
- [ ] Request official transcript (institutional email destination)
- [ ] Verify destination validation passes
- [ ] Request to personal email → verify blocked

#### 7. Graduation
- [ ] Check graduation eligibility checklist
- [ ] All items should be checked
- [ ] Apply for graduation

### Expected Results
- All steps complete without errors
- Correct status shown at each stage
- Proper validation messages displayed

---

## Registrar UAT Script

### Preconditions
- Registrar account created with 2FA enabled

### Test Steps

#### 1. Academic Setup
- [ ] Create new academic session
- [ ] Create semester within session
- [ ] Create grading configuration

#### 2. Admissions
- [ ] View admissions funnel
- [ ] Approve/reject applications in bulk
- [ ] Generate admission list

#### 3. Results
- [ ] View result status board
- [ ] Review result batch
- [ ] Approve through FSM stages

#### 4. Transcripts
- [ ] Process transcript request queue
- [ ] Generate transcript PDF
- [ ] Dispatch transcript

#### 5. Reports
- [ ] Generate NUC annual returns
- [ ] Verify output format

---

## Bursar UAT Script

### Preconditions
- Bursar account created

### Test Steps

#### 1. Fee Configuration
- [ ] Create fee type
- [ ] Set fee schedule for session
- [ ] Configure payment deadline

#### 2. Payment Processing
- [ ] Process manual payment
- [ ] Process refund
- [ ] Configure fee waiver

#### 3. Reconciliation
- [ ] Run payment reconciliation
- [ ] View unmatched payments
- [ ] Match payment to invoice

#### 4. Reports
- [ ] Run daily revenue report
- [ ] Run outstanding debtors report
- [ ] Export to Excel

---

## VC UAT Script

### Preconditions
- VC account created with 2FA enabled

### Test Steps

#### 1. Dashboard
- [ ] Load VC dashboard
- [ ] Verify all KPIs display correctly
- [ ] Verify charts render

#### 2. Accreditation
- [ ] View accreditation readiness
- [ ] View programme status

#### 3. Reports
- [ ] Generate enrollment report
- [ ] Generate financial summary

---

## Technical UAT

### Preconditions
- Test environment deployed

### Test Steps

#### 1. Performance
- [ ] Load test: 500 concurrent users
- [ ] API response time < 2s
- [ ] Dashboard load < 2s

#### 2. Security
- [ ] SQL injection test (manual)
- [ ] XSS test (manual)
- [ ] 2FA flow works

#### 3. PWA
- [ ] Install as PWA
- [ ] Test offline mode
- [ ] Test sync when online

#### 4. Backup/Restore
- [ ] Verify backup runs
- [ ] Test restore procedure