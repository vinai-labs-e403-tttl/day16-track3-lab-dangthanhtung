# Lab 16 Benchmark Report

## Metadata
- Dataset: hotpot_mini.json
- Mode: llama3-local
- Records: 16
- Agents: react, reflexion

## Summary
| Metric | ReAct | Reflexion | Delta |
|---|---:|---:|---:|
| EM | 1.0 | 1.0 | 0.0 |
| Avg attempts | 1 | 1 | 0 |
| Avg token estimate | 479 | 480 | 1 |
| Avg latency (ms) | 1765.25 | 1080 | -685.25 |

## Failure modes
```json
{
  "react": {
    "none": 8
  },
  "reflexion": {
    "none": 8
  }
}
```

## Extensions implemented
- structured_evaluator
- reflection_memory
- benchmark_report_json

## Discussion
Reflexion helps when the first attempt stops after the first hop or drifts to a wrong second-hop entity. The tradeoff is higher attempts, token cost, and latency. This run uses the OpenAI Python client pointed at a local Llama 3 compatible endpoint for actor, evaluator, and reflector steps, with token and latency values collected from local runtime metadata and wall-clock measurements. Reflection memory is useful when the evaluator identifies a missed hop or unsupported final entity, because the next actor attempt receives a concrete lesson and strategy. Remaining errors usually indicate evaluator strictness, context ambiguity, or a reflection that did not point to the exact missing evidence.
