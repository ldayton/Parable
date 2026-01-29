# Frontend Phases

Sequential pipeline with clean phase boundaries. Each phase completes before the next starts.

| Phase | Module          | Description                                                   |
| :---: | --------------- | ------------------------------------------------------------- |
|   0   | `__init__.py`   | Entry point; orchestrates phases                              |
|   1   | `verify.py`     | Subset verification; reject unsupported Python features early |
|   2   | `names.py`      | Scope analysis and name binding                               |
|   3   | `signatures.py` | Type syntax parsing and kind checking                         |
|   4   | `fields.py`     | Dataflow over `__init__`; infer field types                   |
|   5   | `hierarchy.py`  | Class hierarchy; subtyping relations                          |
|   6   | `inference.py`  | Bidirectional type inference (↑synth / ↓check)                |
|   7   | `lowering.py`   | Type-directed elaboration to IR                               |

## Design Principles

- **Sequential**: Each phase completes fully before the next starts
- **No back-edges**: Phase N reads outputs of phases 0..N-1, writes one artifact
- **Fail fast**: Reject bad input at the earliest possible phase
- **Decoupled**: Lowering only sees TypedAST, never calls inference

## Module Boundaries

| Module          | Knows about types? | Knows about IR? |
| --------------- | :----------------: | :-------------: |
| `verify.py`     |         no         |       no        |
| `names.py`      |         no         |       no        |
| `signatures.py` |   yes (parsing)    |       no        |
| `fields.py`     |  yes (inference)   |       no        |
| `hierarchy.py`  |  yes (subtyping)   |       no        |
| `inference.py`  |    yes (bidir)     |       no        |
| `lowering.py`   |  no (just reads)   |       yes       |

## Data Flow

```
         AST
          │
          ▼
┌─────────────────┐
│  0. __init__    │──▶ Context (empty tables)
└────────┬────────┘
         ▼
┌─────────────────┐
│  1. verify      │──▶ (rejects bad input or passes through)
└────────┬────────┘
         ▼
┌─────────────────┐
│  2. names       │──▶ NameTable { name → kind }
└────────┬────────┘
         ▼
┌─────────────────┐
│  3. signatures  │──▶ SigTable { func → (params, ret) }
└────────┬────────┘
         ▼
┌─────────────────┐
│  4. fields      │──▶ FieldTable { class → [(name, type)] }
└────────┬────────┘
         ▼
┌─────────────────┐
│  5. hierarchy   │──▶ SubtypeRel { class → ancestors }
└────────┬────────┘
         ▼
┌─────────────────┐
│  6. inference   │──▶ TypedAST (↑synth / ↓check)
└────────┬────────┘
         ▼
┌─────────────────┐
│  7. lowering    │──▶ IR Module
└────────┬────────┘
         ▼
         IR
```
