from sqlalchemy import Column, Integer, String, Float, Date, JSON, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(String(255), unique=True, index=True)
    invoice_number = Column(String(255), nullable=True)
    amount = Column(String(255), nullable=True)  # Now stored as string
    due_date = Column(String(255), nullable=True)  # Now stored as string
    payment_status = Column(String(50), nullable=True)
    discount_rate = Column(String(255), nullable=True)  # Now stored as string
    late_fee = Column(String(255), nullable=True)  # Now stored as string
    grace_period = Column(String(255), nullable=True)  # Now stored as string
    vendor_name = Column(String(255), nullable=True)
    buyer_name = Column(String(255), nullable=True)
    suggestions = Column(Text, nullable=True)  # Store JSON string
    user_email = Column(String(50), nullable=True)
