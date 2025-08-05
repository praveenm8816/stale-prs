Here’s a clean, well-structured documentation outline suitable for a presentation or README explaining your GitHub Action and Python script for auto-closing stale PRs and reporting via Microsoft Teams:

📄 Organization PR Stale Report and Auto-Close Automation
🧩 Overview
This setup automates:

Scanning all open PRs in the GitHub organization.

Identifying stale PRs (open for more than DAYS_STALE days).

Auto-closing PRs if older than DAYS_CLOSE days.

Sending reports to Microsoft Teams with PR details and mentions.

🔁 Workflow Summary
📅 Triggers
This GitHub Action runs:

Twice daily via cron:

13:30 UTC (8:30 AM EST / 9:30 AM EDT)

22:00 UTC (5:00 PM EST / 6:00 PM EDT)

Manually using the workflow_dispatch trigger.

⚙️ Workflow File (.github/workflows/stale-prs.yml)
yaml
Copy
Edit
name: Organization PR Stale Report and Auto Close

on:
  schedule:
    - cron: '30 13 * * *'
    - cron: '0 22 * * *'
  workflow_dispatch:

jobs:
  scan-org-prs:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install requests PyGithub tabulate

      - name: Scan, close, and report PRs
        env:
          GITHUB_TOKEN: ${{ secrets.ORG_PAT }}
          TEAMS_WEBHOOK_URL: ${{ secrets.TEAMS_WEBHOOK_URL }}
          ORG_NAME: your-org-name
          DAYS_STALE: 2
          DAYS_CLOSE: 7
        run: |
          python3 .github/stale_prs.py
🐍 Python Script Summary (.github/stale_prs.py)
🔑 Environment Variables
GITHUB_TOKEN: Personal Access Token (from secrets)

ORG_NAME: GitHub organization name

DAYS_STALE: Days after which PRs are considered stale (default: 2)

DAYS_CLOSE: Days after which stale PRs are auto-closed (default: 7)

TEAMS_WEBHOOK_URL: Microsoft Teams incoming webhook URL

🔍 Script Behavior
1. Scan Repositories
Iterates over all repositories in the organization.

For each open PR:

Calculates age in days.

Determines whether it is stale or should be auto-closed.

2. Stale PR Report
If PR is older than DAYS_STALE:

Adds PR details (repo, number, title, author, link) to a report.

Identifies committers to mention (excluding bots like cibuilder, dependabot).

Includes admin (@praveenm8816) in all mention lists.

3. Auto-Close PRs
If PR is older than DAYS_CLOSE:

Adds a comment to the PR mentioning responsible users.

Closes the PR via API.

Sends a notification to Teams with PR summary and closure reason.

4. Teams Notification
Sends a card-style report to Teams:

For individual PR closures

For the full daily stale PR report (in markdown table format)

📬 Example Teams Message
Title: Stale Pull Requests Report

Fields:

Repo name

PR number + title

Created date

Mentions of relevant users (@author)

Report sent as Markdown table using tabulate

🧪 Secrets Required
Secret Name	Description
ORG_PAT	GitHub Personal Access Token (with repo & read:org scopes)
TEAMS_WEBHOOK_URL	Webhook URL for Microsoft Teams channel

✅ Setup Checklist
🔐 Generate a classic GitHub PAT with repo, read:org

🔐 Store it as a secret named ORG_PAT

🔗 Create a Teams webhook and store it as TEAMS_WEBHOOK_URL

📝 Set ORG_NAME in the workflow or pass as secret/environment variable

✅ Confirm the script runs and Teams notifications appear correctly

📈 Output Example
Console Output:

yaml
Copy
Edit
| Repo      | #   | Title                    | Author   | Created   | Link       |
|-----------|-----|--------------------------|----------|-----------|------------|
| example-repo | 12  | Fix login issue         | johndoe  | 2025-08-01| https://...|
Total closed PRs: 3
Teams Notification:

PR #12 in example-repo has been closed after being open for more than 7 days.
Notified: @johndoe @praveenm8816

📌 Notes
Bots like dependabot are handled specially — original commit authors are identified and notified.

If no commits are made by real users, the admin is always included.

Script gracefully handles API errors per repository.

Let me know if you'd like this in PowerPoint, Markdown, or PDF format — I can generate one for you.
