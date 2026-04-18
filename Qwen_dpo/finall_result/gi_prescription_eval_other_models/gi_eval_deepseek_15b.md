# GI处方能力自动评估（DEP/DER/DUC/FCF/CCR）

- dose_tol=0.1
- course_tol=0.2

## Pooled (Internal + External)

| 模型 | n | DEP | DER | DUC | FCF | CCR | GI Score |
|---|---:|---:|---:|---:|---:|---:|---:|
| deepseek-r1-distill-qwen-1.5b | 82 | 0.0799 | 0.0282 | 0.0000 | 0.0000 | 0.1799 | 0.1156 |

## Internal

| 模型 | n | DEP | DER | DUC | FCF | CCR | GI Score |
|---|---:|---:|---:|---:|---:|---:|---:|
| deepseek-r1-distill-qwen-1.5b | 59 | 0.1111 | 0.0392 | 0.0000 | 0.0000 | 0.2500 | 0.1217 |

## External

| 模型 | n | DEP | DER | DUC | FCF | CCR | GI Score |
|---|---:|---:|---:|---:|---:|---:|---:|
| deepseek-r1-distill-qwen-1.5b | 23 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.1000 |
