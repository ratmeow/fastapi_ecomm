from app.backend.db import Base
from sqlalchemy import Integer, String, Boolean, ForeignKey, Column, Date
import datetime


class Rating(Base):
    __tablename__ = "ratings"

    id = Column(Integer, primary_key=True, index=True)
    grade = Column(Integer)
    user_id = Column(Integer, ForeignKey("users.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    is_active = Column(Boolean, default=True)
