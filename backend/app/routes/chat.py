import uuid
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.database import get_db
from backend.app.models.project import Project
from backend.app.models.chat_message import ChatMessage
from backend.app.schemas.chat import (
    ConversationalStepRequest,
    ConversationalStepResponse,
    ChatMessageResponse,
    CreateProjectFromChatRequest,
)
from backend.app.schemas.project import ProjectResponse, ProjectCreate
from backend.app.services.conversational_assistant import conversational_assistant
from backend.app.services.workspace_manager import workspace_manager
from backend.app.services.subdomain_service import subdomain_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/chat", tags=["Conversational Chatbot"])

@router.post("/message", response_model=ConversationalStepResponse)
async def process_chat_message(
    payload: ConversationalStepRequest,
    x_gemini_api_key: Optional[str] = Header(None, alias="X-Gemini-Api-Key"),
    db: AsyncSession = Depends(get_db)
):
    """
    Processes a conversational turn in the 9-step guided website building flow.
    Evaluates natural language input, updates extracted state, and returns next question + suggestions.
    Optionally persists messages if project_id is provided.
    """
    if not payload.user_message or not payload.user_message.strip():
        raise HTTPException(status_code=400, detail="User message cannot be empty.")

    try:
        response = await conversational_assistant.process_chat_turn(
            user_message=payload.user_message,
            current_step=payload.current_step or "business_name",
            collected_data=payload.collected_data or {},
            api_key=x_gemini_api_key
        )
    except Exception as e:
        logger.error(f"Error processing chat turn with Gemini: {e}", exc_info=True)
        err_str = str(e)
        if "API key is not configured" in err_str or "No active Gemini API key" in err_str:
            raise HTTPException(
                status_code=400,
                detail="Gemini API key is not configured. Please set GEMINI_API_KEY in your local .env file."
            )
        if "API_KEY_INVALID" in err_str or "401" in err_str or "Invalid Gemini API key" in err_str:
            raise HTTPException(
                status_code=401,
                detail="Invalid Gemini API key. Please check your GEMINI_API_KEY configuration."
            )
        if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "quota" in err_str.lower():
            raise HTTPException(
                status_code=429,
                detail="Gemini API rate limit or quota exceeded (429). Please try again shortly or check your Google AI Studio quota."
            )
        if "timeout" in err_str.lower() or "deadline" in err_str.lower():
            raise HTTPException(
                status_code=504,
                detail="Gemini API request timed out. Please try sending your message again."
            )
        raise HTTPException(
            status_code=502,
            detail=f"Gemini AI error: {err_str}"
        )

    # Persist message history if project_id is bound
    if payload.project_id:
        try:
            project = await db.get(Project, payload.project_id)
            if project:
                user_msg = ChatMessage(
                    project_id=payload.project_id,
                    sender="user",
                    step=payload.current_step,
                    content=payload.user_message
                )
                db.add(user_msg)

                bot_msg = ChatMessage(
                    project_id=payload.project_id,
                    sender="assistant",
                    step=response.next_step,
                    content=response.assistant_message,
                    message_metadata={
                        "suggested_options": response.suggested_options,
                        "updated_data": response.updated_data,
                        "is_complete": response.is_complete
                    }
                )
                db.add(bot_msg)
                await db.commit()
        except Exception as e:
            logger.warning(f"Failed to persist chat message in DB: {e}")

    return response

@router.get("/{project_id}/history", response_model=List[ChatMessageResponse])
async def get_chat_history(
    project_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Retrieves all conversational chat turns for a specific project."""
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    query = (
        select(ChatMessage)
        .where(ChatMessage.project_id == project_id)
        .order_by(ChatMessage.created_at.asc())
    )
    result = await db.execute(query)
    messages = result.scalars().all()
    return messages

@router.post("/create-project", response_model=ProjectResponse, status_code=201)
async def create_project_from_conversation(
    payload: CreateProjectFromChatRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Converts completed conversational requirements into a persistent Project record.
    Initializes workspace directory and prepares project for agent execution.
    """
    state = payload.collected_data
    business_name = state.get("business_name") or "My Business"
    industry = state.get("industry") or "General Business"
    description = state.get("description") or f"A professional website for {business_name}"
    target_audience = state.get("target_audience")
    website_type = state.get("website_type") or "single-page"
    selected_pages = state.get("selected_pages")
    if website_type == "single-page":
        selected_pages = ["home"]
    elif selected_pages:
        from backend.app.services.conversational_assistant import sanitize_page_list
        selected_pages = sanitize_page_list(selected_pages)
    else:
        selected_pages = ["home", "about", "services", "contact"]

    tech_stack = state.get("tech_stack") or "react"
    style = state.get("style") or "Modern & Clean"
    primary_color = state.get("primary_color") or "#2563eb"
    secondary_color = state.get("secondary_color") or "#0f172a"
    accent_color = state.get("accent_color") or "#38bdf8"
    subdomain = state.get("subdomain")
    custom_domain = state.get("custom_domain")

    # Validate using Pydantic ProjectCreate model
    try:
        project_in = ProjectCreate(
            name=business_name.strip(),
            industry=industry.strip(),
            description=description.strip(),
            target_audience=target_audience.strip() if target_audience else None,
            style=style,
            website_type=website_type,
            selected_pages=selected_pages,
            tech_stack=tech_stack,
            subdomain=subdomain,
            custom_domain=custom_domain,
            primary_color=primary_color,
            secondary_color=secondary_color,
            accent_color=accent_color
        )
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Invalid project specification: {str(e)}")

    if project_in.subdomain:
        is_avail = await subdomain_service.is_slug_available(db, project_in.subdomain)
        if not is_avail:
            raise HTTPException(status_code=409, detail=f"Subdomain '{project_in.subdomain}' is already taken.")

    project_id = str(uuid.uuid4())
    project = Project(
        id=project_id,
        name=project_in.name,
        industry=project_in.industry,
        description=project_in.description,
        target_audience=project_in.target_audience,
        style=project_in.style,
        website_type=project_in.website_type,
        selected_pages=project_in.selected_pages,
        tech_stack=project_in.tech_stack,
        subdomain=project_in.subdomain,
        custom_domain=project_in.custom_domain,
        primary_color=project_in.primary_color,
        secondary_color=project_in.secondary_color,
        accent_color=project_in.accent_color,
        status="draft",
        progress_percentage="0%",
        requirements_spec=state
    )

    db.add(project)
    await db.commit()
    await db.refresh(project)

    # Initialize workspace folder
    workspace_manager.get_project_dir(project_id)

    # Record initial onboarding chat messages
    welcome_bot = ChatMessage(
        project_id=project_id,
        sender="assistant",
        step="welcome",
        content=f"Welcome! Project '{business_name}' configured with {website_type} architecture ({tech_stack}). Agents stand ready to generate."
    )
    db.add(welcome_bot)
    await db.commit()

    return project
