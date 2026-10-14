import logging
import urllib.parse
from typing import Dict, Any, List, Optional
from backend.app.schemas.agent import WebsitePlan, AssetManifest, AssetItem
from backend.app.config import settings

logger = logging.getLogger(__name__)

class AssetAgent:
    """
    Asset Agent:
    - Finds verified high-resolution images matching business context.
    - Sources or generates crisp SVG logo matching company branding.
    - Curates Lucide icons for features and navigation.
    - Provides guaranteed inline SVG fallbacks for offline or network-restricted environments.
    """

    AGENT_NAME = "Asset Agent"

    # Curated, verified working high-resolution Unsplash photography by industry category
    INDUSTRY_ASSETS = {
        "technology": {
            "hero": "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=1600&q=80",
            "features": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=1200&q=80",
            "about": "https://images.unsplash.com/photo-1522071820081-009f0129c71c?auto=format&fit=crop&w=1200&q=80",
        },
        "finance": {
            "hero": "https://images.unsplash.com/photo-1460925895917-afdab827c52f?auto=format&fit=crop&w=1600&q=80",
            "features": "https://images.unsplash.com/photo-1559526324-4b87b5e36e44?auto=format&fit=crop&w=1200&q=80",
            "about": "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&w=1200&q=80",
        },
        "healthcare": {
            "hero": "https://images.unsplash.com/photo-1538108149393-fbbd81895907?auto=format&fit=crop&w=1600&q=80",
            "features": "https://images.unsplash.com/photo-1505751172876-fa1923c5c528?auto=format&fit=crop&w=1200&q=80",
            "about": "https://images.unsplash.com/photo-1584515979956-d9f6e5d09982?auto=format&fit=crop&w=1200&q=80",
        },
        "real estate": {
            "hero": "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1600&q=80",
            "features": "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?auto=format&fit=crop&w=1200&q=80",
            "about": "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=1200&q=80",
        },
        "retail": {
            "hero": "https://images.unsplash.com/photo-1441986300917-64674bd600d8?auto=format&fit=crop&w=1600&q=80",
            "features": "https://images.unsplash.com/photo-1472851294608-062f824d29cc?auto=format&fit=crop&w=1200&q=80",
            "about": "https://images.unsplash.com/photo-1555529669-e69e7aa0ba9a?auto=format&fit=crop&w=1200&q=80",
        },
        "consulting": {
            "hero": "https://images.unsplash.com/photo-1552664730-d307ca884978?auto=format&fit=crop&w=1600&q=80",
            "features": "https://images.unsplash.com/photo-1531482615713-2afd69097998?auto=format&fit=crop&w=1200&q=80",
            "about": "https://images.unsplash.com/photo-1600880292203-757bb62b4baf?auto=format&fit=crop&w=1200&q=80",
        },
        "default": {
            "hero": "https://images.unsplash.com/photo-1497366216548-37526070297c?auto=format&fit=crop&w=1600&q=80",
            "features": "https://images.unsplash.com/photo-1497215728101-856f4ea42174?auto=format&fit=crop&w=1200&q=80",
            "about": "https://images.unsplash.com/photo-1542744173-8e7e53415bb0?auto=format&fit=crop&w=1200&q=80",
        }
    }

    def _generate_svg_logo(self, business_name: str, primary_color: str, secondary_color: str) -> str:
        """Generates a clean vector SVG logo mark."""
        initials = "".join([part[0].upper() for part in business_name.split()[:2]]) or "AI"
        svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 50" width="200" height="50" class="h-9 w-auto">
  <defs>
    <linearGradient id="logoGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{primary_color}" />
      <stop offset="100%" stop-color="{secondary_color}" />
    </linearGradient>
  </defs>
  <rect x="2" y="5" width="40" height="40" rx="10" fill="url(#logoGrad)" />
  <text x="22" y="32" font-family="system-ui, -apple-system, sans-serif" font-weight="800" font-size="20" fill="#ffffff" text-anchor="middle">{initials}</text>
  <text x="52" y="32" font-family="system-ui, -apple-system, sans-serif" font-weight="700" font-size="19" fill="{secondary_color}">{business_name[:16]}</text>
</svg>"""
        return svg

    def _generate_fallback_pattern_svg(self, title: str, primary_color: str) -> str:
        """Generates an aesthetic SVG illustration fallback."""
        return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 600" width="100%" height="100%" class="w-full h-full object-cover rounded-xl">
  <defs>
    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{primary_color}" stop-opacity="0.1" />
      <stop offset="100%" stop-color="{primary_color}" stop-opacity="0.25" />
    </linearGradient>
    <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
      <path d="M 40 0 L 0 0 0 40" fill="none" stroke="{primary_color}" stroke-opacity="0.15" stroke-width="1"/>
    </pattern>
  </defs>
  <rect width="800" height="600" fill="url(#bgGrad)" />
  <rect width="800" height="600" fill="url(#grid)" />
  <circle cx="400" cy="300" r="140" fill="{primary_color}" fill-opacity="0.2" />
  <text x="400" y="305" font-family="system-ui, sans-serif" font-weight="600" font-size="24" fill="{primary_color}" text-anchor="middle">{title}</text>
</svg>"""

    async def curate_assets(self, plan: WebsitePlan, user_logo_url: Optional[str] = None) -> AssetManifest:
        """
        Curates imagery, vector logo, and icons corresponding to the website plan.
        """
        industry_key = "default"
        ind_lower = plan.industry.lower()
        for k in self.INDUSTRY_ASSETS:
            if k in ind_lower:
                industry_key = k
                break

        preset = self.INDUSTRY_ASSETS.get(industry_key, self.INDUSTRY_ASSETS["default"])
        p_col = plan.color_scheme.primary
        s_col = plan.color_scheme.secondary

        # Logo asset
        svg_logo_data = self._generate_svg_logo(plan.business_name, p_col, s_col)
        logo_asset = AssetItem(
            id="site-logo",
            type="logo",
            name=f"{plan.business_name} Logo",
            description="Vector brand identity mark",
            url=user_logo_url or f"data:image/svg+xml;utf8,{urllib.parse.quote(svg_logo_data)}",
            fallback_svg=svg_logo_data,
            alt=f"{plan.business_name} Logo",
            source="Generated Brandmark" if not user_logo_url else "User Provided"
        )

        # Curate images for sections
        images = [
            AssetItem(
                id="hero-image",
                type="hero_image",
                name="Hero Visual",
                description=f"High-impact visual for {plan.business_name} hero banner",
                url=preset["hero"],
                fallback_svg=self._generate_fallback_pattern_svg(plan.business_name, p_col),
                alt=f"{plan.business_name} hero photography",
                source="Unsplash CDN"
            ),
            AssetItem(
                id="features-image",
                type="feature_image",
                name="Solutions Overview",
                description="Visual illustrating core offerings and engineering excellence",
                url=preset["features"],
                fallback_svg=self._generate_fallback_pattern_svg("Core Capabilities", p_col),
                alt=f"{plan.business_name} features",
                source="Unsplash CDN"
            ),
            AssetItem(
                id="about-image",
                type="about_image",
                name="Team and Mission",
                description="Workplace culture, executive leadership, and company mission",
                url=preset["about"],
                fallback_svg=self._generate_fallback_pattern_svg("Our Mission", p_col),
                alt=f"About {plan.business_name}",
                source="Unsplash CDN"
            )
        ]

        # Key icons used across sections
        icons = ["ShieldCheck", "Zap", "Headphones", "TrendingUp", "Sparkles", "Mail", "Phone", "MapPin", "ArrowRight", "CheckCircle"]

        return AssetManifest(
            logo=logo_asset,
            images=images,
            icons=icons
        )

asset_agent = AssetAgent()
