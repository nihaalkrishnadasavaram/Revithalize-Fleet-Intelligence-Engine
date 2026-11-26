# Model Selection Report

> These are **proposed** models for future phases, for a fleet of retrofitted electric motorcycles and scooters. None has been implemented, trained or benchmarked in this project, so no performance figures are given.

## Selection criteria

1. **Fit with the data:** small-to-medium tabular data with numeric and categorical features.
2. **Explainability:** fleet managers must understand why a vehicle is flagged.
3. **Simplicity:** suitable for a student team; mature libraries (scikit-learn).
4. **Robustness:** tolerant of noise, outliers and mixed feature scales.

## Summary

| Task | Proposed model | Alternatives considered |
|------|----------------|-------------------------|
| Vehicle health prediction | Random Forest | Linear regression, single decision tree, neural network |
| Fleet risk prediction | Gradient Boosting | Logistic regression, Random Forest |
| Cost forecasting | Linear Regression | ARIMA / Prophet, gradient boosting |
| Fleet allocation | Optimization (assignment / linear programming) | Genetic algorithm, greedy heuristic |

## Justification

### Random Forest – battery and health prediction
- Handles non-linear relationships (e.g. battery fade accelerating with charge cycles and fast charging) and mixed feature types without much preprocessing.
- Resistant to overfitting through averaging many trees; works with modest data.
- Provides feature importances that map neatly onto the existing health components (battery, motor, electrical system, age, maintenance).
- *Trade-off:* less transparent than the current formula; cannot extrapolate beyond the range seen in training.

### Gradient Boosting – risk prediction
- Typically the strongest choice for tabular classification; learns interactions such as "old **and** overdue".
- Works well with imbalanced outcomes when class weights or thresholds are tuned.
- Supports feature importance and SHAP-style explanations.
- *Trade-off:* more hyper-parameters; needs careful validation and probability calibration.

### Linear Regression – cost forecasting
- Fast, easy to explain, and a strong **baseline**: coefficients read as "extra rupees per year of retrofit age".
- Needs little data; any more complex model must beat it to be justified.
- *Trade-off:* assumes linear effects; extend with Ridge regularisation or time features if needed.

### Optimization – fleet allocation
- Allocation is a decision problem, not a prediction problem: the goal is the best assignment of motorcycles and scooters to routes under constraints (battery range, charger availability, cost).
- Assignment algorithms and linear programming give exact or provably good answers and clear constraints.
- *Trade-off:* needs demand, route and charging data that the current dataset does not contain.

## Evaluation approach (all prediction models)

- **Time-ordered split:** train on older data, test on newer data to avoid leakage.
- **Baselines:** compare with the existing rule-based score and with a naive predictor.
- **Metrics:** see `ai_architecture.md` per task.
- **Report honestly:** only metrics actually measured on held-out real data.

## Recommendation

Keep the rule-based framework as the production logic. Pilot Random Forest and Gradient Boosting in parallel on real data; adopt a model only if it clearly outperforms the rules on a hold-out set and remains explainable.
