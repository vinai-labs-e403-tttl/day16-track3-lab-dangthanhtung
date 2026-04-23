from __future__ import annotations

import time
from dataclasses import dataclass
import json
import os
from typing import TypeVar

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel

from .prompts import ACTOR_SYSTEM, EVALUATOR_SYSTEM, REFLECTOR_SYSTEM
from .schemas import JudgeResult, LLMResult, QAExample, ReflectionEntry

T = TypeVar("T", bound=BaseModel)


def format_context(example: QAExample) -> str:
    return "\n\n".join(f"Title: {chunk.title}\nText: {chunk.text}" for chunk in example.context)


def response_token_count(response: object) -> int:
    usage = getattr(response, "usage", None)
    if usage is None:
        return 0
    total = getattr(usage, "total_tokens", None)
    if total is not None:
        return int(total)
    input_tokens = getattr(usage, "input_tokens", None) or 0
    output_tokens = getattr(usage, "output_tokens", None) or 0
    return int(input_tokens + output_tokens)


@dataclass
class OpenAIRuntime:
    model: str = "llama3"
    base_url: str = "http://localhost:11434/v1"

    def __post_init__(self) -> None:
        load_dotenv()
        base_url = os.getenv("OPENAI_BASE_URL") or os.getenv("LLM_BASE_URL") or self.base_url
        api_key = os.getenv("OPENAI_API_KEY") or "local-llama3"
        self.client = OpenAI(base_url=base_url, api_key=api_key)

    def actor_answer(
        self,
        example: QAExample,
        attempt_id: int,
        agent_type: str,
        reflection_memory: list[str],
    ) -> LLMResult:
        memory = "\n".join(f"- {item}" for item in reflection_memory) or "No prior reflections."
        prompt = f"""Question:
{example.question}

Context:
{format_context(example)}

Agent type: {agent_type}
Attempt: {attempt_id}

Reflection memory:
{memory}
"""
        started = time.perf_counter()
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": ACTOR_SYSTEM},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
        )
        latency_ms = round((time.perf_counter() - started) * 1000)
        content = response.choices[0].message.content or ""
        return LLMResult(
            text=content.strip(),
            token_count=response_token_count(response),
            latency_ms=latency_ms,
        )

    def evaluator(self, example: QAExample, answer: str) -> tuple[JudgeResult, int, int]:
        prompt = f"""Question:
{example.question}

Gold answer:
{example.gold_answer}

Predicted answer:
{answer}

Context:
{format_context(example)}
"""
        parsed, token_count, latency_ms = self._parse(EVALUATOR_SYSTEM, prompt, JudgeResult)
        return parsed, token_count, latency_ms

    def reflector(
        self,
        example: QAExample,
        attempt_id: int,
        answer: str,
        judge: JudgeResult,
    ) -> tuple[ReflectionEntry, int, int]:
        prompt = f"""Question:
{example.question}

Context:
{format_context(example)}

Failed attempt: {attempt_id}
Predicted answer: {answer}
Evaluator reason: {judge.reason}
Missing evidence: {judge.missing_evidence}
Spurious claims: {judge.spurious_claims}
"""
        parsed, token_count, latency_ms = self._parse(REFLECTOR_SYSTEM, prompt, ReflectionEntry)
        parsed.attempt_id = attempt_id
        return parsed, token_count, latency_ms

    def _parse(self, instructions: str, prompt: str, output_type: type[T]) -> tuple[T, int, int]:
        started = time.perf_counter()
        response = self._chat_json(instructions, prompt, output_type)
        latency_ms = round((time.perf_counter() - started) * 1000)
        content = response.choices[0].message.content or "{}"
        return self._parse_json_content(content, output_type), response_token_count(response), latency_ms

    def _chat_json(self, instructions: str, prompt: str, output_type: type[T]) -> object:
        schema = output_type.model_json_schema()
        json_prompt = f"""{prompt}

Return only a JSON object that matches this schema:
{json.dumps(schema)}
"""
        messages = [
            {"role": "system", "content": instructions},
            {"role": "user", "content": json_prompt},
        ]
        try:
            return self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": output_type.__name__,
                        "schema": schema,
                        "strict": True,
                    },
                },
            )
        except Exception:
            return self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0,
                response_format={"type": "json_object"},
            )

    @staticmethod
    def _parse_json_content(content: str, output_type: type[T]) -> T:
        try:
            return output_type.model_validate_json(content)
        except ValueError:
            start = content.find("{")
            end = content.rfind("}")
            if start == -1 or end == -1 or end < start:
                raise
            return output_type.model_validate(json.loads(content[start : end + 1]))
