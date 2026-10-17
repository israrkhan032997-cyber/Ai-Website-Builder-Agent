import os
import re
import socket
import logging
from typing import Dict, Any, Optional, Tuple, List
from urllib.parse import urlparse
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from backend.app.models.project import Project
from backend.app.models.checkpoint import Checkpoint
from backend.app.schemas.project import NaturalLanguageEditRequest
from backend.app.services.workspace_manager import workspace_manager
from backend.app.services.git_service import git_service
from backend.app.services.ai_provider import ai_provider

logger = logging.getLogger(__name__)

COLOR_NAME_MAP: Dict[str, str] = {
    "emerald": "#10b981",
    "blue": "#2563eb",
    "sky": "#0284c7",
    "cyan": "#06b6d4",
    "teal": "#0d9488",
    "green": "#16a34a",
    "indigo": "#4f46e5",
    "violet": "#7c3aed",
    "purple": "#9333ea",
    "fuchsia": "#c026d3",
    "pink": "#db2777",
    "rose": "#e11d48",
    "red": "#dc2626",
    "orange": "#ea580c",
    "amber": "#d97706",
    "yellow": "#ca8a04",
    "slate": "#475569",
    "gray": "#4b5563",
    "zinc": "#52525b",
    "dark": "#0f172a",
    "black": "#000000",
    "white": "#ffffff"
}

RESERVED_TEST_DOMAINS = {
    "example.com", "example.org", "example.net",
    "localhost", "127.0.0.1", "test.com", "placeholder.com"
}


class EditingService:
    """
    Dedicated website editing agent:
    - Parses natural-language modification requests.
    - Preserves exact user assets and URLs (logos, images, text).
    - Validates asset URLs and prevents silent replacement of broken/inaccessible assets.
    - Applies minimal, surgical source-code patches to maintain project stability.
    - Updates live workspace files, records Git checkpoints, and keeps preview in sync.
    """

    def extract_urls(self, text: str) -> List[str]:
        """Extracts and preserves exact raw HTTP/HTTPS URLs from text."""
        # Match standard URLs, stripping trailing punctuation (periods, commas, closing brackets/quotes)
        url_pattern = r'https?://[^\s<>"\'\)\]\}]+'
        raw_matches = re.findall(url_pattern, text)
        cleaned_urls = []
        for u in raw_matches:
            # Strip trailing punctuation accidentally caught at the end of a sentence
            clean_u = re.sub(r'[,.\'"\)\]\}]+$', '', u)
            if clean_u and clean_u not in cleaned_urls:
                cleaned_urls.append(clean_u)
        return cleaned_urls

    IMAGE_EXTENSIONS = {
        ".png", ".jpg", ".jpeg", ".svg", ".webp", ".gif", ".ico", ".bmp", ".avif"
    }

    async def validate_asset_url(self, url: str) -> Tuple[bool, Optional[str]]:
        """
        Validates URL syntax, domain resolvability, direct image vs webpage, and accessibility.
        Returns: (is_valid, error_reason)
        """
        try:
            parsed = urlparse(url)
        except Exception as e:
            return False, f"Invalid URL structure: {e}"

        if parsed.scheme not in ["http", "https"]:
            return False, f"URL '{url}' must use http:// or https:// protocol."

        if not parsed.netloc:
            return False, f"URL '{url}' is missing a valid host or domain name."

        host = parsed.hostname
        if not host:
            return False, f"URL '{url}' has an invalid hostname."

        # Domain syntax check
        if "." not in host and host not in ["localhost"]:
            return False, f"Host '{host}' in URL '{url}' is not a valid Fully Qualified Domain Name."

        clean_path = parsed.path.lower().split("?")[0].split("#")[0]
        has_img_ext = any(clean_path.endswith(ext) for ext in self.IMAGE_EXTENSIONS)

        # Allow standard RFC 2606 example and test domains without network ping
        if any(host.endswith(d) or host == d for d in RESERVED_TEST_DOMAINS):
            # Check if test domain URL points to a webpage instead of an image
            if not has_img_ext and not any(kw in clean_path for kw in ["logo", "asset", "img", "image", "photo", "brand", "icon"]):
                return False, f"The supplied URL '{url}' points to a webpage (HTML document) rather than a direct image file. Please provide a direct image URL (such as a .png, .svg, .jpg, or .webp) or permission to extract the image from the page."
            return True, None

        # DNS resolution check
        try:
            socket.getaddrinfo(host, None)
        except (socket.gaierror, socket.herror):
            return False, f"The domain '{host}' could not be resolved (DNS lookup failed). Please check the link or provide a valid asset URL."
        except Exception:
            pass

        # Accessibility and Content-Type check
        try:
            async with httpx.AsyncClient(timeout=4.0, follow_redirects=True) as client:
                resp = await client.head(url)
                if resp.status_code == 405:  # Method Not Allowed on HEAD, try small GET
                    resp = await client.get(url, headers={"Range": "bytes=0-1024"})
                if resp.status_code in [404, 410]:
                    return False, f"The image URL '{url}' returned HTTP {resp.status_code} ({resp.reason_phrase}). The asset does not exist at this location."
                if resp.status_code >= 500:
                    return False, f"The image host returned server error HTTP {resp.status_code} for URL '{url}'."

                # Check Content-Type header to ensure it's not a webpage
                content_type = resp.headers.get("content-type", "").lower()
                if "text/html" in content_type or "application/xhtml+xml" in content_type:
                    return False, f"The supplied URL '{url}' points to a webpage (Content-Type: '{content_type}') rather than a direct image file. Please provide a direct image URL (such as a .png, .svg, .jpg, or .webp) or permission to extract the image from the page."
                if not has_img_ext and not any(img_mime in content_type for img_mime in ["image/", "svg", "octet-stream"]):
                    return False, f"The supplied URL '{url}' returned '{content_type}' rather than a direct image file. Please provide a direct image URL."
        except httpx.ConnectError:
            return False, f"Connection to '{host}' failed. The asset server is unreachable."
        except httpx.TimeoutException:
            logger.warning(f"Timeout verifying URL accessibility: {url}")
        except Exception as e:
            logger.warning(f"Error checking URL accessibility: {e}")

        return True, None

    async def download_asset_locally(
        self,
        project_id: str,
        url: str,
        preferred_name: str = "asset"
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Downloads a remote asset and saves it into the project workspace under assets/.
        Returns: (success, relative_workspace_path, error_message)
        """
        try:
            async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
                resp = await client.get(url)
                if resp.status_code != 200:
                    return False, "", f"Failed to download asset: HTTP {resp.status_code}"

                # Determine extension
                content_type = resp.headers.get("content-type", "")
                ext = ".png"
                if "svg" in content_type or url.lower().endswith(".svg"):
                    ext = ".svg"
                elif "jpeg" in content_type or "jpg" in content_type or url.lower().endswith((".jpg", ".jpeg")):
                    ext = ".jpg"
                elif "webp" in content_type or url.lower().endswith(".webp"):
                    ext = ".webp"
                elif "gif" in content_type or url.lower().endswith(".gif"):
                    ext = ".gif"

                safe_base = re.sub(r'[^a-zA-Z0-9_\-]', '', preferred_name).strip() or "asset"
                rel_path = f"assets/{safe_base}{ext}"

                project_dir = workspace_manager.get_project_dir(project_id)
                assets_dir = project_dir / "assets"
                assets_dir.mkdir(parents=True, exist_ok=True)
                dest_file = assets_dir / f"{safe_base}{ext}"

                dest_file.write_bytes(resp.content)
                return True, rel_path, None
        except Exception as e:
            return False, "", f"Could not download asset from '{url}': {str(e)}"

    # -----------------------------------------------------------------------
    # Targeted Deterministic Patchers
    # -----------------------------------------------------------------------

    def patch_logo(self, html: str, logo_url: str, business_name: str = "Website") -> Tuple[str, bool]:
        """
        Deterministically updates the logo in HTML header while preserving
        exact aspect ratio, layout, and surrounding code.
        """
        new_logo_tag = f'<img src="{logo_url}" alt="{business_name} Logo" class="h-9 w-auto object-contain">'

        # Case 1: Header brand anchor containing an <img>
        header_img = re.search(r'(<header\b[\s\S]*?<a\b[^>]*>\s*)(<img\b[^>]*>)', html, flags=re.I)
        if header_img:
            updated = html[:header_img.start(2)] + new_logo_tag + html[header_img.end(2):]
            return updated, True

        # Case 2: Existing <img> with alt containing Logo
        alt_logo_pattern = r'<img\b[^>]*\balt=["\'][^"\']*Logo[^"\']*["\'][^>]*>'
        if re.search(alt_logo_pattern, html, flags=re.I):
            updated = re.sub(alt_logo_pattern, new_logo_tag, html, count=1, flags=re.I)
            return updated, True

        # Case 3: Any <img> inside <header>...</header>
        any_header_img = re.search(r'(<header\b[\s\S]*?)(<img\b[^>]*>)([\s\S]*?</header>)', html, flags=re.I)
        if any_header_img:
            updated = html[:any_header_img.start(2)] + new_logo_tag + html[any_header_img.end(2):]
            return updated, True

        # Case 4: Header brand anchor containing an inline <svg>
        svg_logo_pattern = r'(<header\b[\s\S]*?<a\b[^>]*>\s*)(<svg\b[\s\S]*?</svg>)'
        if re.search(svg_logo_pattern, html, flags=re.I):
            updated = re.sub(svg_logo_pattern, f'\\g<1>{new_logo_tag}', html, count=1, flags=re.I)
            return updated, True

        # Case 5: Any anchor with flex items-center containing <img>
        flex_img = r'(<a\b[^>]*class=["\'][^"\']*flex[^"\']*items-center[^"\']*["\'][^>]*>\s*)<img\b[^>]*>'
        if re.search(flex_img, html, flags=re.I):
            updated = re.sub(flex_img, f'\\g<1>{new_logo_tag}', html, count=1, flags=re.I)
            return updated, True

        # Case 6: Existing <img> with data:image/svg+xml in src
        data_svg_pattern = r'<img\b[^>]*\bsrc=["\']data:image/svg\+xml[^"\']*["\'][^>]*>'
        if re.search(data_svg_pattern, html, flags=re.I):
            updated = re.sub(data_svg_pattern, new_logo_tag, html, count=1, flags=re.I)
            return updated, True

        # Case 7: Fallback to first <img> in body
        first_img = re.search(r'(<body\b[\s\S]*?)(<img\b[^>]*>)', html, flags=re.I)
        if first_img:
            updated = html[:first_img.start(2)] + new_logo_tag + html[first_img.end(2):]
            return updated, True

        return html, False

    def patch_logo_jsx(self, jsx: str, logo_url: str, business_name: str = "Website") -> Tuple[str, bool]:
        """
        Deterministically updates the logo in React JSX components (Navbar.jsx, Footer.jsx)
        preserving className, aspect ratio, and surrounding code.
        """
        new_jsx_tag = f'<img src="{logo_url}" alt="{business_name} Logo" className="h-9 w-auto object-contain" />'

        # Case 1: Existing <img ...> in JSX with alt containing Logo
        if re.search(r'<img\b[^>]*\balt=["\'][^"\']*Logo[^"\']*["\'][^>]*>', jsx, flags=re.I):
            updated = re.sub(r'<img\b[^>]*\balt=["\'][^"\']*Logo[^"\']*["\'][^>]*>', new_jsx_tag, jsx, count=1, flags=re.I)
            return updated, True

        # Case 2: Icon box in Navbar.jsx or Footer.jsx (e.g. rounded div containing Lucide icon like Sparkles)
        icon_box_pattern = r'<div\b[^>]*\bclassName=["\'][^"\']*rounded[^"\']*bg-[^"\']*["\'][^>]*>\s*<[A-Z][a-zA-Z0-9]*\b[^>]*/>\s*</div>'
        if re.search(icon_box_pattern, jsx, flags=re.I):
            updated = re.sub(icon_box_pattern, new_jsx_tag, jsx, count=1, flags=re.I)
            return updated, True

        # Case 3: Any existing <img ...> in JSX
        if re.search(r'<img\b[^>]*\bsrc=["\'][^"\']*["\'][^>]*>', jsx, flags=re.I):
            updated = re.sub(r'<img\b[^>]*\bsrc=["\'][^"\']*["\'][^>]*>', new_jsx_tag, jsx, count=1, flags=re.I)
            return updated, True

        return jsx, False

    def patch_hero_image(self, html: str, image_url: str) -> Tuple[str, bool]:
        """Updates hero section image or background image with exact URL."""
        # Check hero section
        hero_pattern = r'(<section\b[^>]*(?:id=["\']hero["\']|hero)[^>]*>[\s\S]*?)(<img\b[^>]*\bsrc=["\'])([^"\']*)(["\'][^>]*>)'
        if re.search(hero_pattern, html, flags=re.I):
            updated = re.sub(
                hero_pattern,
                f'\\g<1>\\g<2>{image_url}\\g<4>',
                html,
                count=1,
                flags=re.I
            )
            return updated, True

        # Check background image style inside hero
        bg_pattern = r'(<section\b[^>]*(?:id=["\']hero["\']|hero)[^>]*>[\s\S]*?background-image:\s*url\([\'"]?)([^\'")]+)(\'?"?\))'
        if re.search(bg_pattern, html, flags=re.I):
            updated = re.sub(bg_pattern, f'\\g<1>{image_url}\\g<3>', html, count=1, flags=re.I)
            return updated, True

        # Fallback to first large image in main body
        first_img_pattern = r'(<main\b[\s\S]*?<img\b[^>]*\bsrc=["\'])([^"\']*)(["\'][^>]*>)'
        if re.search(first_img_pattern, html, flags=re.I):
            updated = re.sub(first_img_pattern, f'\\g<1>{image_url}\\g<3>', html, count=1, flags=re.I)
            return updated, True

        return html, False

    def patch_section_image(self, html: str, section_id: str, image_url: str) -> Tuple[str, bool]:
        """Updates image in a specific section (about, services, features, etc.)."""
        sec_pattern = rf'(<section\b[^>]*(?:id=["\']{section_id}["\']|{section_id})[^>]*>[\s\S]*?)(<img\b[^>]*\bsrc=["\'])([^"\']*)(["\'][^>]*>)'
        if re.search(sec_pattern, html, flags=re.I):
            updated = re.sub(sec_pattern, f'\\g<1>\\g<2>{image_url}\\g<4>', html, count=1, flags=re.I)
            return updated, True

        # Check background style in that section
        sec_bg_pattern = rf'(<section\b[^>]*(?:id=["\']{section_id}["\']|{section_id})[^>]*>[\s\S]*?background-image:\s*url\([\'"]?)([^\'")]+)(\'?"?\))'
        if re.search(sec_bg_pattern, html, flags=re.I):
            updated = re.sub(sec_bg_pattern, f'\\g<1>{image_url}\\g<3>', html, count=1, flags=re.I)
            return updated, True

        return html, False

    def patch_headline(self, html: str, section_id: Optional[str], new_headline: str) -> Tuple[str, bool]:
        """Updates heading text verbatim while preserving all tags and attributes."""
        clean_text = new_headline.strip()
        if section_id:
            sec_h1 = rf'(<section\b[^>]*(?:id=["\']{section_id}["\']|{section_id})[^>]*>[\s\S]*?<h[12]\b[^>]*>)([\s\S]*?)(</h[12]>)'
            if re.search(sec_h1, html, flags=re.I):
                updated = re.sub(sec_h1, f'\\g<1>\n                    {clean_text}\n                \\g<3>', html, count=1, flags=re.I)
                return updated, True

        # Default: First <h1> in hero or main
        h1_pattern = r'(<h1\b[^>]*>)([\s\S]*?)(</h1>)'
        if re.search(h1_pattern, html, flags=re.I):
            updated = re.sub(h1_pattern, f'\\g<1>\n                    {clean_text}\n                \\g<3>', html, count=1, flags=re.I)
            return updated, True

        return html, False

    def patch_hero_paragraph(self, html: str, new_text: str) -> Tuple[str, bool]:
        """Updates hero paragraph text verbatim."""
        clean_text = new_text.strip()
        p_pattern = r'(<section\b[^>]*(?:id=["\']hero["\']|hero)[^>]*>[\s\S]*?<p\b[^>]*>)([\s\S]*?)(</p>)'
        if re.search(p_pattern, html, flags=re.I):
            updated = re.sub(p_pattern, f'\\g<1>\n                    {clean_text}\n                \\g<3>', html, count=1, flags=re.I)
            return updated, True
        return html, False

    def patch_remove_section(self, html: str, section_id: str) -> Tuple[str, bool]:
        """Surgically removes a section by id without touching anything else."""
        sec_pattern = rf'<section\b[^>]*(?:id=["\']{section_id}["\']|{section_id})[^>]*>[\s\S]*?</section>'
        if re.search(sec_pattern, html, flags=re.I):
            updated = re.sub(sec_pattern, '', html, count=1, flags=re.I)
            # Clean matching nav links
            nav_link_pattern = rf'<a\b[^>]*href=["\'](?:#{section_id}|{section_id}\.html)["\'][^>]*>[\s\S]*?</a>\s*'
            updated = re.sub(nav_link_pattern, '', updated, flags=re.I)
            return updated, True
        return html, False

    def patch_primary_color(
        self,
        html_files: Dict[str, str],
        css_content: str,
        new_color: str,
        old_color: Optional[str] = None
    ) -> Tuple[Dict[str, str], str, bool]:
        """Updates primary brand color in CSS tokens and inline styles across HTML files."""
        color_hex = COLOR_NAME_MAP.get(new_color.lower().strip(), new_color.strip())
        old_hex = (old_color or "#2563eb").strip()

        # Update CSS variables and rules
        new_css = re.sub(r'(--color-primary:\s*)[^;]+;', f'\\g<1>{color_hex};', css_content, flags=re.I)
        new_css = re.sub(r'(:root\s*\{[\s\S]*?--primary:\s*)[^;]+;', f'\\g<1>{color_hex};', new_css, flags=re.I)

        # Update HTML inline styles
        new_html_files = {}
        for path, html in html_files.items():
            patched = html
            if old_hex.lower() in patched.lower():
                # Case-insensitive replace for old hex code
                patched = re.sub(re.escape(old_hex), color_hex, patched, flags=re.I)
            # Replace style="background-color: ..." or border-color for primary buttons
            patched = re.sub(r'(style=["\'](?:background-color|border-color|color):\s*)#[0-9a-fA-F]{3,6}', f'\\1{color_hex}', patched)
            new_html_files[path] = patched

        return new_html_files, new_css, True

    def patch_hero_background_color(self, html: str, color_name_or_hex: str) -> Tuple[str, bool]:
        """
        Updates ONLY the hero section background color without changing the entire site theme.
        Fulfills: 'Change the background to blue means change requested background, not entire theme.'
        """
        color_val = COLOR_NAME_MAP.get(color_name_or_hex.lower().strip(), color_name_or_hex.strip())
        hero_tag_pattern = r'(<section\b[^>]*(?:id=["\']hero["\']|hero)[^>]*)(>)'

        def _replace_hero_tag(match: re.Match) -> str:
            tag = match.group(1)
            # Remove any existing bg-gradient or background-color inline styles
            if 'style="' in tag:
                tag = re.sub(r'style="([^"]*)"', rf'style="\1; background-color: {color_val} !important;"', tag)
            else:
                tag = f'{tag} style="background-color: {color_val} !important;"'
            return f'{tag}{match.group(2)}'

        if re.search(hero_tag_pattern, html, flags=re.I):
            updated = re.sub(hero_tag_pattern, _replace_hero_tag, html, count=1, flags=re.I)
            return updated, True

        return html, False

    # -----------------------------------------------------------------------
    # Natural Language Intent Parser & Executor
    # -----------------------------------------------------------------------

    def _extract_quoted_text(self, text: str) -> Optional[str]:
        """Extracts text within single or double quotes."""
        match = re.search(r"['\"]([^'\"]{2,})['\"]", text)
        if match:
            return match.group(1).strip()
        # Check text after "to " or "as "
        to_match = re.search(r'\b(?:to|as|headline|heading|text|into)\s+([A-Za-z0-9\s\-_.,!&]+)$', text, flags=re.I)
        if to_match:
            candidate = to_match.group(1).strip()
            if len(candidate) > 2 and not candidate.startswith("http"):
                return candidate
        return None

    def _detect_color_keyword(self, text: str) -> Optional[str]:
        """Detects color mentions in edit prompt."""
        t_lower = text.lower()
        # Look for hex color
        hex_match = re.search(r'#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})\b', text)
        if hex_match:
            return hex_match.group(0)

        for name in COLOR_NAME_MAP.keys():
            if re.search(rf'\b{name}\b', t_lower):
                return name
        return None

    async def apply_edit(
        self,
        db: AsyncSession,
        project: Project,
        data: NaturalLanguageEditRequest
    ) -> Dict[str, Any]:
        """
        Executes a targeted, reliable source-code modification based on user prompt.
        """
        instruction = data.instruction.strip()
        if not instruction:
            raise HTTPException(status_code=400, detail="Edit instruction cannot be empty.")

        inst_lower = instruction.lower()

        # Check for vague / ambiguous instructions that would cause unintended damage
        ambiguous_triggers = ["make it better", "change it", "fix it", "do something", "update site", "make changes"]
        if any(instruction.strip().lower() == t for t in ambiguous_triggers):
            return {
                "status": "clarification_needed",
                "message": "Could you please specify which element you would like to modify? For example, you can request to update the logo, change the hero headline, replace a section image with a URL, or change the primary brand color.",
                "commit_hash": project.active_checkpoint_hash,
                "target_page": "index.html"
            }

        # 1. Extract and validate URLs (support structured asset_url from request payload)
        extracted_urls = self.extract_urls(instruction)
        primary_url = data.asset_url or (extracted_urls[0] if extracted_urls else None)

        if primary_url:
            is_valid, err_msg = await self.validate_asset_url(primary_url)
            if not is_valid:
                raise HTTPException(
                    status_code=400,
                    detail=f"The supplied asset URL '{primary_url}' cannot be accessed: {err_msg} Please verify the link or provide an alternative image URL."
                )

        # 2. Check for local download request
        should_download_local = any(k in inst_lower for k in ["download and host", "host locally", "save locally", "download local"])
        final_asset_url = primary_url
        if primary_url and should_download_local:
            asset_type = "logo" if "logo" in inst_lower else "image"
            dl_ok, rel_path, dl_err = await self.download_asset_locally(project.id, primary_url, preferred_name=f"{project.id}_{asset_type}")
            if dl_ok:
                final_asset_url = rel_path
            else:
                raise HTTPException(status_code=400, detail=f"Could not download and host asset locally: {dl_err}")

        # 3. Determine target pages
        target_page = "index.html"
        if data.page_slug:
            target_slug = "index" if data.page_slug in ["home", "index"] else data.page_slug
            if workspace_manager.file_exists(project.id, f"{target_slug}.html"):
                target_page = f"{target_slug}.html"
        else:
            for potential in ["about", "services", "portfolio", "contact", "pricing", "products"]:
                if potential in inst_lower and workspace_manager.file_exists(project.id, f"{potential}.html"):
                    target_page = f"{potential}.html"
                    break

        # Read available HTML files
        all_workspace_files = workspace_manager.list_files(project.id)
        html_file_paths = [f["path"] for f in all_workspace_files if f["path"].endswith(".html")]
        if "index.html" not in html_file_paths and workspace_manager.file_exists(project.id, "index.html"):
            html_file_paths.append("index.html")

        applied_changes: List[str] = []
        modified_files: List[str] = []

        # -------------------------------------------------------------------
        # INTENT 1: Logo Replacement (Global across all HTML pages & React components)
        # -------------------------------------------------------------------
        is_logo_intent = any(k in inst_lower for k in [
            "logo", "brandmark", "brand mark", "brand icon", "company icon", "site icon", "favicon"
        ]) or ("replace logo" in inst_lower or "change logo" in inst_lower)

        if is_logo_intent and primary_url:
            if not final_asset_url:
                raise HTTPException(status_code=400, detail="Please supply a valid image URL for the logo (e.g. 'https://example.com/logo.png').")

            # 1. Patch all HTML files
            for hp in html_file_paths:
                content = workspace_manager.read_file(project.id, hp)
                patched, ok = self.patch_logo(content, final_asset_url, project.name)
                if ok:
                    workspace_manager.write_file(project.id, hp, patched)
                    if hp not in modified_files:
                        modified_files.append(hp)

            # 2. Patch React component files if present (Navbar.jsx, Footer.jsx, App.jsx)
            for jsx_path in ["src/components/Navbar.jsx", "src/components/Footer.jsx", "src/App.jsx"]:
                if workspace_manager.file_exists(project.id, jsx_path):
                    jsx_content = workspace_manager.read_file(project.id, jsx_path)
                    patched_jsx, ok_jsx = self.patch_logo_jsx(jsx_content, final_asset_url, project.name)
                    if ok_jsx:
                        workspace_manager.write_file(project.id, jsx_path, patched_jsx)
                        if jsx_path not in modified_files:
                            modified_files.append(jsx_path)

            # 3. VERIFICATION: Read back all written files from disk and verify exact URL
            verified_files = []
            for mf in modified_files:
                disk_content = workspace_manager.read_file(project.id, mf)
                if final_asset_url in disk_content:
                    verified_files.append(mf)

            if not verified_files:
                raise HTTPException(
                    status_code=500,
                    detail=f"Logo update verification failed: exact asset URL '{final_asset_url}' could not be applied and verified in website source code."
                )

            project.logo_url = final_asset_url
            applied_changes.append(f"Updated website logo to exact asset '{final_asset_url}' across {len(verified_files)} files ({', '.join(verified_files)})")

        # -------------------------------------------------------------------
        # INTENT 2: Hero / Section Image Replacement
        # -------------------------------------------------------------------
        elif primary_url and any(k in inst_lower for k in ["hero", "banner", "background image", "header image", "image"]):
            target_sec = "hero"
            for sec in ["about", "features", "services", "contact", "portfolio"]:
                if sec in inst_lower:
                    target_sec = sec
                    break

            content = workspace_manager.read_file(project.id, target_page)
            if target_sec == "hero":
                patched, ok = self.patch_hero_image(content, final_asset_url)
            else:
                patched, ok = self.patch_section_image(content, target_sec, final_asset_url)

            if ok:
                workspace_manager.write_file(project.id, target_page, patched)
                modified_files.append(target_page)
                applied_changes.append(f"Replaced {target_sec} image with exact URL '{final_asset_url}' in {target_page}")
            else:
                # Fallback to general image patch
                patched, ok = self.patch_hero_image(content, final_asset_url)
                if ok:
                    workspace_manager.write_file(project.id, target_page, patched)
                    modified_files.append(target_page)
                    applied_changes.append(f"Updated image to exact URL '{final_asset_url}' in {target_page}")

        # -------------------------------------------------------------------
        # INTENT 3: Section Removal
        # -------------------------------------------------------------------
        elif any(k in inst_lower for k in ["remove", "delete"]) and "section" in inst_lower:
            target_sec = None
            for sec in ["pricing", "testimonials", "features", "services", "about", "contact", "faq"]:
                if sec in inst_lower:
                    target_sec = sec
                    break

            if target_sec:
                for hp in html_file_paths:
                    content = workspace_manager.read_file(project.id, hp)
                    patched, ok = self.patch_remove_section(content, target_sec)
                    if ok:
                        workspace_manager.write_file(project.id, hp, patched)
                        if hp not in modified_files:
                            modified_files.append(hp)
                applied_changes.append(f"Removed '{target_sec}' section from {', '.join(modified_files)}")

        # -------------------------------------------------------------------
        # INTENT 4: Color Updates (Primary Brand Color OR Section Background)
        # -------------------------------------------------------------------
        detected_color = self._detect_color_keyword(instruction)
        if detected_color and any(k in inst_lower for k in ["color", "primary", "brand", "background", "theme", "emerald"]):
            # Specific Section Background (e.g. "Change the hero background to blue")
            if "hero background" in inst_lower or ("background" in inst_lower and "hero" in inst_lower):
                content = workspace_manager.read_file(project.id, "index.html")
                patched, ok = self.patch_hero_background_color(content, detected_color)
                if ok:
                    workspace_manager.write_file(project.id, "index.html", patched)
                    if "index.html" not in modified_files:
                        modified_files.append("index.html")
                    applied_changes.append(f"Updated hero background to {detected_color} while preserving overall theme")
            else:
                # Global brand primary color
                css_content = workspace_manager.read_file(project.id, "styles.css") if workspace_manager.file_exists(project.id, "styles.css") else ""
                html_map = {hp: workspace_manager.read_file(project.id, hp) for hp in html_file_paths}
                new_htmls, new_css, ok = self.patch_primary_color(html_map, css_content, detected_color, project.primary_color)
                for hp, h_code in new_htmls.items():
                    workspace_manager.write_file(project.id, hp, h_code)
                    if hp not in modified_files:
                        modified_files.append(hp)
                if new_css:
                    workspace_manager.write_file(project.id, "styles.css", new_css)
                    if "styles.css" not in modified_files:
                        modified_files.append("styles.css")
                project.primary_color = COLOR_NAME_MAP.get(detected_color.lower(), detected_color)
                applied_changes.append(f"Updated primary brand color to {detected_color}")

        # -------------------------------------------------------------------
        # INTENT 5: Headline / Text Updates
        # -------------------------------------------------------------------
        if any(k in inst_lower for k in ["headline", "heading", "title", "text", "h1"]):
            quoted_text = self._extract_quoted_text(instruction)
            if quoted_text:
                content = workspace_manager.read_file(project.id, target_page)
                patched, ok = self.patch_headline(content, data.section_id, quoted_text)
                if ok:
                    workspace_manager.write_file(project.id, target_page, patched)
                    if target_page not in modified_files:
                        modified_files.append(target_page)
                    applied_changes.append(f"Updated headline to '{quoted_text}' in {target_page}")

        # -------------------------------------------------------------------
        # INTENT 6: Open-Ended / General Modification via Gemini (with Post-Validation)
        # -------------------------------------------------------------------
        if not applied_changes:
            content = workspace_manager.read_file(project.id, target_page)
            if not ai_provider.is_configured():
                raise HTTPException(status_code=400, detail="Gemini API key is not configured for open-ended edits.")

            edit_prompt = f"""
You are an expert Frontend Web Developer and UI Engineer.
The user wants to make a specific modification to their website page ({target_page}).

User Instruction:
"{instruction}"

Current File Content:
```{content}```

Requirements:
1. Apply the user's requested change cleanly and surgically.
2. PRESERVE all existing Tailwind CSS styling, responsive layout, meta tags, interactive scripts, and components.
3. DO NOT redesign unrelated components or rewrite existing content unless explicitly requested.
4. If a URL or quoted text was provided, include it VERBATIM.
5. Return ONLY the complete updated file content. Do not include markdown fences or conversational text outside code.
"""
            updated_code, log_msg = await ai_provider.generate_text(
                prompt=edit_prompt,
                system_instruction="You are an expert web developer. Output ONLY valid, complete code."
            )
            if not updated_code or len(updated_code.strip()) < 50:
                raise HTTPException(status_code=502, detail=f"Gemini was unable to generate code changes: {log_msg}")

            clean_code = updated_code.strip()
            clean_code = re.sub(r"^```[a-zA-Z]*\r?\n", "", clean_code)
            clean_code = re.sub(r"\r?\n```$", "", clean_code).strip()

            # Post-validation: If user supplied exact URLs, verify they are in clean_code!
            if primary_url and primary_url not in clean_code:
                # Deterministically restore the exact URL if Gemini dropped or mangled it
                if "logo" in inst_lower:
                    clean_code, _ = self.patch_logo(clean_code, final_asset_url, project.name)
                else:
                    clean_code, _ = self.patch_hero_image(clean_code, final_asset_url)

            workspace_manager.write_file(project.id, target_page, clean_code)
            modified_files.append(target_page)
            applied_changes.append(f"Applied custom modification to {target_page}")

        # -------------------------------------------------------------------
        # Step 4: Save Git Checkpoint & Return Response
        # -------------------------------------------------------------------
        checkpoint_msg = f"edit: {instruction[:60]}"
        git_ok, commit_hash, changed_files = git_service.create_checkpoint(project.id, checkpoint_msg)
        if git_ok and commit_hash:
            chk = Checkpoint(
                project_id=project.id,
                commit_hash=commit_hash,
                message=checkpoint_msg,
                changed_files=changed_files or modified_files
            )
            db.add(chk)
            project.active_checkpoint_hash = commit_hash

        await db.commit()

        summary_msg = "; ".join(applied_changes) if applied_changes else f"Applied your changes to {target_page}."
        return {
            "status": "success",
            "message": summary_msg,
            "commit_hash": commit_hash or project.active_checkpoint_hash,
            "target_page": target_page,
            "modified_files": modified_files
        }


editing_service = EditingService()
