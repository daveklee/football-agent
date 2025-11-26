"""Email sender utility for sending formatted summaries via Gmail SMTP."""
import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class EmailSender:
    """Send emails via Gmail SMTP."""
    
    def __init__(self):
        """Initialize email sender with Gmail credentials from environment."""
        self.sender_email = os.getenv('GMAIL_SENDER_EMAIL')
        self.app_password = os.getenv('GMAIL_APP_PASSWORD')
        self.recipient_email = os.getenv('GMAIL_RECIPIENT_EMAIL')
        
        # Gmail SMTP configuration
        self.smtp_server = 'smtp.gmail.com'
        self.smtp_port = 587
        
    def is_configured(self) -> bool:
        """Check if email is properly configured."""
        return all([self.sender_email, self.app_password, self.recipient_email])
    
    def format_summary_email(
        self,
        agent_responses: List[str],
        tool_calls: List[Dict[str, str]],
        session_id: str,
        event_count: int
    ) -> str:
        """Format the agent summary into an HTML email.
        
        Args:
            agent_responses: List of agent text responses
            tool_calls: List of tool call dicts with 'name' and optional 'args'
            session_id: Session ID for this run
            event_count: Total number of events processed
            
        Returns:
            HTML formatted email body
        """
        # Extract key actions
        lineup_changes = []
        trades = []
        waiver_wire = []
        injuries = []
        other_actions = []
        
        for call in tool_calls:
            name = call.get('name', '')
            if 'lineup' in name.lower() or 'optimize' in name.lower():
                lineup_changes.append(call)
            elif 'trade' in name.lower():
                trades.append(call)
            elif 'waiver' in name.lower() or 'pickup' in name.lower():
                waiver_wire.append(call)
            elif 'injury' in name.lower() or 'ir' in name.lower():
                injuries.append(call)
            elif 'playwright' in name.lower() or 'navigate' in name.lower() or 'click' in name.lower():
                # Browser actions - likely making changes
                other_actions.append(call)
        
        # Build HTML email
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            font-family: 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background-color: white;
            border-radius: 8px;
            padding: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #1a73e8;
            border-bottom: 3px solid #1a73e8;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #5f6368;
            margin-top: 30px;
            border-left: 4px solid #1a73e8;
            padding-left: 10px;
        }}
        .summary {{
            background-color: #e8f0fe;
            border-left: 4px solid #1a73e8;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        .action-item {{
            background-color: #f8f9fa;
            border-left: 3px solid #34a853;
            padding: 10px 15px;
            margin: 10px 0;
            border-radius: 4px;
        }}
        .tool-call {{
            font-family: 'Courier New', monospace;
            background-color: #f1f3f4;
            padding: 5px 10px;
            border-radius: 3px;
            display: inline-block;
            margin: 5px 0;
            font-size: 0.9em;
        }}
        .response {{
            background-color: #fef7e0;
            border-left: 3px solid #f9ab00;
            padding: 15px;
            margin: 15px 0;
            border-radius: 4px;
            font-style: italic;
        }}
        .metadata {{
            color: #5f6368;
            font-size: 0.9em;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #e0e0e0;
        }}
        .no-actions {{
            color: #5f6368;
            font-style: italic;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🏈 Fantasy Football Daily Summary</h1>
        
        <div class="summary">
            <strong>Run Date:</strong> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}<br>
            <strong>Session ID:</strong> {session_id}<br>
            <strong>Events Processed:</strong> {event_count}
        </div>
"""
        
        # Lineup Changes
        if lineup_changes:
            html += "<h2>📋 Lineup Optimizations</h2>\n"
            for call in lineup_changes:
                html += f'<div class="action-item"><span class="tool-call">{call["name"]}</span></div>\n'
        
        # Trades
        if trades:
            html += "<h2>🤝 Trade Actions</h2>\n"
            for call in trades:
                html += f'<div class="action-item"><span class="tool-call">{call["name"]}</span></div>\n'
        
        # Waiver Wire
        if waiver_wire:
            html += "<h2>🔄 Waiver Wire Actions</h2>\n"
            for call in waiver_wire:
                html += f'<div class="action-item"><span class="tool-call">{call["name"]}</span></div>\n'
        
        # Injuries
        if injuries:
            html += "<h2>🏥 Injury Management</h2>\n"
            for call in injuries:
                html += f'<div class="action-item"><span class="tool-call">{call["name"]}</span></div>\n'
        
        # Other Actions
        if other_actions:
            html += "<h2>⚙️ Other Actions</h2>\n"
            for call in other_actions:
                html += f'<div class="action-item"><span class="tool-call">{call["name"]}</span></div>\n'
        
        # Agent Responses
        if agent_responses:
            html += "<h2>💬 Agent Reasoning & Summary</h2>\n"
            for response in agent_responses[:5]:  # Limit to first 5 responses
                # Clean up response text
                cleaned = response.strip()
                if cleaned:
                    html += f'<div class="response">{cleaned}</div>\n'
        
        # If no significant actions
        if not (lineup_changes or trades or waiver_wire or injuries):
            html += '<p class="no-actions">No significant lineup or roster changes were needed this week.</p>\n'
        
        # Metadata footer
        html += f"""
        <div class="metadata">
            <em>This summary was automatically generated by your Fantasy Football Agent.</em>
        </div>
    </div>
</body>
</html>
"""
        return html
    
    def send_summary_email(
        self,
        agent_responses: List[str],
        tool_calls: List[Dict[str, str]],
        session_id: str,
        event_count: int
    ) -> bool:
        """Send formatted summary email.
        
        Args:
            agent_responses: List of agent text responses
            tool_calls: List of tool call dicts
            session_id: Session ID for this run
            event_count: Total number of events processed
            
        Returns:
            True if email was sent successfully, False otherwise
        """
        if not self.is_configured():
            logger.warning("Email not configured. Skipping email send.")
            logger.warning("Set GMAIL_SENDER_EMAIL, GMAIL_APP_PASSWORD, and GMAIL_RECIPIENT_EMAIL in .env")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"🏈 Fantasy Football Daily Summary - {datetime.now().strftime('%m/%d/%Y')}"
            msg['From'] = self.sender_email
            msg['To'] = self.recipient_email
            
            # Format HTML content
            html_content = self.format_summary_email(
                agent_responses,
                tool_calls,
                session_id,
                event_count
            )
            
            # Attach HTML part
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Send email
            logger.info(f"Sending email to {self.recipient_email}...")
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.app_password)
                server.send_message(msg)
            
            logger.info("Email sent successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}", exc_info=True)
            return False

    def send_lineup_optimization_email(
        self,
        agent_responses: List[str],
        tool_calls: List[Dict[str, str]],
        session_id: str,
        event_count: int
    ) -> bool:
        """Send formatted lineup optimization summary email.
        
        Similar to send_summary_email but with a subject line specific to lineup optimization.
        
        Args:
            agent_responses: List of agent text responses
            tool_calls: List of tool call dicts
            session_id: Session ID for this run
            event_count: Total number of events processed
            
        Returns:
            True if email was sent successfully, False otherwise
        """
        if not self.is_configured():
            logger.warning("Email not configured. Skipping email send.")
            logger.warning("Set GMAIL_SENDER_EMAIL, GMAIL_APP_PASSWORD, and GMAIL_RECIPIENT_EMAIL in .env")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"🏈 Fantasy Football Lineup Optimization - {datetime.now().strftime('%m/%d/%Y')}"
            msg['From'] = self.sender_email
            msg['To'] = self.recipient_email
            
            # Format HTML content (reuse same formatting method)
            html_content = self.format_summary_email(
                agent_responses,
                tool_calls,
                session_id,
                event_count
            )
            
            # Attach HTML part
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Send email
            logger.info(f"Sending lineup optimization email to {self.recipient_email}...")
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.app_password)
                server.send_message(msg)
            
            logger.info("Lineup optimization email sent successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send lineup optimization email: {e}", exc_info=True)
            return False
