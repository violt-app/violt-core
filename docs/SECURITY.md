# 🔐 Violt Security Policy

At **Violt**, security is not just a feature—it is a fundamental pillar of our commitment to user **privacy, autonomy, and trust**. As a hybrid open-source and AI-powered smart home platform, we prioritize safeguarding our users’ environments while maintaining the transparency and collaboration that define our community.

---

## 🚨 Reporting a Vulnerability

If you've discovered a security vulnerability in **Violt Core** or **Violt AI**, we urge you to **responsibly disclose it** by reporting through GitHub’s [Security Advisory process](https://docs.github.com/en/code-security/security-advisories).

> **⚠ DO NOT open public issues for security vulnerabilities.**

Please include:
- A clear, reproducible description of the issue
- Potential impact and affected components
- (Optional) CVSS v3.1 vector score

**Response Commitment:**  
We aim to respond within **7 business days** and provide status updates throughout the resolution process. Please allow us **up to 90 days** for coordinated disclosure and patching before going public.

If you wish to write or publish about a Violt-related vulnerability, please contact us first to ensure accurate and responsible communication.

---

## 🚫 What Doesn’t Qualify

To maintain focus and integrity, we do not accept reports involving:
- Automated scanner reports with no contextual validation
- Theoretical issues lacking real-world exploit paths
- Vulnerabilities introduced by third-party libraries (report to their maintainers)
- Social engineering or phishing
- Attacks requiring full access to the Violt host or local network
- Exploits that require malicious add-ons/integrations not officially supported
- Attacks relying on already-compromised environments
- Privilege escalation for logged-in users (Violt Core assumes full access for trusted local users)

---

## 🛠 Supported Versions

We accept reports for:
- The latest stable version of **Violt Core**
- Beta or development versions of **Violt AI** if publicly released

We **do not** accept issues related to forks or custom builds outside official distributions.

---

## 🧮 Scoring Vulnerabilities

We use **CVSS v3.1** to assess severity. If you’re able to, please provide a vector string (e.g., `AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H`).  
Not sure how? No problem—we’ll handle scoring internally.

---

## 🔏 CVE & Public Disclosure

We request **CVE identifiers** for valid vulnerabilities that meet the following:
- Affect core Violt components (not external libraries)
- Are not already publicly disclosed or known to the team
- Have a severity of **Medium** or higher

All resolved vulnerabilities will be documented transparently via [GitHub Security Advisories](https://github.com/violt-core).

---

## 🎖 Bounties & Recognition

As an open-source-first project, Violt currently does **not offer monetary bounties**. However, we deeply value our community’s contribution.  
All verified researchers will be **publicly credited** (with consent) in our advisory and release notes.

---

## 📚 Historical Security Advisories

You can view all past and active security disclosures via our [Security Advisory Log](https://github.com/violt-core/security-advisories).

---

## 🔐 Violt’s Security Foundations

- **Local-first design**: No forced cloud dependence for core automations.
- **End-to-end encryption** of user data.
- **Zero Trust Model** for cloud communication between Violt Core and Violt AI.
- **OAuth2-secured APIs** and session-based permissions for multi-user setups.
- **AI behavior sandboxing** to prevent unauthorized command execution.
- **Continuous community-led auditing** through our open-source GitHub presence.

---

For any questions or responsible disclosure concerns, please contact the core team directly at:  
📧 **security@violt.app**
