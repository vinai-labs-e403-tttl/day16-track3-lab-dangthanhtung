from __future__ import annotations
from dataclasses import dataclass
from typing import Literal
from .openai_runtime import OpenAIRuntime
from .schemas import AttemptTrace, QAExample, ReflectionEntry, RunRecord

@dataclass
class BaseAgent:
    agent_type: Literal["react", "reflexion"]
    runtime: OpenAIRuntime
    max_attempts: int = 1

    def run(self, example: QAExample) -> RunRecord:
        reflection_memory: list[str] = []
        reflections: list[ReflectionEntry] = []
        traces: list[AttemptTrace] = []
        final_answer = ""
        final_score = 0
        for attempt_id in range(1, self.max_attempts + 1):
            actor_result = self.runtime.actor_answer(example, attempt_id, self.agent_type, reflection_memory)
            answer = actor_result.text
            judge, judge_tokens, judge_latency_ms = self.runtime.evaluator(example, answer)
            token_count = actor_result.token_count + judge_tokens
            latency_ms = actor_result.latency_ms + judge_latency_ms
            trace = AttemptTrace(
                attempt_id=attempt_id,
                answer=answer,
                score=judge.score,
                reason=judge.reason,
                token_estimate=token_count,
                latency_ms=latency_ms,
            )
            final_answer = answer
            final_score = judge.score
            if judge.score == 1:
                traces.append(trace)
                break

            if self.agent_type == "reflexion" and attempt_id < self.max_attempts:
                reflection, reflection_tokens, reflection_latency_ms = self.runtime.reflector(
                    example,
                    attempt_id,
                    answer,
                    judge,
                )
                trace.reflection = reflection
                traces.append(trace)
                reflections.append(reflection)
                reflection_memory.append(f"{reflection.lesson} Next: {reflection.next_strategy}")
                trace.token_estimate += reflection_tokens
                trace.latency_ms += reflection_latency_ms
                continue
            traces.append(trace)
        total_tokens = sum(t.token_estimate for t in traces)
        total_latency = sum(t.latency_ms for t in traces)
        failure_mode = "none" if final_score == 1 else "wrong_final_answer"
        return RunRecord(qid=example.qid, question=example.question, gold_answer=example.gold_answer, agent_type=self.agent_type, predicted_answer=final_answer, is_correct=bool(final_score), attempts=len(traces), token_estimate=total_tokens, latency_ms=total_latency, failure_mode=failure_mode, reflections=reflections, traces=traces)

class ReActAgent(BaseAgent):
    def __init__(self, runtime: OpenAIRuntime) -> None:
        super().__init__(agent_type="react", runtime=runtime, max_attempts=1)

class ReflexionAgent(BaseAgent):
    def __init__(self, runtime: OpenAIRuntime, max_attempts: int = 3) -> None:
        super().__init__(agent_type="reflexion", runtime=runtime, max_attempts=max_attempts)
