# MCAT (Modular Computerized Adaptive Test) Database Specification

## 1. Item Response Theory (IRT) Data Model
MCAT utilizes the 3-Parameter Logistic (3PL) Item Response Theory model:
$$P_i(\theta) = c_i + \frac{1 - c_i}{1 + e^{-a_i (\theta - b_i)}}$$
Where:
- $a_i$: Item discrimination parameter.
- $b_i$: Item difficulty parameter.
- $c_i$: Pseudo-guessing parameter.
- $\theta$: Student latent cognitive ability estimate.

## 2. Table Structure
- `mcat_exams`: Active and historical testing windows, time limits, and target cohort divisions.
- `mcat_blueprints`: Test configuration rules (number of items, content distribution across domains).
- `mcat_items`: Psychometrically calibrated question pool with options, keys, and IRT parameters.
- `mcat_attempts`: Session lifecycle records (`STARTED`, `IN_PROGRESS`, `SUBMITTED`, `TERMINATED`).
- `mcat_responses`: Granular logs of selected option, correctness, response latency (milliseconds), and order presented.
- `mcat_ability_estimates`: Progression of $\theta$ estimates during the adaptive testing trajectory.
- `mcat_integrity_events`: Offline desktop kiosk security events (window focus lost, devtools open attempt, shortcut key interception).
