# Lab 16 Benchmark Report

## Metadata
- Dataset: hotpot_mini.json
- Mode: openai
- Records: 16
- Agents: react, reflexion

## Summary
| Metric | ReAct | Reflexion | Delta |
|---|---:|---:|---:|
| EM | 0.875 | 0.875 | 0.0 |
| Avg attempts | 1 | 1.25 | 0.25 |
| Avg token estimate | 439.75 | 642.5 | 202.75 |
| Avg latency (ms) | 4328.5 | 4632.75 | 304.25 |

## Failure modes
```json
{
  "react": {
    "none": 7,
    "wrong_final_answer": 1
  },
  "reflexion": {
    "none": 7,
    "wrong_final_answer": 1
  }
}
```

## Extensions implemented
- structured_evaluator
- reflection_memory
- benchmark_report_json

## Discussion
Reflexion helps when the first attempt stops after the first hop or drifts to a wrong second-hop entity. The tradeoff is higher attempts, token cost, and latency. This run uses real OpenAI API calls for actor, evaluator, and reflector steps, with token and latency values collected from API usage metadata and wall-clock measurements. Reflection memory is useful when the evaluator identifies a missed hop or unsupported final entity, because the next actor attempt receives a concrete lesson and strategy. Remaining errors usually indicate evaluator strictness, context ambiguity, or a reflection that did not point to the exact missing evidence.
