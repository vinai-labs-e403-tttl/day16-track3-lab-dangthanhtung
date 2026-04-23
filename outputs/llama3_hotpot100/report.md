# Lab 16 Benchmark Report

## Metadata
- Dataset: hotpot_100.json
- Mode: llama3-local
- Records: 200
- Agents: react, reflexion

## Summary
| Metric | ReAct | Reflexion | Delta |
|---|---:|---:|---:|
| EM | 0.71 | 0.89 | 0.18 |
| Avg attempts | 1 | 1.43 | 0.43 |
| Avg token estimate | 3231.27 | 5330.76 | 2099.49 |
| Avg latency (ms) | 2967.2 | 6364.44 | 3397.24 |

## Failure modes
```json
{
  "react": {
    "none": 71,
    "wrong_final_answer": 29
  },
  "reflexion": {
    "none": 89,
    "wrong_final_answer": 11
  }
}
```

## Extensions implemented
- structured_evaluator
- reflection_memory
- benchmark_report_json

## Discussion
Reflexion helps when the first attempt stops after the first hop or drifts to a wrong second-hop entity. The tradeoff is higher attempts, token cost, and latency. This run uses the OpenAI Python client pointed at a local Llama 3 compatible endpoint for actor, evaluator, and reflector steps, with token and latency values collected from local runtime metadata and wall-clock measurements. Reflection memory is useful when the evaluator identifies a missed hop or unsupported final entity, because the next actor attempt receives a concrete lesson and strategy. Remaining errors usually indicate evaluator strictness, context ambiguity, or a reflection that did not point to the exact missing evidence.
