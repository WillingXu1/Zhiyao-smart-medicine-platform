# GI处方能力自动评估（DEP/DER/DUC/FCF/CCR）

- dose_tol=0.1
- course_tol=0.2

## Pooled (Internal + External)

| 模型 | n | DEP | DER | DUC | FCF | CCR | GI Score |
|---|---:|---:|---:|---:|---:|---:|---:|
| qwen2.5-7b-instruct | 82 | 0.2805 | 0.1622 | 0.2190 | 0.2503 | 0.0000 | 0.3120 |

## Internal

| 模型 | n | DEP | DER | DUC | FCF | CCR | GI Score |
|---|---:|---:|---:|---:|---:|---:|---:|
| qwen2.5-7b-instruct | 59 | 0.3898 | 0.2255 | 0.3043 | 0.3478 | 0.0000 | 0.3946 |

## External

| 模型 | n | DEP | DER | DUC | FCF | CCR | GI Score |
|---|---:|---:|---:|---:|---:|---:|---:|
| qwen2.5-7b-instruct | 23 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.1000 |
