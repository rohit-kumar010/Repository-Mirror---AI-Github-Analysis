from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
from datetime import datetime
import re

app = Flask(__name__)
CORS(app)

GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '')

def fetch_github_data(repo_url):
    """Extract owner and repo name from GitHub URL and fetch repository data"""
    # Parse GitHub URL
    pattern = r'github\.com/([^/]+)/([^/]+)'
    match = re.search(pattern, repo_url)
    
    if not match:
        return None
    
    owner, repo = match.groups()
    repo = repo.replace('.git', '')
    
    headers = {'Authorization': f'token {GITHUB_TOKEN}'} if GITHUB_TOKEN else {}
    base_url = f'https://api.github.com/repos/{owner}/{repo}'
    
    try:
        # Fetch main repo data
        repo_response = requests.get(base_url, headers=headers)
        if repo_response.status_code != 200:
            return None
        repo_data = repo_response.json()
        
        # Fetch commits
        commits_response = requests.get(f'{base_url}/commits', headers=headers)
        commits = commits_response.json() if commits_response.status_code == 200 else []
        
        # Fetch languages
        languages_response = requests.get(f'{base_url}/languages', headers=headers)
        languages = languages_response.json() if languages_response.status_code == 200 else {}
        
        # Fetch contents (to check README and structure)
        contents_response = requests.get(f'{base_url}/contents', headers=headers)
        contents = contents_response.json() if contents_response.status_code == 200 else []
        
        # Fetch branches
        branches_response = requests.get(f'{base_url}/branches', headers=headers)
        branches = branches_response.json() if branches_response.status_code == 200 else []
        
        return {
            'repo_data': repo_data,
            'commits': commits[:100],  # Last 100 commits
            'languages': languages,
            'contents': contents,
            'branches': branches
        }
    except Exception as e:
        print(f"Error fetching GitHub data: {e}")
        return None

def analyze_repository(github_data):
    """Analyze repository and generate score with detailed metrics"""
    repo_data = github_data['repo_data']
    commits = github_data['commits']
    languages = github_data['languages']
    contents = github_data['contents']
    branches = github_data['branches']
    
    # Initialize scoring components
    scores = {}
    
    # 1. Documentation Score (0-20 points)
    doc_score = 0
    has_readme = any(file.get('name', '').lower() == 'readme.md' for file in contents)
    readme_size = next((file.get('size', 0) for file in contents if file.get('name', '').lower() == 'readme.md'), 0)
    
    if has_readme:
        doc_score += 10
        if readme_size > 500:
            doc_score += 5
        if readme_size > 1500:
            doc_score += 5
    
    has_license = any(file.get('name', '').lower().startswith('license') for file in contents)
    if has_license:
        doc_score += 3
    
    has_contributing = any(file.get('name', '').lower() in ['contributing.md', 'contributing.rst'] for file in contents)
    if has_contributing:
        doc_score += 2
    
    scores['documentation'] = min(doc_score, 20)
    
    # 2. Project Structure Score (0-15 points)
    structure_score = 0
    file_count = len(contents)
    
    if file_count >= 5:
        structure_score += 5
    elif file_count >= 3:
        structure_score += 3
    
    # Check for common good structure patterns
    common_folders = ['src', 'tests', 'docs', 'lib', 'config', 'public', 'assets']
    folder_names = [file.get('name', '').lower() for file in contents if file.get('type') == 'dir']
    structure_matches = sum(1 for folder in common_folders if folder in folder_names)
    structure_score += min(structure_matches * 2, 10)
    
    scores['structure'] = min(structure_score, 15)
    
    # 3. Code Quality Score (0-20 points)
    quality_score = 0
    
    # Language diversity
    if len(languages) > 0:
        quality_score += 5
    if len(languages) > 2:
        quality_score += 3
    
    # Check for test files
    has_tests = any('test' in file.get('name', '').lower() or 'spec' in file.get('name', '').lower() for file in contents)
    if has_tests:
        quality_score += 7
    
    # Check for config files (eslint, prettier, etc.)
    config_files = ['.eslintrc', '.prettierrc', 'tsconfig.json', 'pytest.ini', 'setup.py', 'requirements.txt', 'package.json']
    has_config = any(any(cf in file.get('name', '') for cf in config_files) for file in contents)
    if has_config:
        quality_score += 5
    
    scores['quality'] = min(quality_score, 20)
    
    # 4. Commit History Score (0-20 points)
    commit_score = 0
    commit_count = len(commits)
    
    if commit_count >= 10:
        commit_score += 10
    elif commit_count >= 5:
        commit_score += 7
    elif commit_count >= 3:
        commit_score += 5
    elif commit_count >= 1:
        commit_score += 3
    
    # Check commit consistency
    if commit_count > 1:
        commit_dates = []
        for commit in commits[:30]:
            try:
                date_str = commit['commit']['author']['date']
                commit_dates.append(datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%SZ'))
            except:
                pass
        
        if len(commit_dates) > 1:
            # Check if commits span multiple days
            date_range = (max(commit_dates) - min(commit_dates)).days
            if date_range > 30:
                commit_score += 5
            elif date_range > 7:
                commit_score += 3
            elif date_range > 1:
                commit_score += 2
    
    # Check commit message quality
    good_messages = sum(1 for c in commits[:20] if len(c['commit']['message']) > 20 and not c['commit']['message'].startswith('Update '))
    if good_messages > 10:
        commit_score += 5
    elif good_messages > 5:
        commit_score += 3
    
    scores['commits'] = min(commit_score, 20)
    
    # 5. Version Control Best Practices (0-15 points)
    vc_score = 0
    
    # Multiple branches
    branch_count = len(branches)
    if branch_count > 3:
        vc_score += 7
    elif branch_count > 1:
        vc_score += 5
    
    # Check for .gitignore
    has_gitignore = any(file.get('name', '') == '.gitignore' for file in contents)
    if has_gitignore:
        vc_score += 5
    
    # Check if repo has issues/PRs enabled
    if not repo_data.get('has_issues', False):
        vc_score -= 2
    else:
        vc_score += 3
    
    scores['version_control'] = max(min(vc_score, 15), 0)
    
    # 6. Activity & Maintenance Score (0-10 points)
    activity_score = 0
    
    # Recent activity
    if repo_data.get('updated_at'):
        try:
            last_update = datetime.strptime(repo_data['updated_at'], '%Y-%m-%dT%H:%M:%SZ')
            days_since_update = (datetime.utcnow() - last_update).days
            
            if days_since_update < 7:
                activity_score += 5
            elif days_since_update < 30:
                activity_score += 4
            elif days_since_update < 90:
                activity_score += 3
            elif days_since_update < 180:
                activity_score += 2
            elif days_since_update < 365:
                activity_score += 1
        except:
            pass
    
    # Stars and forks (indicates community interest)
    stars = repo_data.get('stargazers_count', 0)
    if stars > 10:
        activity_score += 3
    elif stars > 5:
        activity_score += 2
    elif stars > 0:
        activity_score += 1
    
    forks = repo_data.get('forks_count', 0)
    if forks > 5:
        activity_score += 2
    elif forks > 0:
        activity_score += 1
    
    scores['activity'] = min(activity_score, 10)
    
    # Calculate total score
    total_score = sum(scores.values())
    
    return {
        'total_score': total_score,
        'breakdown': scores,
        'metrics': {
            'has_readme': has_readme,
            'readme_size': readme_size,
            'has_tests': has_tests,
            'commit_count': commit_count,
            'branch_count': branch_count,
            'languages': list(languages.keys()),
            'file_count': file_count,
            'stars': repo_data.get('stargazers_count', 0),
            'forks': repo_data.get('forks_count', 0),
            'has_license': has_license,
            'has_gitignore': has_gitignore
        }
    }

def generate_summary_and_roadmap(analysis_result):
    """Generate human-readable summary and personalized roadmap"""
    score = analysis_result['total_score']
    metrics = analysis_result['metrics']
    breakdown = analysis_result['breakdown']
    
    # Generate summary - more natural and descriptive
    summary_parts = []
    
    # Documentation assessment
    if breakdown['documentation'] >= 15:
        summary_parts.append("The repository has strong documentation")
    elif breakdown['documentation'] >= 10:
        summary_parts.append("Documentation is present but could be more comprehensive")
    else:
        summary_parts.append("Documentation is lacking and needs significant improvement")
    
    # Code quality and structure
    if breakdown['quality'] >= 15 and breakdown['structure'] >= 12:
        summary_parts.append("code structure is clean and well-organized")
    elif breakdown['quality'] >= 10 or breakdown['structure'] >= 8:
        summary_parts.append("code organization is acceptable but has room for improvement")
    else:
        summary_parts.append("code structure and organization need significant work")
    
    # Testing
    if metrics['has_tests']:
        summary_parts.append("Tests are included which is great for maintainability")
    else:
        summary_parts.append("tests are missing and should be added")
    
    # Commit history
    if breakdown['commits'] >= 15:
        summary_parts.append("The commit history shows consistent development practices")
    elif breakdown['commits'] >= 10:
        summary_parts.append("Commit activity is moderate")
    else:
        summary_parts.append("More frequent and meaningful commits are needed")
    
    # Version control practices
    if breakdown['version_control'] >= 10:
        summary_parts.append("Good use of Git best practices")
    else:
        summary_parts.append("Version control practices need improvement")
    
    # Combine into natural sentences
    if len(summary_parts) >= 3:
        summary = f"{summary_parts[0]}, {summary_parts[1]}, and {summary_parts[2]}. " + ". ".join(summary_parts[3:]) + "."
    else:
        summary = ". ".join(summary_parts) + "."
    
    summary = summary.replace(".. ", ". ").replace("..", ".")
    
    # Generate personalized roadmap - constructive and specific
    roadmap = []
    
    # Critical items first (documentation)
    if not metrics['has_readme']:
        roadmap.append("⚠️ CRITICAL ISSUE: Your repository is missing a README.md file. Without it, no one knows what your project does or how to use it. Create README.md immediately and include: project title, description, installation steps (prerequisites, dependencies, setup commands), usage examples with code snippets, and screenshots/demo links. This is non-negotiable for any serious project.")
    elif metrics['readme_size'] < 500:
        roadmap.append("❌ WEAK DOCUMENTATION: Your README.md exists but is too brief (under 500 characters). Recruiters will skip your project. Fix this by adding: detailed setup instructions, usage examples, API documentation if applicable, troubleshooting section, and contribution guidelines. A good README should be 1500+ characters.")
    elif metrics['readme_size'] < 1500:
        roadmap.append("⚡ GOOD START, NEEDS MORE: Your README has basic info but lacks depth. Add these missing sections: project badges (build status, license), detailed feature list, architecture diagram or flowchart, environment variables setup, deployment instructions, and FAQ section. Make it comprehensive.")
    
    # Testing (very important)
    if not metrics['has_tests']:
        roadmap.append("🚨 NO TESTS DETECTED: This is a major red flag for employers. Your code has zero automated tests, meaning you're not validating functionality. Fix this NOW: For JavaScript/TypeScript use Jest or Mocha, for Python use pytest or unittest, for Java use JUnit. Start with testing critical functions, then add integration tests. Aim for 60%+ coverage minimum.")
    else:
        if breakdown['quality'] < 15:
            roadmap.append("✅ TESTS EXIST, BUT EXPAND COVERAGE: You have some tests which is good, but coverage seems limited. Add: edge case testing (null values, empty inputs, boundary conditions), integration tests for API endpoints, end-to-end tests for critical user flows, and mock external dependencies properly.")
    
    # Project structure
    if breakdown['structure'] < 8:
        roadmap.append("❌ POOR PROJECT STRUCTURE: Your files are disorganized or dumped in root directory. This looks unprofessional. Restructure immediately: Create src/ or lib/ for source code, tests/ or __tests__/ for test files, docs/ for documentation, config/ for configuration files, and public/assets/ for static files. Follow your framework's conventions (e.g., React uses src/components/, Python uses package_name/ with __init__.py).")
    elif breakdown['structure'] < 12:
        roadmap.append("⚠️ STRUCTURE NEEDS IMPROVEMENT: Your folder organization is basic but not optimal. Improve by: grouping related files into modules/packages, separating business logic from UI components, creating a clear separation between utility functions and main code, and adding index files for cleaner imports.")
    
    # Code quality
    if breakdown['quality'] < 10:
        roadmap.append("🚨 CODE QUALITY TOOLS MISSING: You don't have linting or formatting setup. Code probably has inconsistent style. Fix this: Install ESLint + Prettier (JavaScript), Black + Pylint (Python), or RuboCop (Ruby). Add .eslintrc or .pylintrc config files. Set up pre-commit hooks using Husky (JS) or pre-commit (Python) to run checks automatically. This prevents messy code from being committed.")
        roadmap.append("❌ NO TYPE CHECKING: Your project lacks type safety which leads to runtime errors. Migrate to TypeScript if using JavaScript, add type hints to Python functions (use mypy for checking), or use PropTypes/Flow for React. Type checking catches bugs before runtime.")
    elif breakdown['quality'] < 15:
        roadmap.append("⚡ TIGHTEN CODE QUALITY: You have basic quality tools but they're not strict enough. Configure stricter linting rules (e.g., airbnb style guide for ESLint), enable error-on-warning in CI, add complexity checks (max function length, cyclomatic complexity), and enforce 100% type coverage.")
    
    # Git best practices
    if metrics['commit_count'] < 5:
        roadmap.append("❌ VERY FEW COMMITS: You have less than 5 commits. This either means you committed everything at once (bad practice) or barely worked on this. Show your development process by: committing after each logical change, writing descriptive commit messages using format 'type(scope): description' (e.g., 'feat(auth): add login validation'), and never commit large chunks of unrelated changes together.")
    elif metrics['commit_count'] < 15:
        roadmap.append("⚠️ LOW COMMIT FREQUENCY: Your commit count is below average. This suggests infrequent commits with too many changes bundled together. Best practice: commit every 30-60 minutes of work, use atomic commits (one logical change per commit), write messages that explain WHY not just WHAT (e.g., 'fix(api): handle null response to prevent crash' instead of 'fix bug'), and never use vague messages like 'Update', 'Fix', or 'Changes'.")
    else:
        if breakdown['commits'] < 15:
            roadmap.append("✅ GOOD COMMIT COUNT, IMPROVE MESSAGES: You commit regularly but your commit messages need work. Many are probably unclear or too generic. Follow conventional commits: 'feat:' for features, 'fix:' for bugs, 'docs:' for documentation, 'refactor:' for code improvements, 'test:' for tests, 'chore:' for maintenance. Add detailed descriptions in commit body for complex changes.")
    
    # Branching strategy
    if metrics['branch_count'] <= 1:
        roadmap.append("🚨 WORKING ONLY ON MAIN BRANCH: This is extremely poor practice. You're committing everything directly to main/master which is risky and unprofessional. Fix this immediately: Create a 'develop' branch for ongoing work using 'git checkout -b develop', for each new feature create a feature branch 'git checkout -b feature/feature-name', work on feature branch, then merge via Pull Request with code review, keep main branch protected and production-ready only.")
        roadmap.append("❌ NO PULL REQUEST WORKFLOW: Without branches, you can't use Pull Requests. This means no code review, no CI checks before merge, and no discussion on changes. Adopt GitHub Flow: create feature branch → push → open PR → review → merge. Even solo developers should use PRs for discipline and CI automation.")
    elif metrics['branch_count'] <= 3:
        roadmap.append("⚠️ LIMITED BRANCHING: You have a few branches but not using them effectively. Improve by: creating a new branch for EVERY feature/bugfix (don't reuse branches), using descriptive branch names like 'feature/user-authentication' or 'bugfix/fix-memory-leak', deleting branches after merging to keep repo clean, and using branch protection rules to prevent direct commits to main.")
    
    # Essential files
    if not metrics['has_license']:
        roadmap.append("⚠️ NO LICENSE FILE: Your code has no legal protection. Anyone can steal it, and many developers won't contribute to unlicensed projects. Add LICENSE file immediately: Use MIT for permissive open-source, Apache 2.0 for patent protection, GPL for copyleft, or choose at choosealicense.com. Copy the license text, replace [year] and [fullname], and commit it.")
    
    if not metrics['has_gitignore']:
        roadmap.append("❌ MISSING .gitignore: You're likely committing files you shouldn't (node_modules/, __pycache__/, .env, .DS_Store, build artifacts). This bloats your repo and exposes secrets. Create .gitignore NOW: For Node.js add 'node_modules/', '.env', 'dist/', for Python add '__pycache__/', '*.pyc', 'venv/', '.env', for Java add 'target/', '*.class'. Use gitignore.io to generate comprehensive templates.")
    
    # CI/CD and automation
    if score >= 50 and breakdown['quality'] >= 10:
        roadmap.append("⚡ ADD CI/CD PIPELINE: You're manually testing and deploying which is error-prone and slow. Set up GitHub Actions: Create .github/workflows/ci.yml, add jobs for 'npm test' or 'pytest', run linting, build the project, and fail PR if tests fail. This catches bugs before they reach main branch. Example: on every push, auto-run tests, lint, and type check.")
    
    if score >= 60:
        roadmap.append("🔧 AUTOMATE WITH PRE-COMMIT HOOKS: You're probably committing code that fails linting or tests. Stop this: Install Husky (for JS/TS) or pre-commit (for Python), configure hooks to run linters and formatters before commit, add 'npm run lint' and 'npm test' to pre-commit, reject commit if checks fail. This enforces quality before code even reaches Git.")
    
    if score >= 70:
        roadmap.append("🚀 SETUP CONTINUOUS DEPLOYMENT: You're manually deploying which wastes time and creates inconsistency. Automate it: Use GitHub Actions to deploy on successful merge to main, deploy to Vercel/Netlify (frontend), Heroku/Railway (backend), or AWS/Azure (production). Add staging environment for testing before production. Example workflow: push to develop → auto-deploy to staging, merge to main → auto-deploy to production.")
    
    # Code quality improvements
    if breakdown['quality'] < 18:
        roadmap.append("❌ CODE READABILITY ISSUES: Your code probably has poor naming, long functions, and little comments. Refactor immediately: Use descriptive variable names (getUserById not gud), keep functions under 30 lines (extract complex logic), add JSDoc/docstrings for all public functions explaining parameters and return values, remove commented-out code, and explain 'why' not 'what' in comments. Example: '// Retry 3 times because API rate limits' not '// Loop 3 times'.")
    
    if len(metrics['languages']) == 1 and metrics['file_count'] < 10:
        roadmap.append("⚠️ PROJECT CONFIGURATION MISSING: Your project lacks proper configuration files which makes it hard to run. Add: package.json with scripts and dependencies (Node.js), requirements.txt or pyproject.toml (Python), pom.xml or build.gradle (Java). Include setup instructions in README: how to install dependencies, how to run locally, how to build for production.")
    
    # Documentation beyond README
    if score >= 40 and metrics['readme_size'] > 500:
        roadmap.append("📚 ADD CODE DOCUMENTATION: Your README is decent but code itself lacks documentation. Fix by: adding docstrings to all functions and classes (Python), using JSDoc for JavaScript functions, documenting complex algorithms with inline comments, creating API.md file for backend endpoints with request/response examples, and adding architectural decision records (ADR) for major design choices.")
        roadmap.append("🤝 CREATE CONTRIBUTING.md: You want contributors but no guidelines exist. This confuses people. Create CONTRIBUTING.md with: how to set up dev environment, coding style guide, how to submit PR (fork, branch, commit, PR), how to run tests, how to report bugs, and code of conduct. This increases quality contributions.")
    
    # Version control improvements
    if breakdown['version_control'] < 10:
        roadmap.append("❌ ISSUES NOT ENABLED: You have no way to track bugs and features. Enable GitHub Issues immediately and: create issue templates for bugs and features (.github/ISSUE_TEMPLATE/), use labels (bug, enhancement, documentation), create milestones for version planning, reference issues in commits ('fixes #42'), and close issues via PRs automatically. This shows organized project management.")
        roadmap.append("⚠️ NOT USING PULL REQUESTS: You're merging code without review which lets bugs slip through. Start using PRs even when solo: create PR for every feature branch, write PR description explaining what and why, add PR template (.github/pull_request_template.md) with checklist (tests added, docs updated, no conflicts), request reviews from teammates, and require passing CI before merge. This creates accountability and documentation.")
    
    # Performance and optimization
    if score >= 70 and breakdown['quality'] >= 15:
        roadmap.append("⚡ OPTIMIZE PERFORMANCE: Your code works but may have performance issues. Profile and optimize: use Chrome DevTools or Lighthouse (web), cProfile or py-spy (Python), identify bottlenecks (N+1 queries, unnecessary re-renders, unoptimized loops), add caching for expensive operations, lazy load images and components, and measure improvements with benchmarks. Don't guess, measure.")
    
    # Community and visibility
    if metrics['stars'] == 0 and score >= 60:
        roadmap.append("📊 LOW VISIBILITY: Your project is good but no one knows about it (0 stars). Fix this: add shields.io badges to README (build status, license, version), write clear project description on GitHub, add 5-10 relevant topics/tags (react, api, machine-learning), create demo GIF or video, share on Reddit/Twitter/Dev.to, and optimize README as landing page to convert visitors to users/contributors.")
    
    # Advanced improvements for high-scoring repos
    if score >= 80:
        roadmap.append("📖 CREATE COMPREHENSIVE DOCS: Your project is advanced but documentation isn't complete. Build a docs site: use Docusaurus, VuePress, or MkDocs, include Getting Started guide, API reference with examples, architecture overview with diagrams, troubleshooting section, migration guides between versions, and deploy docs to GitHub Pages or Netlify. Great projects have great docs.")
        roadmap.append("🎯 ADD EXAMPLES AND DEMOS: You have good code but users need to see it in action. Create: 'examples/' folder with working sample projects, live demo deployed on free hosting, video walkthrough on YouTube, blog post explaining architecture and decisions, and interactive playground if applicable (CodeSandbox, Repl.it). Show, don't just tell.")
    
    # Security
    if score >= 50 and not metrics['has_gitignore']:
        roadmap.append("🔒 SECURITY VULNERABILITIES: Your repo might expose secrets or use vulnerable dependencies. Audit immediately: never commit API keys or passwords (use .env files), add .env to .gitignore, scan dependencies with 'npm audit' or 'safety check', keep packages updated, use Dependabot for automated security updates, validate all user inputs, and run OWASP security checks. Security breaches destroy reputation.")
    
    # If repo is excellent, focus on maintenance and growth
    if score >= 90:
        roadmap.append("🌟 EXCELLENT PROJECT, MAINTAIN QUALITY: Your repo is top-tier, now sustain it: set up Renovate or Dependabot for auto dependency updates, respond to issues within 48 hours, release new versions with detailed changelogs following semver, write migration guides for breaking changes, monitor error tracking (Sentry, Bugsnag), collect user feedback via discussions, and plan roadmap openly.")
        roadmap.append("🚀 SCALE YOUR IMPACT: You've mastered this project, time to amplify: give conference talks about your work, write technical blog posts on Medium/Dev.to, mentor junior developers via issues/discussions, contribute to related open-source projects, create video tutorials, build a community (Discord/Slack), or turn project into SaaS product. Share your expertise.")
    
    # Limit roadmap to most important items (8-12 items)
    if len(roadmap) > 12:
        roadmap = roadmap[:12]
    
    # Ensure at least some guidance even for perfect repos
    if not roadmap:
        roadmap.append("Outstanding repository! Keep up the excellent work and continue following best practices")
        roadmap.append("Share your knowledge: write technical blog posts, give talks, or create tutorials about your project")
        roadmap.append("Engage with your users through issues, discussions, and regular updates")
    
    return {
        'score': score,
        'summary': summary,
        'roadmap': roadmap
    }

@app.route('/api/analyze', methods=['POST'])
def analyze():
    """Main endpoint to analyze a GitHub repository"""
    data = request.json
    repo_url = data.get('repo_url', '')
    
    if not repo_url:
        return jsonify({'error': 'Repository URL is required'}), 400
    
    # Fetch GitHub data
    github_data = fetch_github_data(repo_url)
    
    if not github_data:
        return jsonify({'error': 'Failed to fetch repository data. Make sure the URL is valid and the repository is public.'}), 400
    
    # Analyze repository
    analysis_result = analyze_repository(github_data)
    
    # Generate summary and roadmap
    result = generate_summary_and_roadmap(analysis_result)
    
    # Add metrics for transparency
    result['metrics'] = analysis_result['metrics']
    result['breakdown'] = analysis_result['breakdown']
    
    # Remove rating field to keep only numerical score
    if 'rating' in result:
        del result['rating']
    
    return jsonify(result)

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'message': 'Repository Mirror API is running'})

if __name__ == '__main__':
    print("🚀 Repository Mirror API starting...")
    print("📊 GitHub Token:", "Configured" if GITHUB_TOKEN else "Not configured (rate limits will apply)")
    app.run(debug=True, host='0.0.0.0', port=5000)
