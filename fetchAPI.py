import requests
import csv
import time
import re
import base64
import ast
from datetime import datetime

# Token and headers for GitHub API
token = 'Your_token'
headers = {'Authorization': f'token {token}'}

# Parameters for GitHub API 
owner = 'microsoft'
repo = 'vscode'

branches = [('main', 1000), ('TylerLeonhardt/fix-arrowkeys-quickpick-a11y', 600), ('aamunger/outputInputFocus', 600), 
            ('aeschli/serverBackgroundDownload', 600), ('aeschli/prior-peafowl', 600), ('alexr00/commentEditorLanguage', 600)]

# Open the CSV file for writing
with open('commits.csv', 'w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(['SHA', 'committer', 'message', 'parents', 'URL', 'verification_status', 'stats', 'files', 'author_name','date', 'author_login', 'author_repos_url', 'author_orgs_url', 'merge', 'branch'])

    # Fetch commits from GitHub API
    for branch, commit_limit in branches:
        commit_count = 0
        page = 1
        while True:
            response = requests.get(f'https://api.github.com/repos/{owner}/{repo}/commits?sha={branch}&page={page}&per_page=100', headers=headers)
            commits = response.json()

            # If this page is empty, we've fetched all commits
            if not commits:
                break

            # Write commit data to CSV
            for commit in commits:
                commit_sha = commit['sha']
                commit_data = commit['commit']
                author = commit.get('author', {})

                # Fetch each individual commit's data
                commit_response = requests.get(f'https://api.github.com/repos/{owner}/{repo}/commits/{commit_sha}', headers=headers)
                commit_info = commit_response.json()
                print(commit_info)
                is_merge = len(commit['parents']) > 1

                author_login = ''
                author_repos_url = ''
                author_orgs_url = ''
                
                if author:
                    author_login = author.get('login', '')
                    author_repos_url = author.get('repos_url', '')
                    author_orgs_url = author.get('organizations_url', '')

                writer.writerow([
                    commit_sha,
                    commit_data['committer']['name'],
                    commit_data['message'].replace('\n', ' '),  # Replace linebreaks with a space
                    ','.join([parent['sha'] for parent in commit['parents']]),
                    commit['url'],
                    commit_data['verification']['verified'],
                    commit_info.get('stats', {}),
                    [file['filename'] for file in commit_info.get('files', [])],
                    commit_data['author']['name'],
                    commit_data['author']['date'],
                    author_login,
                    author_repos_url,
                    author_orgs_url,
                    is_merge,
                    branch
                ])

                # Increase commit count
                commit_count += 1
                if commit_count >= commit_limit:
                    break

                # Sleep to avoid rate limits
                time.sleep(0.5)
            
            # Stop fetching if we have reached the limit
            if commit_count >= commit_limit:
                break

            page += 1


# # Open the CSV file for writing
with open('issues_events.csv', 'w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(['issue', 'event', 'commit_id', 'event_creator', 'created_at', 'state', 'closed_at'])

    # Initialize counters for closed and open issues
    closed_counter = 0
    open_counter = 0

    # Fetch closed issues from GitHub API
    page = 1
    while closed_counter < 20:
        response = requests.get(f'https://api.github.com/repos/{owner}/{repo}/issues?state=closed&page={page}&per_page=30', headers=headers)
        issues = response.json()

        for issue in issues:
            issue_number = issue['number']
            closed_at = issue['closed_at']
            created_at = issue['created_at']
            state = issue["state"]
            closed_counter += 1

            events_response = requests.get(f'https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/events', headers=headers)
            events = events_response.json()

            for event in events:
                commit_id = event['commit_id'] if 'commit_id' in event else ''
                event_creator = event['actor']['login'] if 'actor' in event and event['actor'] is not None else ''
                writer.writerow([issue_number, event['event'], commit_id, event_creator, created_at, state, closed_at])

            time.sleep(0.5)

            if closed_counter >= 20:
                break

        page += 1

    # Fetch open issues from GitHub API
    page = 1
    while open_counter < 20:
        response = requests.get(f'https://api.github.com/repos/{owner}/{repo}/issues?state=open&page={page}&per_page=30', headers=headers)
        issues = response.json()

        for issue in issues:
            issue_number = issue['number']
            creation_time = issue['created_at']
            state = issue["state"]
            open_counter += 1

            events_response = requests.get(f'https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/events', headers=headers)
            events = events_response.json()

            for event in events:
                commit_id = event['commit_id'] if 'commit_id' in event else ''
                event_creator = event['actor']['login'] if 'actor' in event and event['actor'] is not None else ''
                writer.writerow([issue_number, event['event'], commit_id, event_creator, creation_time, state, ''])

            time.sleep(0.5)

            if open_counter >= 20:
                break

        page += 1




# Open the CSV file for writing
with open('pull_requests.csv', 'w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(['pr_id', 'title', 'state', 'user', 'created_at', 'merged_at', 'merge_commit_sha'])

    # Initialize pull request counter
    pr_counter = 0

    # Start page number at 1
    page = 1

    # Loop until we have the desired number of pull requests
    while pr_counter < 1000:
        response = requests.get(f'https://api.github.com/repos/{owner}/{repo}/pulls?state=all&page={page}&per_page=100', headers=headers)
        pull_requests = response.json()
        
        # If there are no pull requests on this page, we're done
        if not pull_requests:
            break

        # Write pull request data to CSV
        for pr in pull_requests:
            pr_id = pr['number']
            pr_title = pr['title']
            pr_state = pr['state']
            pr_author = pr['user']['login']
            pr_created_at = pr['created_at']
            pr_merged_at = pr['merged_at']
            pr_merge_commit_sha = pr['merge_commit_sha'] if 'merge_commit_sha' in pr else ''

            writer.writerow([pr_id, pr_title, pr_state, pr_author, pr_created_at, pr_merged_at, pr_merge_commit_sha])

            # Increment pull request counter
            pr_counter += 1

            # If we have the desired number of pull requests, we're done
            if pr_counter >= 1000:
                break

        # Increment the page number for the next iteration
        page += 1

        # Sleep to avoid rate limits
        time.sleep(0.5)

with open('branches.csv', 'w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(['name'])
    branches_url = f"https://api.github.com/repos/{owner}/{repo}/branches"
    counter = 0

    while counter < 10:
        response = requests.get(branches_url, headers=headers)
        branches_data = response.json()
        print(branches_data[0])
        for branch in branches_data:
            name = branch['name']

            writer.writerow([name])

            counter += 1

            if counter >= 10:
                break


# def get_paginated_results(url, max_results=1000):
#     page = 1
#     results = []
#     while True:
#         response = requests.get(url + f"&page={page}", headers=headers)
#         response.raise_for_status()
#         data = response.json()
#         results.extend(data)
#         if len(results) >= max_results or len(data) < 30:
#             break
#         page += 1
#     return results[:max_results]


# def write_csv(filename, data, headers):
#     with open(filename, 'w', newline='', encoding='utf-8') as f:
#         writer = csv.DictWriter(f, fieldnames=headers)
#         writer.writeheader()
#         for d in data:
#             row = {}
#             for h in headers:
#                 row[h] = d[h] if h in d else None
#             writer.writerow(row)


# def get_all_branches(owner, repo):
#     branches_url = f"https://api.github.com/repos/{owner}/{repo}/branches"
#     branches_data = get_paginated_results(branches_url)
#     print("fetch branches")
#     branches = []
#     for branch in branches_data:
#         branches.append({
#             'name': branch['name'],
#             'commit': branch['commit']['sha'],
#         })
    
#     return branches

# branches = get_all_branches(owner, repo)
# write_csv('branches.csv', branches, ['name', 'commit'])




