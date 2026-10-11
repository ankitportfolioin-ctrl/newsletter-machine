import { Router } from 'express';

const router = Router();

// Privacy Policy
router.get('/privacy', (req, res) => {
  res.json({
    title: 'Privacy Policy',
    lastUpdated: '2026-01-20',
    content: `
# Privacy Policy

**Last Updated:** January 20, 2026

## Introduction

Newsletter Machine ("we", "our", or "us") is committed to protecting your privacy. This Privacy Policy explains how we collect, use, disclose, and safeguard your information when you use our service.

## Information We Collect

### Personal Information
- **Email Address**: Used for account creation and communication
- **Name**: Optional, used for personalization
- **Password**: Stored securely using bcrypt hashing

### Usage Data
- **Niches**: Topics you configure for content collection
- **Sources**: RSS feeds and platforms you connect
- **Collection History**: Records of content collection runs
- **Newsletters**: Generated newsletter content
- **Feedback**: Your ratings and preferences

### Technical Data
- **IP Address**: For security and rate limiting
- **Browser Type**: For compatibility
- **Device Information**: For optimization
- **Log Data**: Timestamps, error logs, performance metrics

## How We Use Your Information

We use the collected information to:
1. **Provide the Service**: Generate newsletters based on your configured niches
2. **Improve Performance**: Optimize content collection and generation
3. **Security**: Protect against unauthorized access and abuse
4. **Communication**: Send important updates about your account
5. **Analytics**: Understand usage patterns to improve the service

## Data Storage and Security

### Encryption
- **Passwords**: Hashed using bcrypt with 10 rounds
- **Data in Transit**: Encrypted using HTTPS/TLS
- **API Keys**: Stored securely with encryption at rest

### Access Controls
- **Authentication**: JWT-based authentication with 7-day expiry
- **Authorization**: User data is isolated and accessible only to the owner
- **Rate Limiting**: Protection against abuse and DDoS attacks

### Data Retention
- **Account Data**: Retained until account deletion
- **Collection Data**: Retained for 90 days, then archived
- **Logs**: Retained for 30 days for debugging

## Third-Party Services

We integrate with the following third-party services:

### Content Sources
- **RSS Feeds**: Public RSS feeds from websites you specify
- **Reddit API**: Collects posts from configured subreddits
- **YouTube API**: Searches for videos based on your keywords

### AI Services
- **OpenAI**: Generates newsletter content (if configured)

These services have their own privacy policies. We only send them the data necessary for their function.

## Your Rights

### Access and Portability
You can request a copy of all your data at any time through the Settings page.

### Deletion
You can delete your account and all associated data through the Settings page. This action is irreversible.

### Correction
You can update your personal information (name, email) through your account settings.

### Objection
You can object to certain data processing by contacting us at privacy@newsmachine.example.com.

## Cookies and Tracking

We use minimal cookies for:
- **Authentication**: JWT tokens stored in localStorage
- **Preferences**: Theme preference (light/dark mode)

We do NOT use:
- Third-party tracking cookies
- Advertising cookies
- Analytics cookies (unless you opt-in)

## Children's Privacy

Our service is not intended for users under 16 years of age. We do not knowingly collect personal information from children.

## Changes to This Policy

We may update this Privacy Policy from time to time. We will notify you of any changes by:
- Posting the new policy on this page
- Updating the "Last Updated" date
- Sending an email for significant changes

## Contact Us

If you have questions about this Privacy Policy or our data practices:
- **Email**: privacy@newsmachine.example.com
- **Address**: [Your Business Address]

## GDPR Compliance

For users in the European Union, we comply with the General Data Protection Regulation (GDPR):
- **Lawful Basis**: We process data based on contract performance and legitimate interests
- **Data Protection Officer**: Available at dpo@newsmachine.example.com
- **Supervisory Authority**: You can lodge a complaint with your local data protection authority

## CCPA Compliance

For California residents, we comply with the California Consumer Privacy Act (CCPA):
- **Right to Know**: You can request what data we collect
- **Right to Delete**: You can request deletion of your data
- **Right to Opt-Out**: We do not sell your personal information

---

**By using Newsletter Machine, you agree to this Privacy Policy.**
    `,
  });
});

// Terms of Service
router.get('/terms', (req, res) => {
  res.json({
    title: 'Terms of Service',
    lastUpdated: '2026-01-20',
    content: `
# Terms of Service

**Last Updated:** January 20, 2026

## Acceptance of Terms

By accessing or using Newsletter Machine ("the Service"), you agree to be bound by these Terms of Service ("Terms"). If you do not agree to these Terms, do not use the Service.

## Description of Service

Newsletter Machine is a content aggregation and newsletter generation platform that:
- Collects content from RSS feeds, Reddit, and YouTube based on your configured niches
- Generates AI-powered newsletters summarizing collected content
- Provides a dashboard for managing niches, sources, and newsletter history

## User Accounts

### Registration
- You must provide accurate and complete information during registration
- You are responsible for maintaining the confidentiality of your account credentials
- You must be at least 16 years old to create an account

### Account Security
- You are responsible for all activities that occur under your account
- You must notify us immediately of any unauthorized access
- We recommend using strong, unique passwords

## Acceptable Use

### You Agree NOT to:
1. **Violate Laws**: Use the service for any illegal purpose
2. **Infringe Rights**: Collect or distribute content you don't have rights to
3. **Abuse the Service**: Attempt to overwhelm, disrupt, or exploit the service
4. **Scrape Excessively**: Make an unreasonable number of requests to source websites
5. **Misrepresent Content**: Present AI-generated content as human-written without disclosure
6. **Share Credentials**: Allow others to use your account
7. **Reverse Engineer**: Attempt to decompile or extract source code
8. **Resell Service**: Resell access to the service without authorization

### We Reserve the Right to:
- Suspend or terminate accounts that violate these Terms
- Remove content that violates these Terms
- Modify or discontinue the service at any time
- Refuse service to anyone for any reason

## Content and Intellectual Property

### Your Content
- You retain ownership of your niches, configurations, and feedback
- You grant us a license to use your content to provide the service
- You are responsible for ensuring you have rights to configured sources

### Our Content
- The service, including code, design, and documentation, is owned by Newsletter Machine
- AI-generated newsletters are provided "as-is" with no guarantee of accuracy
- You may use generated newsletters for personal or commercial purposes

### Third-Party Content
- Content collected from external sources remains owned by its original creators
- We provide links and summaries, not full reproduction of copyrighted material
- You are responsible for complying with source websites' terms of service

## AI-Generated Content

### Disclaimer
- Newsletters are generated using AI (OpenAI GPT-4)
- AI may produce inaccurate, incomplete, or biased content
- You should verify important information before relying on it
- We are not responsible for errors in AI-generated content

### Attribution
- AI-generated content should be attributed to "Newsletter Machine"
- Do not present AI-generated content as human research without disclosure
- Include source links when sharing newsletter content

## Privacy

Your use of the service is also governed by our [Privacy Policy](/api/legal/privacy). By using the service, you consent to our data practices as described in the Privacy Policy.

## Limitation of Liability

### To the Maximum Extent Permitted by Law:
- The service is provided "as-is" without warranties of any kind
- We are not liable for any indirect, incidental, special, or consequential damages
- Our total liability shall not exceed the amount you paid us in the last 12 months
- We are not liable for data loss, service interruptions, or security breaches

### Exceptions:
- This limitation does not apply to fraud, gross negligence, or willful misconduct
- Some jurisdictions do not allow liability limitations, so this may not apply to you

## Indemnification

You agree to indemnify and hold harmless Newsletter Machine from any claims, damages, or expenses arising from:
- Your use of the service
- Your violation of these Terms
- Your infringement of any third-party rights

## Termination

### By You:
- You can delete your account at any time through Settings
- All your data will be permanently deleted

### By Us:
- We can suspend or terminate your account for violating these Terms
- We can discontinue the service with 30 days notice
- We will attempt to provide data export before termination

## Changes to Terms

We may modify these Terms at any time. We will:
- Post the updated Terms on this page
- Update the "Last Updated" date
- Notify you of significant changes via email

Your continued use of the service after changes constitutes acceptance of the new Terms.

## Governing Law

These Terms are governed by the laws of [Your Jurisdiction], without regard to conflict of law principles.

## Dispute Resolution

### Informal Resolution
Before filing a claim, you agree to try informal resolution by contacting us at legal@newsmachine.example.com.

### Arbitration
For unresolved disputes, you agree to binding arbitration in [Your City/State], except:
- You can file a claim in small claims court
- You can seek injunctive relief for intellectual property violations

### Class Action Waiver
You agree to resolve disputes on an individual basis and not in a class or consolidated action.

## General Provisions

### Entire Agreement
These Terms constitute the entire agreement between you and Newsletter Machine.

### Severability
If any provision is unenforceable, the remaining provisions continue in full force.

### Waiver
Our failure to enforce any right is not a waiver of that right.

### Assignment
You cannot assign these Terms without our consent. We can assign these Terms to an affiliate or acquirer.

### Contact
For questions about these Terms:
- **Email**: legal@newsmachine.example.com
- **Address**: [Your Business Address]

---

**By using Newsletter Machine, you agree to these Terms of Service.**
    `,
  });
});

// Cookie Policy
router.get('/cookies', (req, res) => {
  res.json({
    title: 'Cookie Policy',
    lastUpdated: '2026-01-20',
    content: `
# Cookie Policy

**Last Updated:** January 20, 2026

## What Are Cookies

Cookies are small text files stored on your device when you visit a website. They help the website remember your preferences and improve your experience.

## How We Use Cookies

Newsletter Machine uses minimal cookies and local storage for essential functionality:

### Essential Cookies (Required)
- **Authentication Token**: JWT token stored in localStorage for keeping you logged in
- **Theme Preference**: Light/dark mode preference stored in localStorage

### What We DON'T Use
- ❌ Third-party tracking cookies
- ❌ Advertising cookies
- ❌ Analytics cookies (unless you opt-in)
- ❌ Social media cookies

## Managing Cookies

### Browser Settings
You can control cookies through your browser settings:
- **Chrome**: Settings > Privacy and Security > Cookies
- **Firefox**: Options > Privacy & Security > Cookies
- **Safari**: Preferences > Privacy > Cookies
- **Edge**: Settings > Cookies and Site Permissions

### Impact of Disabling Cookies
If you disable cookies:
- You won't be able to log in or stay logged in
- Your theme preference won't be saved
- The service may not function properly

## Local Storage

We use browser localStorage for:
- **Authentication**: Storing your JWT token
- **Preferences**: Theme preference (light/dark mode)
- **Onboarding**: Tracking if you've completed setup

Local storage is similar to cookies but has larger capacity and doesn't expire automatically.

## Third-Party Services

When you connect external sources (Reddit, YouTube), those services may set their own cookies. We don't control these cookies.

## Changes to This Policy

We may update this Cookie Policy. Changes will be posted on this page with an updated date.

## Contact Us

Questions about our cookie usage? Contact us at privacy@newsmachine.example.com.

---

**By continuing to use Newsletter Machine, you accept our use of cookies as described in this policy.**
    `,
  });
});

export default router;
