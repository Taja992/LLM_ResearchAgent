"""Shared test setup: pytest loads this file before any test runs."""

from pydantic_ai import models

# Safety net: any accidental call to a real LLM fails the test instead of running.
# Fake models (FunctionModel, TestModel) still work.
models.ALLOW_MODEL_REQUESTS = False
