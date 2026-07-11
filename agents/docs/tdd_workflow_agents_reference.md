---
description: Master Reference Guide for OpenCode Agents and Teams.
disable: true
hidden: true
---

# Blueprint: Test-Driven Development (TDD) Workflow for Autonomous Agents

This document defines the core philosophy, execution loops, and architectural boundaries for agentic code generation and validation.

---

## 1. Core Philosophy: The Red-Green-Refactor Cycle

The agent must treat tests as executable specifications. Code must never be written without a defining test.

### The Execution Loop

1. 🔴 **RED**: Write a small, intentional unit test for a single expected behavior. Run the test and ensure it **fails** (verifying the test works and the logic is currently missing).
2. 🟢 **GREEN**: Write the _minimum necessary production code_ required to make the test pass. Avoid scope creep or optimization.
3. 🔵 **REFACTOR**: Optimize, clean, and deduplicate the code. Rerun the test to ensure no functional regressions occurred.

---

## 2. Strategy A: Core Software Engineering Projects

Apply strict TDD. The agent must write tests first to establish structural contracts before generating functional code.

### Guidelines for Core SE

- **Test Behaviors, Not Internals**: Assert against public interfaces, APIs, and functions. Do not write tests for private methods or internal variables.
- **Deterministic Rules**: Assertions must expect exact inputs to equal exact outputs (`assert actual == expected`).
- **Error Handling First**: Write failing tests for edge cases, null pointers, empty collections, and network failures before implementing the happy path.
- **Isolation**: Use mocks, stubs, and fakes to isolate the system under test from external databases or networks.

---

## 3. Strategy B: AI/ML Infrastructure & Data Plumbing

Apply strict TDD here exactly like Core SE. While ML models are statistical, the pipelines that feed them are deterministic software.

### Guidelines for ML Infrastructure

- **Data Preprocessing & Transformations**: Write tests first to verify text tokenization, string cleaning, or image resizing against precise token/pixel boundaries.
- **Feature Engineering**: Assert that normalization (e.g., Min-Max scaling) outputs values strictly between `0.0` and `1.0` and handles empty or out-of-bounds matrices safely.
- **API & Serving Layers**: Write integration tests first ensuring the deployment web framework (FastAPI, Flask, etc.) correctly validates input JSON schemas and returns explicit HTTP error codes for bad payloads.

---

## 4. Strategy C: AI/ML Model Evaluations (Non-TDD)

Traditional TDD fails for the core model logic because outputs are probabilistic, not deterministic. Do not write strict unit tests for model training or predictions. Instead, use an evaluation pipeline framework.

### Guidelines for Model Evaluations

- **Regression Testing (Gold Datasets)**: Evaluate model checkpoints against a static, curated benchmarking dataset. A test "passes" if global metrics (e.g., F1-score, Accuracy, BLEU, or custom LLM judges) meet or exceed a defined baseline threshold.
- **Invariance Testing**: Assert that minor, non-semantic alterations to inputs do not change the classification output.
  - _Example:_ `predict("John is a qualified candidate") == predict("Sarah is a qualified candidate")`
- **Directional (Metamorphic) Expectations**: Assert that modifying a key feature shifts the prediction in a logical direction, even if the exact number cannot be guessed.
  - _Example:_ Increasing a house's square footage must output a predicted price _greater than_ the previous prediction.
- **Data Validation Contracts**: Use runtime validation tools (e.g., Pydantic or Great Expectations) to check data schema, null distributions, and type anomalies at the model input boundary.
