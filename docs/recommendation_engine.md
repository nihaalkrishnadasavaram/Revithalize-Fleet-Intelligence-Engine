# Recommendation Engine

The engine in `backend/app/recommendations/` applies **if–then rules** to each vehicle's data and its three scores. It is deterministic: the same data always gives the same recommendations.

## Output format

Every recommendation has: `vehicle_id`, `category`, `priority` (High / Medium / Low), `title`, `reason` (the numbers that triggered it), `suggested_action` and, for cost recommendations, `estimated_annual_saving_inr`.

All rupee amounts are written with Indian digit grouping, for example ₹8,852 or ₹1,25,000.

## Rules

### Maintenance
| Condition | Priority | Recommendation |
|-----------|----------|----------------|
| Health score < 50 | High | Immediate inspection required |
| Battery health < 70 % | High | Battery replacement assessment |
| Battery health 70–79.9 % | Medium | Schedule battery inspection |
| Weakest of motor / electrical health < 65 % (< 50 % is High) | Medium / High | Inspect motor and electrical system |
| Maintenance status = Overdue | Medium | Complete overdue maintenance |
| Fast charging ≥ 60 % of charges and battery health < 85 % | Medium | Reduce fast charging |
| Maintenance Due Soon and health < 65 | Low | Schedule upcoming maintenance |

### Cost Reduction
| Condition | Priority | Recommendation |
|-----------|----------|----------------|
| Yearly maintenance cost ≥ 1.8 × type benchmark | Medium (High if ≥ 2.5×) | Control high maintenance spending – preventive maintenance and cost monitoring |
| Operating cost per km ≥ 1.4 × benchmark | Medium | Review operating cost per kilometre |
| Energy consumption ≥ 1.25 × benchmark | Medium | Investigate high energy consumption |

### Utilization
| Condition | Priority | Recommendation |
|-----------|----------|----------------|
| Utilization < 30 % | Medium | Reassign under-used vehicle |
| Utilization ≥ 90 % and health < 65 | Medium | Reduce load on heavily used vehicle |

### Risk Management
| Condition | Priority | Recommendation |
|-----------|----------|----------------|
| Risk score ≥ 70 | High | High operational risk |
| Risk score 55–69.9 | Medium | Elevated operational risk |

## Estimated annual savings (₹)

Cost recommendations include an illustrative estimate of the yearly rupee saving. The recoverable shares are assumptions for this academic project, not measured results.

| Recommendation | Estimate |
|----------------|----------|
| High maintenance spending | 30 % × (yearly maintenance cost − benchmark) |
| High operating cost per km | 50 % × (₹ per km − benchmark) × yearly distance |
| High energy consumption | 50 % × excess kWh per year × ₹9 per kWh |

The dashboard shows the saving on each recommendation card, the total (for the current filters) on the Recommendations page, and the fleet total on the Overview page.

## Avoiding duplicates

Within one category several rules may match. The engine keeps **only the highest-priority match per category**, so a vehicle gets at most four recommendations (one per category). On a tie the earlier rule in the list wins. This is verified by `test_each_category_appears_at_most_once_per_vehicle`.

## Risk alerts

A vehicle with a **risk score ≥ 70** also gets a **risk alert** (`alerts.py`), stored in its own table. The alert explains *why* using the factors present:

| Factor | Alert wording |
|--------|---------------|
| Breakdowns ≥ 1.0 per year | "N breakdowns in Y years since retrofit" |
| Battery health < 75 % | "battery health is down to X %" |
| Maintenance overdue | "maintenance is overdue" |
| Motor or electrical health < 60 % | "motor or electrical system health is low" |
| Accidents ≥ 2 | "N accidents on record" |
| Condition Poor | "vehicle condition is poor" |

The recommended action is built from the same factors, e.g. *"Restrict to low-risk duty, then test the battery pack, complete the overdue maintenance."* The alert is the notification view; the matching *Risk Management* recommendation is the action plan for the same trigger.

## Results on the 3,000-vehicle synthetic dataset

| Item | Count |
|------|------:|
| Recommendations generated | 2,380 |
| – Cost Reduction | 965 |
| – Maintenance | 826 |
| – Utilization | 296 |
| – Risk Management | 293 |
| Priority High / Medium / Low | 294 / 1,995 / 91 |
| Risk alerts | 49 |
| Estimated annual saving across cost recommendations | ₹14,01,431 |

## Changing the rules

Thresholds are named constants at the top of `rules.py`; each rule is a small function returning matches for one category. Adding a rule means adding one function branch and one test.
