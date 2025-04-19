#!/usr/bin/env python3
import os
import re
import json
import base64
from datetime import datetime
from github import Github
import pandas as pd
import matplotlib.pyplot as plt
import io

# Initialize GitHub API client
token = os.environ.get("GITHUB_TOKEN")
g = Github(token)
username = os.environ.get("GITHUB_REPOSITORY").split("/")[0]
user = g.get_user(username)

# Dictionary to map file extensions to languages
extension_map = {
    '.py': 'Python',
    '.js': 'JavaScript',
    '.ts': 'TypeScript',
    '.html': 'HTML',
    '.css': 'CSS',
    '.scss': 'SCSS',
    '.java': 'Java',
    '.c': 'C',
    '.cpp': 'C++',
    '.go': 'Go',
    '.rb': 'Ruby',
    '.php': 'PHP',
    '.swift': 'Swift',
    '.kt': 'Kotlin',
    '.rs': 'Rust',
    '.sh': 'Shell',
    '.sql': 'SQL',
    '.md': 'Markdown',
    '.json': 'JSON',
    '.yml': 'YAML',
    '.yaml': 'YAML',
    '.xml': 'XML',
    '.dart': 'Dart',
    '.jsx': 'React',
    '.tsx': 'React',
    '.vue': 'Vue',
    '.r': 'R',
}

# Common frameworks and libraries to look for in package files
frameworks = {
    'React': ['react', 'react-dom', 'next.js', 'create-react-app'],
    'Angular': ['@angular/core'],
    'Vue': ['vue', 'nuxt'],
    'Django': ['django'],
    'Flask': ['flask'],
    'Express': ['express'],
    'Spring': ['spring-boot', 'spring-core'],
    'Laravel': ['laravel'],
    'TensorFlow': ['tensorflow'],
    'PyTorch': ['torch'],
    'Node.js': ['node', 'npm', 'package.json'],
    'Docker': ['Dockerfile', 'docker-compose'],
    'Kubernetes': ['kubernetes', 'k8s'],
    'GraphQL': ['graphql'],
    'AWS': ['aws-sdk', 'boto3'],
    'Firebase': ['firebase'],
    'MongoDB': ['mongodb', 'mongoose'],
    'PostgreSQL': ['pg', 'postgresql'],
    'MySQL': ['mysql'],
    'Redis': ['redis'],
}

# Initialize counters
language_stats = {}
framework_stats = {}
contributions = {'commits': 0, 'issues': 0, 'pull_requests': 0}

# Process repositories
for repo in user.get_repos():
    if repo.fork:
        continue  # Skip forked repositories

    # Count commits
    try:
        commits = repo.get_commits(author=user)
        for _ in commits:
            contributions['commits'] += 1
    except Exception:
        pass  # Skip if there's an issue with commits

    # Process files to identify languages and frameworks
    try:
        contents = repo.get_contents("")
        while contents:
            file_content = contents.pop(0)
            if file_content.type == "dir":
                contents.extend(repo.get_contents(file_content.path))
            else:
                # Extract extension and update language stats
                _, ext = os.path.splitext(file_content.name.lower())
                if ext in extension_map:
                    lang = extension_map[ext]
                    language_stats[lang] = language_stats.get(lang, 0) + 1
                
                # Look for framework indicators
                if file_content.name in ['package.json', 'requirements.txt', 'build.gradle', 'pom.xml', 'Gemfile']:
                    try:
                        content = repo.get_contents(file_content.path).decoded_content.decode('utf-8')
                        for framework, indicators in frameworks.items():
                            if any(indicator in content.lower() for indicator in indicators):
                                framework_stats[framework] = framework_stats.get(framework, 0) + 1
                    except:
                        pass
                        
                # Direct framework indicators from file names
                for framework, indicators in frameworks.items():
                    if any(indicator in file_content.name.lower() for indicator in indicators):
                        framework_stats[framework] = framework_stats.get(framework, 0) + 1
    except Exception as e:
        print(f"Error processing repo {repo.name}: {e}")

# Count issues and PRs
for issue in g.search_issues(f"author:{username} type:issue"):
    contributions['issues'] += 1

for pr in g.search_issues(f"author:{username} type:pr"):
    contributions['pull_requests'] += 1

# Generate charts
def create_chart(data, title, filename):
    plt.figure(figsize=(10, 6))
    df = pd.DataFrame(list(data.items()), columns=['Name', 'Count'])
    df = df.sort_values('Count', ascending=False).head(10)  # Top 10
    
    plt.bar(df['Name'], df['Count'], color='skyblue')
    plt.title(title)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    # Save to buffer
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    
    # Upload to repo as an asset
    repo = g.get_repo(f"{username}/{username}")
    contents = buffer.getvalue()
    try:
        repo.create_file(f"images/{filename}", f"Update {filename}", contents, branch="main")
    except:
        repo.update_file(f"images/{filename}", f"Update {filename}", 
                          contents, 
                          repo.get_contents(f"images/{filename}", ref="main").sha, 
                          branch="main")
    plt.close()
    return f"images/{filename}"

# Create directories if needed
repo = g.get_repo(f"{username}/{username}")
try:
    repo.get_contents("images", ref="main")
except:
    repo.create_file("images/.gitkeep", "Create images directory", "", branch="main")

# Generate and save charts
lang_chart = create_chart(language_stats, "Most Used Languages", "languages.png")
framework_chart = create_chart(framework_stats, "Frameworks & Technologies", "frameworks.png")

# Update README.md
readme_repo = g.get_repo(f"{username}/{username}")
readme_content = readme_repo.get_contents("README.md", ref="main")
current_readme = base64.b64decode(readme_content.content).decode('utf-8')

# Create new stats section
current_date = datetime.now().strftime("%Y-%m-%d")
stats_section = f"""
## 🛠️ My Tech Stack

### Languages
![Languages](https://github.com/{username}/{username}/raw/main/{lang_chart})

### Frameworks & Technologies
![Frameworks](https://github.com/{username}/{username}/raw/main/{framework_chart})

## 📊 Contribution Stats
- 🔥 **{contributions['commits']}** commits
- 🐛 **{contributions['issues']}** issues reported
- 🔧 **{contributions['pull_requests']}** pull requests submitted

<sub>Last updated: {current_date}</sub>
"""

# Replace existing stats section or append
stats_pattern = re.compile(r'## 🛠️ My Tech Stack.*?<sub>Last updated:.*?</sub>', re.DOTALL)
if re.search(stats_pattern, current_readme):
    new_readme = re.sub(stats_pattern, stats_section, current_readme)
else:
    new_readme = current_readme + "\n" + stats_section

# Update README
if new_readme != current_readme:
    readme_repo.update_file(
        "README.md",
        "Update tech stack statistics",
        new_readme,
        readme_content.sha,
        branch="main"
    )

print("Successfully updated tech stack statistics!")