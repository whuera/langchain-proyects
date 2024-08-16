import os
from typing import Any, Dict, Optional

from ai21 import AI21Client
from langchain_core.pydantic_v1 import BaseModel, Field, SecretStr, root_validator
from langchain_core.utils import convert_to_secret_str

_DEFAULT_TIMEOUT_SEC = 300


class AI21Base(BaseModel):
    """Base class for AI21 models."""

    class Config:
        arbitrary_types_allowed = True

    client: Any = Field(default=None, exclude=True)  #: :meta private:
    api_key: Optional[SecretStr] = None
    """API key for AI21 API."""
    api_host: Optional[str] = None
    """Host URL"""
    timeout_sec: Optional[float] = None
    """Timeout in seconds.
    
    If not set, it will default to the value of the environment 
    variable `AI21_TIMEOUT_SEC` or 300 seconds.
    """
    num_retries: Optional[int] = None
    """Maximum number of retries for API requests before giving up."""

    @root_validator(pre=True)
    def validate_environment(cls, values: Dict) -> Dict:
        api_key = convert_to_secret_str(
            values.get("api_key") or os.getenv("AI21_API_KEY") or ""
        )
        values["api_key"] = api_key

        api_host = (
            values.get("api_host")
            or os.getenv("AI21_API_URL")
            or "https://api.ai21.com"
        )
        values["api_host"] = api_host

        timeout_sec = values.get("timeout_sec") or float(
            os.getenv("AI21_TIMEOUT_SEC", _DEFAULT_TIMEOUT_SEC)
        )
        values["timeout_sec"] = timeout_sec
        return values

    @root_validator(pre=False, skip_on_failure=True)
    def post_init(cls, values: Dict) -> Dict:
        api_key = values["api_key"]
        api_host = values["api_host"]
        timeout_sec = values["timeout_sec"]
        if values.get("client") is None:
            values["client"] = AI21Client(
                api_key=api_key.get_secret_value(),
                api_host=api_host,
                timeout_sec=None if timeout_sec is None else float(timeout_sec),
                via="langchain",
            )

        return values
