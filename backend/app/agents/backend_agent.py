import logging
import json
from typing import Dict, Any, Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.contact_submission import ContactSubmission
from backend.app.schemas.contact import ContactSubmissionCreate
from backend.app.schemas.agent import CodeFile

logger = logging.getLogger(__name__)

class BackendAgent:
    """
    Backend Agent:
    - Provides server-side submission logic and schema validation for generated sites.
    - Implements anti-spam protections (honeypot check, string trimming).
    - Persists inquiries directly into project database storage.
    - Generates standalone serverless API routes for target platforms (e.g., Netlify Functions).
    """

    AGENT_NAME = "Backend Agent"

    def generate_serverless_handler(self, project_id: str) -> CodeFile:
        """
        Generates a standalone Netlify serverless function code file for the generated website,
        allowing it to operate independently when deployed externally.
        """
        code = f"""// Netlify Serverless Function: contact.js
exports.handler = async (event, context) => {{
    if (event.httpMethod !== 'POST') {{
        return {{ statusCode: 405, body: JSON.stringify({{ detail: 'Method Not Allowed' }}) }};
    }}

    try {{
        const body = JSON.parse(event.body || '{{}}');
        if (body.website_hp) {{
            // Honeypot caught spam
            return {{ statusCode: 200, body: JSON.stringify({{ status: 'received' }}) }};
        }}

        if (!body.name || !body.email || !body.message) {{
            return {{ statusCode: 400, body: JSON.stringify({{ detail: 'Missing required fields' }}) }};
        }}

        console.log(`[Contact Submission] Site: {project_id}`, body);

        return {{
            statusCode: 200,
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify({{ status: 'success', message: 'Inquiry received' }})
        }};
    }} catch (err) {{
        return {{ statusCode: 500, body: JSON.stringify({{ detail: 'Internal Server Error' }}) }};
    }}
}};
"""
        return CodeFile(path="netlify/functions/contact.js", content=code, description="Serverless contact submission handler")

    async def process_contact_submission(
        self,
        db: AsyncSession,
        project_id: str,
        data: ContactSubmissionCreate,
        ip_address: Optional[str] = None
    ) -> Tuple[bool, str, Optional[int]]:
        """
        Validates and records a genuine contact submission into the database.
        Returns: (success, message, record_id)
        """
        # 1. Anti-spam honeypot detection
        if data.website_hp and data.website_hp.strip():
            logger.warning(f"Spam bot detected on project {project_id} via honeypot.")
            return True, "Your message has been received.", None

        # 2. Field validation
        if not data.name or len(data.name.strip()) < 2:
            return False, "Name must be at least 2 characters.", None
        if not data.message or len(data.message.strip()) < 5:
            return False, "Message must be at least 5 characters.", None

        # 3. Create persistent record
        submission = ContactSubmission(
            project_id=project_id,
            name=data.name.strip(),
            email=str(data.email).strip().lower(),
            phone=data.phone.strip() if data.phone else None,
            subject=data.subject.strip() if data.subject else None,
            message=data.message.strip(),
            status="unread",
            ip_address=ip_address
        )
        db.add(submission)
        await db.commit()
        await db.refresh(submission)

        logger.info(f"Recorded contact submission #{submission.id} for project {project_id} from {submission.email}")
        return True, "Your message has been received and saved.", submission.id

backend_agent = BackendAgent()
