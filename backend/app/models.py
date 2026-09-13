from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Date, Float
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False)
    hostel = Column(String, default="Boys Hostel")
    room = Column(String, nullable=True)
    block = Column(String, nullable=True)
    active = Column(Boolean, default=True)

class Attendance(Base):
    __tablename__ = "attendance"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(Date, nullable=False)
    status = Column(String, default="PRESENT")
    checked_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User")

class Complaint(Base):
    __tablename__ = "complaints"
    id = Column(Integer, primary_key=True)
    ticket = Column(String, unique=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    location = Column(String, nullable=False)
    category = Column(String, default="Other")
    priority = Column(String, default="MEDIUM")
    status = Column(String, default="REPORTED")
    assigned_to = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User")

class Request(Base):
    __tablename__ = "requests"
    id = Column(Integer, primary_key=True)
    kind = Column(String, nullable=False) # LEAVE, OUTPASS, CLEANING, HOSPITAL
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    payload = Column(Text, default="{}")
    status = Column(String, default="PENDING")
    urgency = Column(String, default="NORMAL")
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User")

class Notice(Base):
    __tablename__ = "notices"
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    category = Column(String, default="General")
    hostel = Column(String, default="All")
    created_at = Column(DateTime, default=datetime.utcnow)

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message = Column(String, nullable=False)
    read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User")

class Worker(Base):
    __tablename__ = "workers"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    department = Column(String, nullable=False)
    job = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    active = Column(Boolean, default=True)

class FAQ(Base):
    __tablename__ = "faqs"
    id = Column(Integer, primary_key=True)
    question = Column(String, nullable=False)
    answer = Column(Text, nullable=False)
    category = Column(String, default="General")
    published = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class MealRating(Base):
    __tablename__ = "meal_ratings"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    meal_name = Column(String, nullable=False)
    food_quality = Column(Integer, nullable=False)
    taste = Column(Integer, nullable=False)
    quantity = Column(Integer, nullable=False)
    comment = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User")
    
class LostFound(Base):
    __tablename__ = "lost_found"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    kind = Column(String, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    location = Column(String, nullable=False)
    status = Column(String, default="OPEN")
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User")

class HostelAttendance(Base):
    """Verified hostel attendance — GPS + Wi-Fi dual-check session (4 PM – 6 PM)."""
    __tablename__ = "hostel_attendance"
    id               = Column(Integer, primary_key=True)
    user_id          = Column(Integer, ForeignKey("users.id"), nullable=False)
    date             = Column(Date, nullable=False)
    status           = Column(String, default="PENDING")   # PENDING | PRESENT | ABSENT
    marked_time      = Column(DateTime, nullable=True)
    gps_verified     = Column(Boolean, default=False)
    network_verified = Column(Boolean, default=False)
    latitude         = Column(Float, nullable=True)
    longitude        = Column(Float, nullable=True)
    ip_address       = Column(String, nullable=True)
    user             = relationship("User")

