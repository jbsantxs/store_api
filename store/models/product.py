from dataclasses import Field
from datetime import datetime
from store.models.base import CreateBaseModel
from store.schemas.product import ProductIn


class ProductModel(ProductIn, CreateBaseModel):
    name: str
    quantity: int
    price: float
    status: bool
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
