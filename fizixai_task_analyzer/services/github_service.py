import logging
import base64
import re
from odoo import models, api, _
from odoo.exceptions import UserError

try:
    from github import Github, GithubException
except ImportError:
    Github = None
    GithubException = Exception

_logger = logging.getLogger(__name__)


class GithubService(models.AbstractModel):
    _name = 'github.service'
    _description = 'GitHub Integration Service'

    @api.model
    def get_github_credentials(self, project=None, partner=None):
        """
        Get GitHub credentials with priority:
        1. Partner-specific
        2. Project-specific
        3. System parameter (global)
        """
        repo_url = None
        token = None
        branch = 'main'

        if partner:
            repo_url = partner.github_repo_url
            token = partner.github_token
            branch = partner.github_branch or 'main'

        if not repo_url and project:
            repo_url = project.github_repo_url
            token = project.github_token
            branch = project.github_branch or 'main'

        if not repo_url:
            # Try system parameters
            repo_url = self.env['ir.config_parameter'].sudo().get_param('fizixai.github_repo_url')
            token = self.env['ir.config_parameter'].sudo().get_param('fizixai.github_token')

        if not repo_url or not token:
            raise UserError(_('GitHub repository and token are not configured.'))

        return {
            'repo_url': repo_url,
            'token': token,
            'branch': branch,
        }

    @api.model
    def _parse_repo_url(self, repo_url):
        """Parse GitHub repository URL to get owner and repo name"""
        # Support both HTTPS and SSH URLs
        # https://github.com/owner/repo
        # git@github.com:owner/repo.git

        if 'github.com/' in repo_url:
            # HTTPS URL
            match = re.search(r'github\.com[:/]([^/]+)/(.+?)(?:\.git)?$', repo_url)
            if match:
                return match.group(1), match.group(2)

        raise UserError(_('Invalid GitHub repository URL: %s') % repo_url)

    @api.model
    def get_github_client(self, project=None, partner=None):
        """Get authenticated GitHub client"""
        if not Github:
            raise UserError(_('PyGithub package is not installed. Please install it: pip install PyGithub'))

        credentials = self.get_github_credentials(project=project, partner=partner)
        return Github(credentials['token']), credentials

    @api.model
    def fetch_code(self, github_url, file_paths=None, partner=None, project=None):
        """
        Fetch code content from GitHub repository

        Args:
            github_url: Full GitHub URL or repo path
            file_paths: List of specific file paths to fetch
            partner: res.partner record
            project: project.project record

        Returns:
            str: Code content
        """
        try:
            client, credentials = self.get_github_client(project=project, partner=partner)
            owner, repo_name = self._parse_repo_url(credentials['repo_url'])

            repo = client.get_repo(f"{owner}/{repo_name}")

            if file_paths:
                # Fetch specific files
                code_content = ""
                for file_path in file_paths:
                    try:
                        file_content = repo.get_contents(file_path, ref=credentials['branch'])
                        decoded_content = base64.b64decode(file_content.content).decode('utf-8')
                        code_content += f"\n\n# File: {file_path}\n{decoded_content}\n"
                    except GithubException as e:
                        _logger.warning(f"Failed to fetch {file_path}: {str(e)}")
                return code_content
            else:
                # Fetch repository structure
                contents = repo.get_contents("", ref=credentials['branch'])
                code_content = "Repository structure:\n"
                for content in contents:
                    code_content += f"- {content.path} ({content.type})\n"
                return code_content

        except Exception as e:
            _logger.error(f"Failed to fetch code from GitHub: {str(e)}")
            return None

    @api.model
    def create_and_push_code(self, task=None, ticket=None, code_suggestion=None, solution_description=None):
        """
        Create code based on AI suggestion and push to GitHub

        Args:
            task: project.task record
            ticket: helpdesk.ticket record
            code_suggestion: Code suggested by AI
            solution_description: Solution description from AI

        Returns:
            dict with success status, commit SHA, PR URL
        """
        if not task and not ticket:
            raise UserError(_('Either task or ticket must be provided'))

        record = task or ticket
        record_type = 'task' if task else 'ticket'
        record_name = record.name

        try:
            # Get GitHub credentials from project or partner
            project = task.project_id if task else None
            partner = record.partner_id

            client, credentials = self.get_github_client(project=project, partner=partner)
            owner, repo_name = self._parse_repo_url(credentials['repo_url'])
            repo = client.get_repo(f"{owner}/{repo_name}")

            # Create a new branch for this change
            branch_name = f"fizixai/{record_type}-{record.id}-{self._sanitize_branch_name(record_name)}"

            # Get the base branch reference
            base_branch = repo.get_branch(credentials['branch'])
            base_sha = base_branch.commit.sha

            # Create new branch
            try:
                repo.create_git_ref(f"refs/heads/{branch_name}", base_sha)
                _logger.info(f"Created branch: {branch_name}")
            except GithubException as e:
                if 'Reference already exists' in str(e):
                    _logger.warning(f"Branch {branch_name} already exists, using it")
                else:
                    raise

            # Parse code suggestion to determine file path and content
            # Expected format: "# File: path/to/file.py\n<code>"
            files_to_update = self._parse_code_suggestion(code_suggestion)

            if not files_to_update:
                raise UserError(_('Could not determine file paths from code suggestion'))

            # Update or create files
            for file_path, file_content in files_to_update.items():
                try:
                    # Try to get existing file
                    existing_file = repo.get_contents(file_path, ref=branch_name)
                    # Update existing file
                    repo.update_file(
                        file_path,
                        f"Update {file_path} for {record_type} #{record.id}: {record_name}",
                        file_content,
                        existing_file.sha,
                        branch=branch_name
                    )
                    _logger.info(f"Updated file: {file_path}")
                except GithubException:
                    # File doesn't exist, create new one
                    repo.create_file(
                        file_path,
                        f"Create {file_path} for {record_type} #{record.id}: {record_name}",
                        file_content,
                        branch=branch_name
                    )
                    _logger.info(f"Created file: {file_path}")

            # Create Pull Request
            pr_title = f"[FizixAI] {record_type.capitalize()} #{record.id}: {record_name}"
            pr_body = f"""## Automated PR by FizixAI

**{record_type.capitalize()}:** {record_name}
**Complexity Score:** {record.ai_complexity_score if hasattr(record, 'ai_complexity_score') else 'N/A'}

### Solution Description
{solution_description or 'No description provided'}

### Changes
{self._generate_changes_summary(files_to_update)}

---
*This PR was automatically generated by FizixAI Task Analyzer*
"""

            pr = repo.create_pull(
                title=pr_title,
                body=pr_body,
                head=branch_name,
                base=credentials['branch']
            )

            _logger.info(f"Created PR: {pr.html_url}")

            return {
                'success': True,
                'commit_sha': base_sha,
                'pr_url': pr.html_url,
                'branch_name': branch_name,
            }

        except GithubException as e:
            _logger.error(f"GitHub API error: {str(e)}")
            raise UserError(_('GitHub Error: %s') % str(e))
        except Exception as e:
            _logger.error(f"Failed to create and push code: {str(e)}")
            raise UserError(_('Failed to push code: %s') % str(e))

    def _sanitize_branch_name(self, name):
        """Sanitize branch name to be GitHub-compatible"""
        # Remove special characters, replace spaces with dashes
        sanitized = re.sub(r'[^a-zA-Z0-9-_]', '-', name.lower())
        # Remove consecutive dashes
        sanitized = re.sub(r'-+', '-', sanitized)
        # Truncate to reasonable length
        return sanitized[:50]

    def _parse_code_suggestion(self, code_suggestion):
        """
        Parse code suggestion to extract file paths and content

        Expected format:
        # File: path/to/file1.py
        <code content>

        # File: path/to/file2.py
        <code content>

        Returns:
            dict: {file_path: content}
        """
        files = {}

        if not code_suggestion:
            return files

        # Split by file markers
        file_pattern = r'#\s*File:\s*(.+?)\n'
        parts = re.split(file_pattern, code_suggestion)

        # parts will be: ['', 'file1.py', '<content>', 'file2.py', '<content>', ...]
        for i in range(1, len(parts), 2):
            if i + 1 < len(parts):
                file_path = parts[i].strip()
                file_content = parts[i + 1].strip()
                files[file_path] = file_content

        # If no file markers found, assume single file
        if not files:
            # Try to infer file type from code
            file_ext = self._infer_file_extension(code_suggestion)
            files[f'auto_generated{file_ext}'] = code_suggestion

        return files

    def _infer_file_extension(self, code):
        """Infer file extension from code content"""
        if 'def ' in code or 'class ' in code or 'import ' in code:
            return '.py'
        elif 'function ' in code or 'const ' in code or 'let ' in code:
            return '.js'
        elif '<?xml' in code or '<odoo>' in code:
            return '.xml'
        else:
            return '.txt'

    def _generate_changes_summary(self, files_to_update):
        """Generate a summary of changes for PR description"""
        summary = ""
        for file_path, content in files_to_update.items():
            lines = len(content.split('\n'))
            summary += f"- `{file_path}` ({lines} lines)\n"
        return summary

    @api.model
    def create_github_issue(self, task=None, ticket=None):
        """
        Create a GitHub issue for a task or ticket

        Args:
            task: project.task record
            ticket: helpdesk.ticket record

        Returns:
            str: GitHub issue URL
        """
        if not task and not ticket:
            raise UserError(_('Either task or ticket must be provided'))

        record = task or ticket
        record_type = 'task' if task else 'ticket'

        try:
            project = task.project_id if task else None
            partner = record.partner_id

            client, credentials = self.get_github_client(project=project, partner=partner)
            owner, repo_name = self._parse_repo_url(credentials['repo_url'])
            repo = client.get_repo(f"{owner}/{repo_name}")

            # Create issue
            issue_title = f"[{record_type.capitalize()}] {record.name}"
            issue_body = f"""## {record_type.capitalize()} Details

**Description:**
{record.description or 'No description'}

**Complexity Score:** {record.ai_complexity_score if hasattr(record, 'ai_complexity_score') else 'N/A'}

**AI Solution Suggestion:**
{record.ai_solution_suggestion if hasattr(record, 'ai_solution_suggestion') else 'No suggestion yet'}

---
*Created automatically by FizixAI Task Analyzer*
*Odoo {record_type.capitalize()} ID: {record.id}*
"""

            labels = []
            if hasattr(record, 'ai_complexity_level') and record.ai_complexity_level:
                labels.append(f"complexity-{record.ai_complexity_level}")

            issue = repo.create_issue(
                title=issue_title,
                body=issue_body,
                labels=labels
            )

            _logger.info(f"Created GitHub issue: {issue.html_url}")

            return issue.html_url

        except Exception as e:
            _logger.error(f"Failed to create GitHub issue: {str(e)}")
            raise UserError(_('Failed to create issue: %s') % str(e))
