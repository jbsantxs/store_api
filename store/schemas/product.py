from datetime import datetime
from decimal import Decimal
from typing import Annotated, Optional
from bson import Decimal128
from pydantic import AfterValidator, Field, BaseModel
from store.schemas.base import BaseSchemaMixin, OutSchema


class ProductBase(BaseSchemaMixin):
    name: str = Field(..., description="Product name")
    quantity: int = Field(..., description="Product quantity")
    price: Decimal = Field(..., description="Product price")
    status: bool = Field(..., description="Product status")


class ProductIn(ProductBase, BaseSchemaMixin):
    ...


class ProductOut(ProductIn, OutSchema):
    ...


def convert_decimal_128(v):
    return Decimal128(str(v))


Decimal_ = Annotated[Decimal, AfterValidator(convert_decimal_128)]


class ProductUpdate(BaseSchemaMixin):
    quantity: Optional[int] = Field(None, description="Product quantity")
    price: Optional[Decimal_] = Field(None, description="Product price")
    status: Optional[bool] = Field(None, description="Product status")
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow, descrption="Last update timestamp")

class ProductUpdateOut(ProductOut):
    ...

class ProductFilters(BaseModel):
    min_price: Optional[Decimal] = Field(None, description="Minimum price filter")
    max_price: Optional[Decimal] = Field(None, description="Maximum price filter")
    name: Optional[str] = Field(None, description="Product name filter")
    status: Optional[bool] = Field(None, description="Product status filter")