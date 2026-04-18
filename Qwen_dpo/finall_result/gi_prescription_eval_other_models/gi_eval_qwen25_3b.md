# GI处方能力自动评估（DEP/DER/DUC/FCF/CCR）

- dose_tol=0.1
- course_tol=0.2

## Pooled (Internal + External)

| 模型 | n | DEP | DER | DUC | FCF | CCR | GI Score |
|---|---:|---:|---:|---:|---:|---:|---:|
| qwen2.5-3b-instruct | 82 | 0.2398 | 0.1481 | 0.1028 | 0.1884 | 0.0000 | 0.2624 |

## Internal

| 模型 | n | DEP | DER | DUC | FCF | CCR | GI Score |
|---|---:|---:|---:|---:|---:|---:|---:|
| qwen2.5-3b-instruct | 59 | 0.3333 | 0.2059 | 0.1429 | 0.2619 | 0.0000 | 0.3257 |

## External

| 模型 | n | DEP | DER | DUC | FCF | CCR | GI Score |
|---|---:|---:|---:|---:|---:|---:|---:|
| qwen2.5-3b-instruct | 23 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.1000 |
