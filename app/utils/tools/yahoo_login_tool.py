"""Tool for retrieving Yahoo credentials for automated login."""
import logging
import os
from typing import Dict, Any, List
from google.adk.tools import FunctionTool

logger = logging.getLogger(__name__)


class YahooLoginTool:
    """Tool for handling Yahoo login credentials.
    
    This tool allows the agent to securely retrieve credentials from the environment
    when it encounters a login page.
    """
    
    def get_tools(self) -> List[FunctionTool]:
        """Get the login tools."""
        return [
            FunctionTool(func=self.get_yahoo_credentials),
            FunctionTool(func=self.get_login_instructions),
        ]
    
    async def get_yahoo_credentials(self) -> Dict[str, Any]:
        """Retrieve Yahoo credentials from environment variables.
        
        Use this tool ONLY when you are on a Yahoo login page and need to enter
        credentials.
        
        Returns:
            Dictionary containing username and password if available.
        """
        email = os.getenv('YAHOO_EMAIL')
        password = os.getenv('YAHOO_PASSWORD')
        
        if not email or not password:
            return {
                'status': 'error',
                'error': 'Credentials not found',
                'message': 'YAHOO_EMAIL and YAHOO_PASSWORD must be set in .env file'
            }
        
        return {
            'status': 'success',
            'email': email,
            'password': password,
            'message': 'Credentials retrieved. Use playwright_fill to enter them.'
        }

    async def get_login_instructions(self) -> str:
        """Get instructions on how to handle the Yahoo login flow.
        
        Returns:
            Step-by-step instructions for logging in.
        """
        return """
        HOW TO LOG IN TO YAHOO:
        
        1. If you see a login page (URL contains 'login.yahoo.com'):
           - Call `get_yahoo_credentials` to get the email and password.
           
        2. Enter Email:
           - Use `playwright__browser_fill` with selector `#login-username` (or similar input field).
           - Value: The email returned by `get_yahoo_credentials`.
           
        3. Click Next:
           - Use `playwright__browser_click` with selector `#login-signin` (or 'Next' button).
           
        4. Enter Password:
           - Wait for password field to appear.
           - Use `playwright__browser_fill` with selector `#login-passwd`.
           - Value: The password returned by `get_yahoo_credentials`.
           
        5. Click Next/Sign In:
           - Use `playwright__browser_click` with selector `#login-signin`.
           
        6. Handle 2FA (if prompted):
           - If asked for verification code, you CANNOT proceed automatically.
           - Notify the user they need to log in manually in the browser window.
           
        7. Verify Login:
           - Wait for redirect to the fantasy league page.
        """
