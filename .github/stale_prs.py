import os
import datetime
import requests
from github import Github
from tabulate import tabulate

# === Settings ===
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
ORG_NAME = os.environ["ORG_NAME"]
DAYS_STALE = int(os.environ.get("DAYS_STALE", 2))
DAYS_CLOSE = int(os.environ.get("DAYS_CLOSE", 7))
TEAMS_WEBHOOK_URL = os.environ.get("TEAMS_WEBHOOK_URL")
ADMIN_GITHUB_USERNAME = "praveenm8816"
ADMIN_MENTION = f"@{ADMIN_GITHUB_USERNAME}"  # Your GitHub username for notifications

g = Github(GITHUB_TOKEN)
org = g.get_organization(ORG_NAME)
now = datetime.datetime.now(datetime.timezone.utc)

stale_report = []
closed_count = 0

def mention_list(users):
    # Remove None and duplicates, and prepend @ for mentions
    return " ".join(f"@{u}" for u in sorted({u for u in users if u}))

for repo in org.get_repos(type="all"):
    try:
        for pr in repo.get_pulls(state="open"):
            created_at = pr.created_at.replace(tzinfo=None)
            age_days = (now - created_at).days
            pr_url = pr.html_url
            pr_author = pr.user.login if pr.user else None

            # Identify original committers if PR is by a bot
            committers = set()
            if pr_author and (pr.user.type == "Bot" or pr_author.lower() in ["cibuilder", "dependabot[bot]"]):
                for commit in pr.get_commits():
                    author = commit.author
                    if author and author.login and author.login.lower() not in ["cibuilder", "dependabot[bot]"]:
                        committers.add(author.login)
                # Always include admin in notifications
                committers.add(ADMIN_GITHUB_USERNAME)
            else:
                # Just the PR author and admin
                committers = {pr_author, ADMIN_GITHUB_USERNAME}

            # Build mention string for comments
            mention_str = mention_list(committers)

            # Add to report if stale
            if age_days >= DAYS_STALE:
                stale_report.append([
                    repo.name, pr.number, pr.title, pr_author, pr.created_at.strftime("%Y-%m-%d"), pr_url, mention_str
                ])

            # Close if > DAYS_CLOSE
            if age_days > DAYS_CLOSE:
                # Comment before closing
                comment_body = (
                    f"🔒 This PR has been open for more than {DAYS_CLOSE} days and is being closed automatically.\n"
                    f"{mention_str}\n"
                    "Please reopen if you still need these changes."
                )
                pr.create_issue_comment(comment_body)
                # Close PR
                pr.edit(state="closed")
                closed_count += 1

                # Notify Teams about closure
                if TEAMS_WEBHOOK_URL:
                    payload = {
                        "@type": "MessageCard",
                        "@context": "http://schema.org/extensions",
                        "summary": "PR Closed Due to Staleness",
                        "themeColor": "FF0000",
                        "title": "Pull Request Closed Automatically",
                        "sections": [{
                            "activityTitle": f'PR <a href="{pr_url}">#{pr.number}</a> has been closed after being open for more than {DAYS_CLOSE} days.',
                            "activitySubtitle": f"Repo: {repo.name} | Author: {pr_author}",
                            "facts": [
                                {"name": "Title", "value": pr.title},
                                {"name": "Created At", "value": pr.created_at.strftime("%Y-%m-%d %H:%M:%S")},
                                {"name": "Notified", "value": mention_str}
                            ],
                            "markdown": True
                        }]
                    }
                    if TEAMS_WEBHOOK_URL:
                        requests.post(TEAMS_WEBHOOK_URL, json=payload)
                    else:
                        print("[TEST] Would send Teams PR close payload:")
                        print(payload)
    except Exception as e:
        print(f"Error processing repo {repo.name}: {e}")

# Build markdown table including mentions
table_md = tabulate(
    [row[:6] for row in stale_report],  # omit mention string in table
    headers=["Repo", "#", "Title", "Author", "Created", "Link"],
    tablefmt="github"
)

print(table_md)

# Full report to Teams, including admin mention and all original committers for each PR
if TEAMS_WEBHOOK_URL and stale_report:
    # Collect unique users to notify (from mention_str in each row)
    users_to_notify = set()
    for row in stale_report:
        mentions = row[6].split()
        for m in mentions:
            if m.startswith("@"):
                users_to_notify.add(m)
    mentions = " ".join(sorted(users_to_notify))
    text = (
        f"{mentions}\n\n"
        f"Here is the list of open PRs older than {DAYS_STALE} days in the organization:\n\n"
        f"<pre>{table_md}</pre>"
    )
    payload = {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "summary": "Organization Stale PRs Report",
        "themeColor": "0076D7",
        "title": "Stale Pull Requests Report",
        "text": text
    }
    if TEAMS_WEBHOOK_URL:
        requests.post(TEAMS_WEBHOOK_URL, json=payload)
    else:
        print("[TEST] Would send Teams stale PRs report payload:")
        print(payload)

print(f"Total closed PRs: {closed_count}")