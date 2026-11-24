from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.operations import CalculationType


class CalculationCreate(BaseModel):
    type: CalculationType = Field(examples=["add"])
    a: float = Field(examples=[10])
    b: float = Field(examples=[5])

    @model_validator(mode="after")
    def no_divide_by_zero(self):
        if self.type == CalculationType.divide and self.b == 0:
            raise ValueError("Cannot divide by zero")
        return self


class CalculationUpdate(BaseModel):
    """All fields optional; the result is recomputed on the server."""
    type: CalculationType | None = None
    a: float | None = None
    b: float | None = None

    @model_validator(mode="after")
    def at_least_one_field(self):
        if self.type is None and self.a is None and self.b is None:
            raise ValueError("Provide at least one of: type, a, b")
        return self


class CalculationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: CalculationType
    a: float
    b: float
    result: float
    user_id: int
    created_at: datetime
    updated_at: datetime
