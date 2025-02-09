from sqlalchemy import Column, Integer, String, Float, Date, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(String(255), unique=True, index=True)
    invoice_number = Column(String(255))
    amount = Column(Float)
    due_date = Column(Date, nullable=True)
    payment_status = Column(String(50))
    discount_rate = Column(Float, nullable=True)
    late_fee = Column(Float, nullable=True)
    grace_period = Column(Integer, nullable=True)
    vendor_name = Column(String(255))
    buyer_name = Column(String(255))
    suggestions = Column(JSON, nullable=True)