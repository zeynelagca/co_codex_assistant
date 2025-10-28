# CoFlow Task Analyzer

AI-powered task and ticket analysis system for Odoo 17, featuring automatic complexity scoring, solution suggestions, and GitHub integration with Claude AI.

## Features

### Core Capabilities
- **AI-Powered Analysis**: Uses Claude 3.5 Sonnet for intelligent task/ticket analysis
- **Complexity Scoring**: Automatic complexity assessment (0-10 scale)
- **Time Estimation**: AI-generated time estimates for task completion
- **Solution Suggestions**: Detailed, actionable solution recommendations
- **Code Generation**: Automatic code suggestions for technical tasks

### GitHub Integration
- **Automatic Code Push**: Push AI-generated code to GitHub repositories
- **Pull Request Creation**: Automatically create PRs with detailed descriptions
- **Multi-Repository Support**: Configure repos per project or per customer
- **Issue Creation**: Create GitHub issues from Odoo tasks/tickets

### Intelligence Features
- **Historical Analysis**: Find and analyze similar past tasks/tickets
- **Context-Aware**: Considers messages, attachments, and related records
- **Code Context**: Analyzes existing codebase when configured
- **Learning System**: Improves estimates based on historical data

### Flexible Triggering
- **Manual**: Analyze on-demand via button click
- **Automatic**: Trigger on task/ticket creation
- **Stage-Based**: Analyze when stage changes
- **Scheduled**: Batch analysis via cron job

## Installation

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

Or install individually:
```bash
pip install anthropic PyGithub requests
```

### 2. Install Odoo Module

1. Copy the `fizixai_task_analyzer` folder to your Odoo addons directory
2. Update the app list in Odoo
3. Install "CoFlow Task Analyzer" module

### 3. Configure API Keys

You'll need:
- **Claude API Key**: Get from https://console.anthropic.com/
- **GitHub Personal Access Token**: Create at https://github.com/settings/tokens
  - Required scopes: `repo` (Full control of private repositories)

## Configuration

### Global Configuration (System Parameters)

Navigate to Settings > Technical > Parameters > System Parameters

Add the following parameters (optional, can be configured per project/customer):
- `coflow.claude_api_key`: Your Claude API key
- `coflow.github_repo_url`: Default GitHub repository URL
- `coflow.github_token`: Default GitHub PAT

### Project Configuration

For each project that should use AI analysis:

1. Go to Project > Configuration > Projects
2. Select your project
3. Go to "AI & GitHub" tab
4. Configure:
   - **GitHub Repository URL**: `https://github.com/username/repo`
   - **GitHub Token**: Your PAT
   - **Default Branch**: Usually `main` or `master`
   - **Claude API Key**: (optional if global key is set)
   - **Claude Model**: Choose model (recommended: Claude 3.5 Sonnet)
   - **Enable AI Analysis**: Check to activate
   - **Auto Trigger on Create**: Analyze new tasks automatically
   - **Trigger on Stage Change**: Analyze when task stage changes
   - **Enable Auto Development**: Allow automatic code generation and GitHub push
   - **Max Complexity for Auto Dev**: Tasks with complexity ≤ this value will be auto-developed

### Customer Configuration

For customer-specific repositories:

1. Go to Contacts
2. Select a customer (must be a company)
3. Go to "AI & GitHub" tab
4. Configure repository and AI settings specific to this customer

Customer settings override project settings.

## Usage

### Analyzing a Task

1. **Manual Analysis**:
   - Open a task
   - Click "AI Analyze" button in the header
   - Wait for analysis to complete

2. **Automatic Analysis**:
   - Create a new task (if auto-trigger is enabled)
   - Or change task stage (if stage trigger is enabled)

3. **View Results**:
   - Go to "AI Analysis" tab to see:
     - Complexity score and level
     - Estimated hours
     - Solution suggestions
     - Code suggestions (if applicable)
     - Similar historical tasks

### Analyzing a Ticket

Same as tasks - the system works identically for helpdesk tickets.

### GitHub Integration

When auto-development is enabled and a task has low complexity:

1. AI generates code solution
2. System creates a new branch: `coflow/task-{id}-{name}`
3. Code is committed to the branch
4. Pull request is created automatically
5. GitHub PR URL is saved in the task

### Viewing Analysis History

Navigate to: Project > AI Analysis History

Here you can:
- View all past analyses
- Filter by complexity level, customer, project
- See GitHub actions taken
- Review solution suggestions

## Architecture

```
fizixai_task_analyzer/
├── models/
│   ├── project_project.py       # Project configuration
│   ├── project_task.py          # Task extensions
│   ├── helpdesk_ticket.py       # Ticket extensions
│   ├── res_partner.py           # Customer configuration
│   └── ai_analysis_history.py   # Analysis history
├── services/
│   ├── claude_mcp_service.py    # Claude AI integration
│   ├── github_service.py        # GitHub API integration
│   ├── complexity_analyzer.py   # Complexity analysis engine
│   └── ai_analyzer.py           # Main analysis orchestrator
├── views/
│   ├── project_project_views.xml
│   ├── project_task_views.xml
│   ├── helpdesk_ticket_views.xml
│   ├── res_partner_views.xml
│   └── ai_analysis_history_views.xml
├── data/
│   └── scheduled_actions.xml    # Cron jobs
└── security/
    └── ir.model.access.csv      # Access rights
```

## Complexity Scoring Guide

The AI assigns complexity scores based on:

| Score | Level | Description |
|-------|-------|-------------|
| 0-2 | Trivial | Simple config, data entry, minor text changes |
| 3-4 | Simple | Straightforward features, clear requirements |
| 5-6 | Moderate | Some design needed, multiple components |
| 7-8 | Complex | Significant architecture changes, unclear requirements |
| 9-10 | Critical | Major refactoring, high risk, system-wide impact |

## Best Practices

1. **API Keys Security**:
   - Use project/customer-specific keys when possible
   - Never commit API keys to version control
   - Rotate keys periodically

2. **GitHub Permissions**:
   - Use fine-grained PATs with minimum required permissions
   - Create separate tokens per project/customer
   - Review auto-created PRs before merging

3. **Auto-Development**:
   - Start with low threshold (2-3) for auto-development
   - Always review auto-generated code
   - Use for simple, well-defined tasks only

4. **Cost Management**:
   - Claude API calls cost money - monitor usage
   - Use scheduled actions wisely (hourly is reasonable)
   - Consider disabling auto-trigger for high-volume projects

## Troubleshooting

### Analysis Fails

1. Check Claude API key is valid
2. Verify API key has sufficient credits
3. Check task/ticket has description
4. Review error message in "AI Analysis" tab

### GitHub Push Fails

1. Verify GitHub token has `repo` scope
2. Check repository URL is correct
3. Ensure default branch exists
4. Review GitHub token expiration

### No Similar Records Found

This is normal for:
- First analyses in the system
- Very unique tasks
- Different keywords than historical data

## Support

For issues, feature requests, or questions:
- GitHub: https://github.com/coflow/odoo-task-analyzer
- Email: support@coflow.com.tr

## License

LGPL-3

## Credits

Developed by CoFlow
Powered by Anthropic Claude AI
