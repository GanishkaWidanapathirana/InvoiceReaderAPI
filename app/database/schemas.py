from pydantic import BaseModel
from typing import Optional, List
from datetime import date


class InvoiceCreate(BaseModel):
    document_id: str
    invoice_number: Optional[str] = None
    amount: Optional[float] = None
    due_date: Optional[date] = None
    payment_status: Optional[str] = None
    discount_rate: Optional[float] = None
    late_fee: Optional[float] = None
    grace_period: Optional[int] = None
    vendor_name: Optional[str] = None
    buyer_name: Optional[str] = None
    suggestions: Optional[List[str]] = []

    class Config:
        from_attributes = True
