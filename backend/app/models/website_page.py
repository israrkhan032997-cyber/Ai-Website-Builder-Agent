from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Integer, ForeignKey, Boolean
from backend.app.database import Base

class WebsitePage(Base):
    __tablename__ = "website_pages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    slug = Column(String(50), nullable=False, index=True) # "index", "about", "services", "portfolio", "contact"
    title = Column(String(150), nullable=False) # "Home", "About Us", "Our Services"
    description = Column(Text, nullable=True)
    file_path = Column(String(100), nullable=False) # "index.html", "about.html"
    is_home = Column(Boolean, default=False)
    nav_order = Column(Integer, default=0)
    order_index = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
