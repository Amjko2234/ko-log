from pydantic import BaseModel, model_validator


class TypeDiscriminationValidatorMixin(BaseModel):
    @model_validator(mode="before")
    @classmethod
    def validate_based_on_type(cls, data: dict[str, object]) -> dict[str, object]:
        """
        Inject the outer `type` into `params` before `Pydantic` runs the
        discriminated-union validation.
        """
        if "params" not in data or "type" not in data:
            return data
        type = data["type"]
        params = data["params"]
        if isinstance(params, dict) and "type" not in params:
            params["type"] = type
            data["params"] = params
        return data
