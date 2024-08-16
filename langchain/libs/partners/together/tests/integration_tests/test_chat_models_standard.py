"""Standard LangChain interface tests"""

from typing import Type

import pytest
from langchain_core.language_models import BaseChatModel
from langchain_core.rate_limiters import InMemoryRateLimiter
from langchain_standard_tests.integration_tests import ChatModelIntegrationTests

from langchain_together import ChatTogether

# Initialize the rate limiter in global scope, so it can be re-used
# across tests.
rate_limiter = InMemoryRateLimiter(
    requests_per_second=0.5,
)


class TestTogetherStandard(ChatModelIntegrationTests):
    @property
    def chat_model_class(self) -> Type[BaseChatModel]:
        return ChatTogether

    @property
    def chat_model_params(self) -> dict:
        return {
            "model": "mistralai/Mistral-7B-Instruct-v0.1",
            "rate_limiter": rate_limiter,
        }

    @pytest.mark.xfail(reason=("May not call a tool."))
    def test_tool_calling_with_no_arguments(self, model: BaseChatModel) -> None:
        super().test_tool_calling_with_no_arguments(model)

    @pytest.mark.xfail(reason="Not yet supported.")
    def test_usage_metadata_streaming(self, model: BaseChatModel) -> None:
        super().test_usage_metadata_streaming(model)
