"""Email sender utility for sending formatted summaries via Gmail SMTP."""
import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from datetime import datetime
from typing import Dict, List, Optional, Any
import re
import base64

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
        
        # Track embedded images for the email
        self.embedded_images = {}
    
    def _markdown_to_html(self, text: str) -> str:
        """Convert common markdown patterns to HTML.
        
        Args:
            text: Markdown text
            
        Returns:
            HTML formatted text
        """
        if not text:
            return ""
        
        # Bold (**text** or __text__)
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
        text = re.sub(r'__(.+?)__', r'<strong>\1</strong>', text)
        
        # Italic (*text* or _text_)
        text = re.sub(r'\*([^*]+?)\*', r'<em>\1</em>', text)
        text = re.sub(r'_([^_]+?)_', r'<em>\1</em>', text)
        
        # Code (`code`)
        text = re.sub(r'`([^`]+?)`', r'<code>\1</code>', text)
        
        # Links [text](url)
        text = re.sub(r'\[([^\]]+?)\]\(([^)]+?)\)', r'<a href="\2">\1</a>', text)
        
        # Images ![alt](url) - handle specially for email embedding
        def replace_image(match):
            alt = match.group(1)
            url = match.group(2)
            # Generate a content ID for the image
            cid = f"img_{len(self.embedded_images)}"
            self.embedded_images[cid] = url
            return f'<img src="cid:{cid}" alt="{alt}" style="max-width: 100%; height: auto; margin: 10px 0;" />'
        
        text = re.sub(r'!\[([^\]]*?)\]\(([^)]+?)\)', replace_image, text)
        
        # Headers (# Header)
        text = re.sub(r'^### (.+)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)
        text = re.sub(r'^## (.+)$', r'<h2>\1</h2>', text, flags=re.MULTILINE)
        text = re.sub(r'^# (.+)$', r'<h1>\1</h1>', text, flags=re.MULTILINE)
        
        # Line breaks
        text = text.replace('\n\n', '<br><br>')
        text = text.replace('\n', '<br>')
        
        # Bullet lists (simple version)
        lines = text.split('<br>')
        in_list = False
        result = []
        for line in lines:
            if line.strip().startswith('* ') or line.strip().startswith('- '):
                if not in_list:
                    result.append('<ul>')
                    in_list = True
                item = line.strip()[2:]
                result.append(f'<li>{item}</li>')
            else:
                if in_list:
                    result.append('</ul>')
                    in_list = False
                result.append(line)
        if in_list:
            result.append('</ul>')
        
        return '<br>'.join(result)
        
    def is_configured(self) -> bool:
        """Check if email is properly configured."""
        return all([self.sender_email, self.app_password, self.recipient_email])
    
    def format_detailed_email(
        self,
        execution_log: List[Dict[str, Any]],
        session_id: str,
        event_count: int,
        error_details: Optional[str] = None,
        title: str = "Fantasy Football Summary"
    ) -> str:
        """Format the agent execution log into a detailed HTML email.
        
        Args:
            execution_log: List of execution events (text or tool calls)
            session_id: Session ID for this run
            event_count: Total number of events processed
            error_details: Optional string containing error traceback or details
            title: Email title
            
        Returns:
            HTML formatted email body
        """
        # Extract key actions for the summary section
        lineup_changes = []
        trades = []
        waiver_wire = []
        injuries = []
        other_actions = []
        
        for event in execution_log:
            if event.get('type') == 'tool':
                name = event.get('name', '')
                # Only count "write" actions or significant analysis tools
                if 'playwright' in name.lower() and ('click' in name.lower() or 'type' in name.lower()):
                     other_actions.append(event)
                elif 'lineup' in name.lower() or 'optimize' in name.lower():
                    lineup_changes.append(event)
                elif 'trade' in name.lower():
                    trades.append(event)
                elif 'waiver' in name.lower() or 'pickup' in name.lower():
                    waiver_wire.append(event)
                elif 'injury' in name.lower() or 'ir' in name.lower():
                    injuries.append(event)

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
            max-width: 900px;
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
            background-color: #f8f9fa;
            padding: 10px;
        }}
        .summary-box {{
            background-color: #e8f0fe;
            border-left: 4px solid #1a73e8;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        .error-box {{
            background-color: #fce8e6;
            border-left: 4px solid #ea4335;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
            color: #c5221f;
        }}
        .error-trace {{
            font-family: 'Courier New', monospace;
            white-space: pre-wrap;
            font-size: 0.85em;
            background-color: #fff;
            padding: 10px;
            border: 1px solid #f5c6cb;
            border-radius: 4px;
            margin-top: 10px;
            overflow-x: auto;
        }}
        .log-entry {{
            margin-bottom: 20px;
            padding-bottom: 20px;
            border-bottom: 1px solid #eee;
        }}
        .log-timestamp {{
            color: #888;
            font-size: 0.8em;
            margin-bottom: 5px;
        }}
        .agent-thought {{
            background-color: #fef7e0;
            border-left: 3px solid #f9ab00;
            padding: 15px;
            border-radius: 4px;
        }}
        .tool-call {{
            background-color: #f1f3f4;
            border-left: 3px solid #5f6368;
            padding: 10px 15px;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
        }}
        .tool-name {{
            font-weight: bold;
            color: #1a73e8;
        }}
        .tool-args {{
            color: #555;
            margin-top: 5px;
            white-space: pre-wrap;
        }}
        .metadata {{
            color: #5f6368;
            font-size: 0.9em;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #e0e0e0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{title}</h1>
        
        <div class="summary-box">
            <strong>Run Date:</strong> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}<br>
            <strong>Session ID:</strong> {session_id}<br>
            <strong>Events Processed:</strong> {event_count}
        </div>
"""
        
        # Error Section
        if error_details:
            html += f"""
        <div class="error-box">
            <h3>❌ Run Failed with Error</h3>
            <p>The agent encountered a problem during execution:</p>
            <div class="error-trace">{error_details}</div>
        </div>
"""

        # Executive Summary of Changes
        html += "<h2>📊 Executive Summary</h2>\n"
        
        has_changes = False
        if lineup_changes:
            html += "<h3>📋 Lineup Changes</h3><ul>"
            for item in lineup_changes:
                html += f"<li>Called <code>{item.get('name')}</code></li>"
            html += "</ul>"
            has_changes = True
            
        if trades:
            html += "<h3>🤝 Trade Actions</h3><ul>"
            for item in trades:
                html += f"<li>Called <code>{item.get('name')}</code></li>"
            html += "</ul>"
            has_changes = True
            
        if waiver_wire:
            html += "<h3>🔄 Waiver Wire</h3><ul>"
            for item in waiver_wire:
                html += f"<li>Called <code>{item.get('name')}</code></li>"
            html += "</ul>"
            has_changes = True
            
        if other_actions:
            html += "<h3>⚙️ Browser Actions</h3><ul>"
            for item in other_actions:
                html += f"<li>Called <code>{item.get('name')}</code></li>"
            html += "</ul>"
            has_changes = True
            
        if not has_changes:
            html += "<p><em>No significant write actions (changes) were detected in this run.</em></p>"

        # Detailed Execution Log
        html += "<h2>📝 Detailed Execution Log</h2>\n"
        
        for entry in execution_log:
            timestamp = entry.get('timestamp', '')
            entry_type = entry.get('type')
            content = entry.get('content')
            
            html += f'<div class="log-entry">\n'
            html += f'<div class="log-timestamp">{timestamp}</div>\n'
            
            if entry_type == 'text':
                # Convert markdown to HTML
                cleaned = content.strip() if content else ""
                if cleaned:
                    html_content = self._markdown_to_html(cleaned)
                    html += f'\u003cdiv class=\"agent-thought\"\u003e{html_content}\u003c/div\u003e\\n'
            elif entry_type == 'tool':
                name = entry.get('name', 'Unknown Tool')
                args = entry.get('args', '')
                html += f'<div class="tool-call">\n'
                html += f'<div class="tool-name">🔧 {name}</div>\n'
                if args:
                    html += f'<div class="tool-args">{args}</div>\n'
                html += f'</div>\n'
            
            html += f'</div>\n'

        # Footer
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
        execution_log: List[Dict[str, Any]],
        session_id: str,
        event_count: int,
        error_details: Optional[str] = None
    ) -> bool:
        """Send formatted summary email.
        
        Args:
            execution_log: List of execution events
            session_id: Session ID for this run
            event_count: Total number of events processed
            error_details: Optional error details
            
        Returns:
            True if email was sent successfully, False otherwise
        """
        return self._send_email(
            execution_log, 
            session_id, 
            event_count, 
            error_details, 
            title="🏈 Fantasy Football Daily Summary",
            subject_prefix="Daily Summary"
        )

    def send_lineup_optimization_email(
        self,
        execution_log: List[Dict[str, Any]],
        session_id: str,
        event_count: int,
        error_details: Optional[str] = None
    ) -> bool:
        """Send formatted lineup optimization summary email.
        
        Args:
            execution_log: List of execution events
            session_id: Session ID for this run
            event_count: Total number of events processed
            error_details: Optional error details
            
        Returns:
            True if email was sent successfully, False otherwise
        """
        return self._send_email(
            execution_log, 
            session_id, 
            event_count, 
            error_details, 
            title="🏈 Fantasy Football Lineup Optimization",
            subject_prefix="Lineup Optimization"
        )

    def _send_email(
        self,
        execution_log: List[Dict[str, Any]],
        session_id: str,
        event_count: int,
        error_details: Optional[str],
        title: str,
        subject_prefix: str
    ) -> bool:
        """Internal method to send email."""
        if not self.is_configured():
            logger.warning("Email not configured. Skipping email send.")
            logger.warning("Set GMAIL_SENDER_EMAIL, GMAIL_APP_PASSWORD, and GMAIL_RECIPIENT_EMAIL in .env")
            return False
        
        try:
            # reset embedded images for this email
            self.embedded_images = {}
            
            # Create message with mixed type to support both HTML and images
            msg = MIMEMultipart('related')
            status = "❌ FAILED" if error_details else "✅ SUCCESS"
            msg['Subject'] = f"{status}: {subject_prefix} - {datetime.now().strftime('%m/%d/%Y')}"
            msg['From'] = self.sender_email
            msg['To'] = self.recipient_email
            
            # Format HTML content (this populates self.embedded_images)
            html_content = self.format_detailed_email(
                execution_log,
                session_id,
                event_count,
                error_details,
                title
            )
            
            # Create alternative part for HTML
            msg_alternative = MIMEMultipart('alternative')
            msg.attach(msg_alternative)
            
            # Attach HTML part
            html_part = MIMEText(html_content, 'html')
            msg_alternative.attach(html_part)
            
            # Attach embedded images
            for cid, image_path in self.embedded_images.items():
                try:
                    # Handle sandbox:/ paths (these are Playwright screenshots)
                    if image_path.startswith('sandbox:/'):
                        # These are typically stored temporarily by Playwright
                        # For now, we'll skip embedding them as they may not be accessible
                        logger.warning(f"Skipping sandbox image: {image_path}")
                        continue
                    elif os.path.exists(image_path):
                        # Local file path
                        with open(image_path, 'rb') as f:
                            img_data = f.read()
                        image = MIMEImage(img_data)
                        image.add_header('Content-ID', f'<{cid}>')
                        msg.attach(image)
                except Exception as e:
                    logger.warning(f"Failed to embed image {image_path}: {e}")
            
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
