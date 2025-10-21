# Project Customer Reports Module for Odoo 17 CE

## Overview

This module enables automated and manual generation of project and timesheet reports in professional XLSX format, sent directly to customers via email.

## Installation

1. Install Python dependency:
   ```bash
   pip3 install xlsxwriter
   ```

2. Copy this module to your Odoo addons directory

3. Restart Odoo server

4. Update Apps List and Install "Project Customer Reports"

## Configuration

### Setting up Report Configurations

1. Go to: **Project → Customer Reports → Report Configurations**
2. Click **Create** to add a new configuration
3. Fill in the following details:
   - **Configuration Name**: Descriptive name for this report config
   - **Project**: Select the project to report on
   - **Customer**: Select the customer (auto-filled from project)
   - **Email To**: Customer email address (validated format)
   - **Email CC**: Optional CC recipients (validated format)

4. Configure **Report Types** tab:
   - **Send Daily Report**: Enable for daily task reports
   - **Daily Report Time**: Time to send (24h format, e.g., 18.0 for 6 PM)
   - **Send Weekly Report**: Enable for weekly task reports
   - **Weekly Report Day**: Day of week to send (e.g., Friday)
   - **Send Weekly Timesheet Report**: Include timesheet data with weekly reports

5. Configure **Report Options** tab:
   - **Include Task Description**: Show task descriptions
   - **Include Allocated Hours**: Show planned hours
   - **Include Spent Hours**: Show actual hours worked
   - **Include Tags**: Show task tags
   - **Include Sprint**: Show sprint information (if available)

6. **Save** the configuration

## Usage

### Automatic Reports (Scheduled)

Once configured, reports are sent automatically:
- **Daily Reports**: Sent at the configured time each day
- **Weekly Reports**: Sent on the configured day of the week
- Reports run via cron jobs in the background

### Manual Report Generation

#### Method 1: From Project Form
1. Open any project
2. Click the **"Send Report"** button in the header
3. Select report type and date range
4. Click **"Send Report"**

#### Method 2: Quick Actions
1. Open any project
2. Go to the **"Customer Reports"** tab
3. Use the quick action buttons:
   - **"Send Daily Report Now"**: Sends reports for all active configs
   - **"Send Weekly Report Now"**: Sends weekly and timesheet reports

#### Method 3: Send Report Wizard
1. From any project, click **"Send Report"** button
2. In the wizard:
   - **Project**: Auto-filled, can be changed
   - **Customer**: Auto-filled from project
   - **Email To/CC**: Auto-filled, can be customized
   - **Report Type**: Choose Daily, Weekly, or Timesheet
   - **Date Range**: Specify custom date range for the report
3. Click **"Send Report"**

## Features

### Report Types

**Daily Task Report**
- Tasks created on the selected date
- Tasks with deadlines on the selected date
- Tasks modified on the selected date
- Professional XLSX format with company branding
- Customizable columns based on configuration

**Weekly Task Report**
- Tasks from the past 7 days (or custom range)
- Includes tasks created, due, or modified in the period
- Summary totals for allocated and spent hours
- Organized by stage

**Weekly Timesheet Report**
- Detailed timesheet entries from the period
- Shows: Date, Employee, Task, Description, Hours
- Summary by employee
- Total hours calculation

### Email Features

- **Professional HTML templates** with company branding
- **Email validation**: Ensures valid email format for To/CC fields
- **Multiple recipients**: Support for comma-separated email lists
- **Automatic attachments**: XLSX reports attached to emails
- **Custom subjects**: Dynamic subjects with project name and dates
- **CC support**: Send copies to additional recipients

### Report Intelligence

**Smart Task Filtering**
The module intelligently captures tasks relevant to the reporting period:
- Tasks **created** during the period
- Tasks with **deadlines** in the period
- Tasks **modified/updated** during the period

This ensures customers see:
- New tasks assigned to their project
- Tasks due in the reporting period
- Any updates or progress on existing tasks

### Date Range Flexibility

- **Automated scheduling**: Use default date ranges (today, last 7 days)
- **Custom date ranges**: Specify exact date ranges in the wizard
- **Date parameters**: Fully functional date selection

## Technical Details

### Models

- `project.report.config`: Configuration for automated reports
- `send.report.wizard`: Wizard for manual report generation
- `project.report.xlsx`: XLSX report generator (AbstractModel)

### Email Templates

- `mail_template_task_report`: Template for task reports
- `mail_template_timesheet_report`: Template for timesheet reports

### Cron Jobs

- `ir_cron_send_daily_reports`: Runs daily to send configured reports
- `ir_cron_send_weekly_reports`: Runs daily, filters by configured weekday

### Security

Access rights for Project Users and Project Managers included.

## Recent Improvements (v17.0.1.0.0)

✅ **Fixed wizard date parameter handling** - Date ranges selected in the wizard now correctly affect the generated reports

✅ **Improved task filtering** - Reports now include tasks created, due, or modified in the period (not just modified)

✅ **Added email validation** - Both wizard and configuration now validate email addresses to prevent errors

✅ **Enhanced date range support** - Methods accept custom date ranges throughout the module

✅ **Better customer visibility** - Customers now see all relevant tasks, not just modified ones

## Support

For issues, questions, or feature requests, please contact your system administrator.

## License

LGPL-3
