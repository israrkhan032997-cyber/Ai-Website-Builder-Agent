import re
from typing import Tuple, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.config import settings

class SubdomainService:
    """
    Manages RFC-1035 compliant customer subdomain slugs, collision detection,
    alternative generation, reservation, and multi-tenant routing resolution.
    """

    RESERVED_SLUGS = {
        "admin", "api", "app", "dashboard", "dev", "staging", "mail", "ftp",
        "smtp", "pop", "status", "test", "demo", "help", "support", "billing",
        "root", "localhost", "preview", "assets", "static", "login", "register"
    }

    def normalize_slug(self, name: str) -> str:
        """Converts business name into a clean, RFC-1035 valid subdomain slug."""
        clean = name.lower().strip()
        # Replace non-alphanumeric characters with hyphens
        clean = re.sub(r"[^a-z0-9]+", "-", clean)
        # Trim leading and trailing hyphens
        clean = clean.strip("-")
        # Ensure length constraint (3 to 63 chars)
        if len(clean) < 3:
            clean = f"site-{clean}"
        return clean[:63]

    def validate_slug(self, slug: str) -> Tuple[bool, str]:
        """Validates hostname compliance."""
        if not slug or len(slug) < 3:
            return False, "Subdomain must be at least 3 characters."
        if len(slug) > 63:
            return False, "Subdomain cannot exceed 63 characters."
        if not re.match(r"^[a-z0-9]([a-z0-9\-]*[a-z0-9])?$", slug):
            return False, "Subdomain may only contain lowercase letters, numbers, and hyphens (cannot start or end with a hyphen)."
        if slug in self.RESERVED_SLUGS:
            return False, f"Subdomain '{slug}' is reserved by the platform."
        return True, "Valid subdomain."

    async def is_slug_available(
        self,
        db: AsyncSession,
        slug: str,
        current_project_id: Optional[str] = None
    ) -> bool:
        """Checks if subdomain is already claimed in database."""
        from backend.app.models.project import Project
        query = select(Project).where(Project.subdomain == slug)
        result = await db.execute(query)
        existing = result.scalars().first()
        if not existing:
            return True
        if current_project_id and existing.id == current_project_id:
            return True
        return False

    async def check_availability(
        self,
        desired_slug: str,
        db: AsyncSession,
        exclude_project_id: Optional[str] = None
    ) -> bool:
        """Convenience alias for checking slug availability."""
        return await self.is_slug_available(db, desired_slug, exclude_project_id)

    async def generate_alternative_slugs(
        self,
        db: AsyncSession,
        base_slug: str,
        count: int = 3
    ) -> List[str]:
        """Generates smart alternative subdomains if preferred slug is taken."""
        alternatives = []
        suffixes = ["design", "official", "hq", "studio", "online", "web", "app", "2"]
        for s in suffixes:
            candidate = f"{base_slug[:50]}-{s}"
            if await self.is_slug_available(db, candidate):
                alternatives.append(candidate)
                if len(alternatives) >= count:
                    break
        return alternatives

    async def get_suggested_slugs(self, base_slug: str, db: AsyncSession, count: int = 3) -> List[str]:
        """Convenience alias for generating alternatives."""
        return await self.generate_alternative_slugs(db, base_slug, count)

    def get_public_url_for_subdomain(self, subdomain: str) -> str:
        """
        Returns the multi-tenant accessible URL for the subdomain.
        Supports both local high-speed routing and custom platform domains.
        """
        host = settings.HOST
        port = settings.PORT
        return f"http://{host}:{port}/site/{subdomain}/index.html"

    def build_subdomain_url(self, subdomain: str) -> str:
        """Convenience alias for building subdomain URL."""
        return self.get_public_url_for_subdomain(subdomain)

    async def resolve_subdomain(self, subdomain: str, db: AsyncSession):
        """Resolves a subdomain slug to its Project record."""
        from backend.app.models.project import Project
        slug = self.normalize_slug(subdomain)
        query = select(Project).where(Project.subdomain == slug)
        res = await db.execute(query)
        return res.scalars().first()

    async def reserve_subdomain(
        self,
        project_id: str,
        desired_slug: str,
        db: AsyncSession
    ) -> Tuple[bool, str, Optional[str]]:
        """Validates and assigns a subdomain slug to a project."""
        from backend.app.models.project import Project
        slug = self.normalize_slug(desired_slug)
        valid, msg = self.validate_slug(slug)
        if not valid:
            return False, slug, msg
        available = await self.is_slug_available(db, slug, current_project_id=project_id)
        if not available:
            return False, slug, f"Subdomain '{slug}' is already taken."
        project = await db.get(Project, project_id)
        if not project:
            return False, slug, "Project not found."
        project.subdomain = slug
        await db.commit()
        return True, slug, None

subdomain_service = SubdomainService()
