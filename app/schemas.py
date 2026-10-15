from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

class CustomerCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
class LoginInput(BaseModel): email: EmailStr; password: str = Field(min_length=1, max_length=128)
class ForgotPasswordInput(BaseModel): email: EmailStr
class ResetPasswordInput(BaseModel): token: str = Field(min_length=20, max_length=200); new_password: str = Field(min_length=8, max_length=128)
class CustomerOut(BaseModel): model_config = ConfigDict(from_attributes=True); id: int; name: str; email: EmailStr; created_at: datetime
class CustomerPatch(BaseModel): name: str | None = Field(default=None, min_length=2, max_length=120)
class AddressInput(BaseModel):
    label: str = Field(default="Home", max_length=60)
    line1: str = Field(min_length=2, max_length=180)
    line2: str | None = Field(default=None, max_length=180)
    city: str = Field(min_length=2, max_length=100)
    region: str = Field(min_length=2, max_length=100)
    postal_code: str = Field(min_length=3, max_length=24)
    country: str = Field(default="United States", min_length=2, max_length=80)
    is_default: bool = False
class AddressPatch(BaseModel):
    label: str | None = Field(default=None, max_length=60); line1: str | None = Field(default=None, min_length=2, max_length=180); line2: str | None = Field(default=None, max_length=180); city: str | None = Field(default=None, min_length=2, max_length=100); region: str | None = Field(default=None, min_length=2, max_length=100); postal_code: str | None = Field(default=None, min_length=3, max_length=24); country: str | None = Field(default=None, min_length=2, max_length=80); is_default: bool | None = None
class AddressOut(AddressInput): model_config = ConfigDict(from_attributes=True); id: int; customer_id: int
class ProductOut(BaseModel): model_config = ConfigDict(from_attributes=True); id: int; name: str; description: str; category: str; price: float; stock: int; featured: bool
class ReviewOut(BaseModel): model_config = ConfigDict(from_attributes=True); id: int; customer_name: str; rating: int; title: str; body: str; created_at: datetime
class OrderItemInput(BaseModel): product_id: int; quantity: int = Field(ge=1, le=50)
class OrderCreate(BaseModel): items: list[OrderItemInput] = Field(min_length=1, max_length=30); shipping_address: str = Field(min_length=5, max_length=400)
class OrderPatch(BaseModel): shipping_address: str = Field(min_length=5, max_length=400)
class OrderItemOut(BaseModel): model_config = ConfigDict(from_attributes=True); product_id: int; product_name: str; quantity: int; unit_price: float
class OrderOut(BaseModel): model_config = ConfigDict(from_attributes=True); id: int; customer_id: int; status: str; payment_status: str; total: float; created_at: datetime; shipping_address: str; items: list[OrderItemOut]
class TokenOut(BaseModel): access_token: str; token_type: str = "bearer"; expires_in: int
class MessageOut(BaseModel): message: str
