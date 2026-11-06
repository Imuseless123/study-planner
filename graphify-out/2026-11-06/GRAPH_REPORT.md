# Graph Report - study-planner  (2026-11-06)

## Corpus Check
- 173 files · ~255,225 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 22 file(s) not represented in the graph (top: (none) 9, .ini 4, .log 3)

## Summary
- 1247 nodes · 2486 edges · 107 communities (48 shown, 59 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 242 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `2e3dca9e`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Logging API
- Frontend Auth App
- test_auth.py
- Auth API Backend
- SubjectRepository
- Test Fixtures Core
- Assignments API
- Frontend Dependencies
- LP Solver Service
- User Data Repositories
- schedule_service.py
- System Architecture Concepts
- Schedule Integration Flow
- Frontend API Clients
- Dashboard Frontend Widgets
- Dashboard Backend Services
- LoggingPage.tsx
- LP Solver Test Fixtures
- react
- Risk Indicator Service
- TypeScript Config
- Logs Integration Tests
- Risk API Tests
- MILP Model Builder
- Solver Tests Warnings
- Subjects Integration Tests
- Risk Calculator Tests
- Solver Integration Tests
- Consent API
- Feedback API
- Assignments Integration Tests
- Backend Setup History
- Risk Model Rationale
- Risk Computation Pipeline
- Database Migrations
- Backend Service Config
- LP API Tests
- Consent Integration Tests
- Postgres Docker Config
- Piecewise Approximation Tests
- Risk Score Calculator
- Risk Classification
- Sleep Deficit Normalization
- Workload Density Normalization
- Frontend Docker Config
- Deadline Proximity Normalization
- Schedule Generate API
- Dashboard Integration Tests
- LP Solver Docker Config
- Risk Indicator Docker Config
- security.py
- Tech Stack Documentation
- Docker Build Config
- Architecture Docs Index
- TestAccountDeletion
- run_real.py
- Healthcheck Config
- Functional Requirements Progress
- MILP Boundary Tests
- Docker Compose Services
- MILP Diminishing Returns Model
- Vite Environment Types
- Tier1 Database Logging
- Schedule Explainability
- CRUD Partial Update Pattern
- Data Deletion UX
- Graphify Skill Trigger
- JWT Authentication Rationale
- 3. Metrics (Các chỉ số so sánh)
- FastAPI Shared Versions
- Test Stack Shared
- Hard Constraints Docs
- Solve Schedule Concept
- Frontend React Architecture
- PostgreSQL Architecture Notes
- Project Knowledge Graph
- Daily Log Backend Setup
- Daily Log Frontend Auth
- Daily Log CRUD Subjects
- Daily Log Data Export
- Functional Requirements Complete
- Pydantic Schemas LP Solver
- User
- devDependencies
- decode_token
- scripts
- delete_user_data
- client
- build_explanation
- build_warnings

## God Nodes (most connected - your core abstractions)
1. `User` - 72 edges
2. `LogRepository` - 38 edges
3. `getErrorMessage()` - 36 edges
4. `antd` - 29 edges
5. `SubjectRepository` - 28 edges
6. `AssignmentRepository` - 26 edges
7. `react` - 25 edges
8. `Subject` - 24 edges
9. `solve_schedule()` - 23 edges
10. `@ant-design/icons` - 22 edges

## Surprising Connections (you probably didn't know these)
- `Lưu ý kỹ thuật` --references--> `_build_time_slots()`  [INFERRED]
  evaluate/README.md → backend/app/services/schedule_service.py
- `Tier 1→Tier 2→Tier 3 Integration with 2-Step Fallback` --semantically_similar_to--> `End-to-End Data Flow Tier1→Tier2→Tier3`  [INFERRED] [semantically similar]
  KLTN/daily-logs/2026-10-21.md → docs/architecture/data-flow.md
- `W_max_effective Risk-Adjusted Daily Cap` --semantically_similar_to--> `W_max_effective Formula`  [INFERRED] [semantically similar]
  KLTN/daily-logs/2026-10-21.md → docs/architecture/data-flow.md
- `Quick Interactions V2 (5-Tap Friction Reduction)` --semantically_similar_to--> `Tier 1 Quick Interactions Mobile-First UX`  [INFERRED] [semantically similar]
  KLTN/daily-logs/2026-10-26-ux-refinement-mobile.md → docs/architecture/tier-1-overview.md
- `FastAPI + SQLAlchemy + PostgreSQL Stack` --semantically_similar_to--> `Tech Stack (React/FastAPI/PuLP/PostgreSQL/Docker)`  [INFERRED] [semantically similar]
  backend/requirements.txt → docs/architecture/system-architecture.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Quick Interactions Input Hub** — kltn_daily_logs_2026_10_26_ux_refinement_mobile_quick_interactions, kltn_daily_logs_2026_10_26_ux_refinement_mobile_quick_study_bar, kltn_daily_logs_2026_10_26_ux_refinement_mobile_quick_sleep_widget, kltn_daily_logs_2026_10_26_ux_refinement_mobile_quick_mood_bar [EXTRACTED 1.00]
- **Three-Tier Microservices Architecture** — docs_architecture_system_architecture_three_tier, docs_architecture_tier_1_overview_tier_1, docs_architecture_tier_2_overview_risk_indicator, docs_architecture_tier_3_overview_lp_solver [EXTRACTED 1.00]
- **MILP optimisation flow with risk scaling and fallback** — docs_daily_logs_2026_10_19_tier_3_lp_solver_milp_model_builder, docs_daily_logs_2026_10_19_tier_3_lp_solver_w_max_effective, docs_daily_logs_2026_10_19_tier_3_lp_solver_fallback_two_step, docs_daily_logs_2026_10_19_tier_3_lp_solver_solve_schedule [EXTRACTED 1.00]
- **MILP Soft-Constraint Risk-Aware Optimization Model** — kltn_architecture_tier_3_overview_milp, kltn_architecture_tier_3_overview_piecewise_sqrt, kltn_architecture_tier_3_overview_penalty_tuning, kltn_architecture_data_flow_w_max_effective [EXTRACTED 1.00]
- **Quick Input Hub mobile logging widgets** — docs_daily_logs_2026_10_26_ux_refinement_mobile_quick_input_hub, docs_daily_logs_2026_10_26_ux_refinement_mobile_quickmoodbar, docs_daily_logs_2026_10_26_ux_refinement_mobile_quicksleepwidget, docs_daily_logs_2026_10_26_ux_refinement_mobile_quickstudybar [EXTRACTED 1.00]
- **Three-Tier Microservices End-to-End Flow** — kltn_architecture_data_flow_tier_1, kltn_architecture_data_flow_tier_2, kltn_architecture_data_flow_tier_3, kltn_architecture_data_flow_postgresql [EXTRACTED 1.00]
- **Three tier schedule generation flow** — docs_daily_logs_2026_10_21_three_tier_integration, docs_daily_logs_2026_10_21_schedule_service, docs_daily_logs_2026_10_21_schedulepage_calendar, readme_three_tier_architecture [EXTRACTED 1.00]
- **Risk Score to W_max_effective Pipeline** — docs_architecture_data_flow_risk_score, docs_architecture_tier_2_overview_risk_indicator, docs_daily_logs_2026_10_14_tier_2_risk_indicator_risk_service, docs_architecture_data_flow_w_max_effective [INFERRED 0.85]

## Communities (107 total, 59 thin omitted)

### Community 0 - "Logging API"
Cohesion: 0.10
Nodes (23): delete_mood(), delete_sleep(), delete_study(), list_mood(), list_sleep(), list_study(), log_mood(), log_sleep() (+15 more)

### Community 1 - "Frontend Auth App"
Cohesion: 0.14
Nodes (22): authApi, AuthResponse, ConsentResponse, LoginPayload, RegisterPayload, UserMe, App(), ProtectedRoute() (+14 more)

### Community 2 - "test_auth.py"
Cohesion: 0.11
Nodes (4): TestLogin, TestLogout, TestMe, TestRegister

### Community 3 - "Auth API Backend"
Cohesion: 0.07
Nodes (20): login(), logout(), me(), register(), update_settings(), UserRepository, LoginRequest, LoginResponse (+12 more)

### Community 4 - "SubjectRepository"
Cohesion: 0.20
Nodes (4): Subject, SubjectRepository, DashboardService, TestSubjectRepository

### Community 5 - "Test Fixtures Core"
Cohesion: 0.10
Nodes (16): auth_headers(), auth_token(), db_session(), engine(), second_auth_headers(), second_auth_token(), second_subject(), second_user() (+8 more)

### Community 6 - "Assignments API"
Cohesion: 0.12
Nodes (17): create_assignment(), delete_assignment(), get_assignment(), get_stats(), _get_subject_name(), list_assignments(), _to_response(), update_assignment() (+9 more)

### Community 7 - "Frontend Dependencies"
Cohesion: 0.13
Nodes (18): dependencies, @ant-design/icons@^5.2.6, antd@^5.12.0, axios@^1.6.2, dayjs@^1.11.10, react@^18.2.0, react-dom@^18.2.0, react-router-dom@^6.20.0 (+10 more)

### Community 8 - "LP Solver Service"
Cohesion: 0.10
Nodes (15): generate_schedule(), health(), root(), Conflict, ConstraintExplanation, DayExplanation, HealthResponse, InfeasibleResponse (+7 more)

### Community 9 - "User Data Repositories"
Cohesion: 0.14
Nodes (10): export_user_data(), Base, Consent, gen_uuid(), MoodLog, Schedule, SleepLog, StudySession (+2 more)

### Community 10 - "schedule_service.py"
Cohesion: 0.05
Nodes (19): get_risk_score(), get_settings(), Settings, health(), root(), fetch_risk_score(), _aggregate_subjects(), _build_time_slots() (+11 more)

### Community 11 - "System Architecture Concepts"
Cohesion: 0.07
Nodes (21): End-to-End Data Flow Tier1→Tier2→Tier3, MILP Model Variables and Constraints, Risk Score (SD/WD/DP/SI Weighted), Time Slots tod_factor Grid, Risk Classification Low/Moderate/High, Workload Risk Indicator (Tier 2), Constraints C1–C7 with Soft Deadline/Daily Cap, LP Optimization Engine (Tier 3 MILP) (+13 more)

### Community 12 - "Schedule Integration Flow"
Cohesion: 0.07
Nodes (28): coinor-cbc solver backend, DEFAULT_LAMBDA_DAILY single source of truth, 2-step Fallback on Infeasible, LP Optimization Engine (Tier 3), MILP Model Builder model.py, Soft Constraints deadline and daily cap, Thesis Example section 4.5.6, W_max_effective risk integration (+20 more)

### Community 13 - "Frontend API Clients"
Cohesion: 0.11
Nodes (22): api, consentApi, ConsentInfo, Feedback, feedbackApi, FeedbackCreate, riskApi, RiskComponents (+14 more)

### Community 14 - "Dashboard Frontend Widgets"
Cohesion: 0.13
Nodes (29): getErrorMessage(), dashboardApi, DashboardSummary, UpcomingAssignment, DeadlineTimeline(), Props, QuickCreateButtons(), ENERGY_LEVELS (+21 more)

### Community 15 - "Dashboard Backend Services"
Cohesion: 0.20
Nodes (3): summary(), get_current_user(), get_db()

### Community 16 - "LoggingPage.tsx"
Cohesion: 0.12
Nodes (28): Assignment, AssignmentCreatePayload, assignmentsApi, AssignmentStats, AssignmentUpdatePayload, logsApi, MoodLogItem, MoodLogPayload (+20 more)

### Community 17 - "LP Solver Test Fixtures"
Cohesion: 0.11
Nodes (8): client(), simple_payload(), _standard_slots(), thesis_example_payload(), boundary_payload(), client(), good_habits_payload(), high_risk_payload()

### Community 18 - "react"
Cohesion: 0.20
Nodes (12): SubjectCreatePayload, ITEMS, MobileBottomNav(), Props, QuickActionFab(), useIsMobile(), AppLayout(), MENU_ITEMS (+4 more)

### Community 19 - "Risk Indicator Service"
Cohesion: 0.14
Nodes (9): compute_risk_score(), RiskResult, health(), root(), HealthResponse, RiskComponents, RiskRequest, RiskResponse (+1 more)

### Community 20 - "TypeScript Config"
Cohesion: 0.10
Nodes (19): compilerOptions, allowImportingTsExtensions, baseUrl, isolatedModules, jsx, lib, module, moduleResolution (+11 more)

### Community 21 - "Logs Integration Tests"
Cohesion: 0.12
Nodes (3): TestMoodLog, TestSleepLog, TestStudyLog

### Community 24 - "Solver Tests Warnings"
Cohesion: 0.16
Nodes (5): extract_schedule(), identify_conflicts(), solve_schedule(), TestFeasibility, TestThesisExample

### Community 26 - "Risk Calculator Tests"
Cohesion: 0.17
Nodes (3): normalize_study_inconsistency(), TestNormalizeStudyInconsistency, TestWeights

### Community 27 - "Solver Integration Tests"
Cohesion: 0.18
Nodes (3): TestDefaultConsistency, TestNonUniqueness, TestWarnings

### Community 28 - "Consent API"
Cohesion: 0.30
Nodes (5): get_consent(), sign_consent(), withdraw(), ConsentCreate, ConsentResponse

### Community 29 - "Feedback API"
Cohesion: 0.30
Nodes (5): create_feedback(), list_feedback(), Feedback, FeedbackCreate, FeedbackResponse

### Community 31 - "Backend Setup History"
Cohesion: 0.18
Nodes (8): API Endpoints and JWT Security, 9-Table Database Schema with CASCADE, Tier 1 Web Application Layer, E2E 10 Manual Tests, Tier 1 Backend Setup (Docker + 9 Tables + 14 Endpoints), Frontend Auth with Zustand and Axios Interceptor, ProtectedRoute 3-Layer Guard, Pytest Suite 93 Tests 93.89% Coverage

### Community 32 - "Risk Model Rationale"
Cohesion: 0.17
Nodes (7): Tier 1 FastAPI Port 8000, Tier 2 Risk Indicator Port 8001, Tier 3 LP Solver Port 8002, 170 Automated Tests, Risk Weights 0.35 0.30 0.20 0.15, Pytest Suite 93 Tests 93.89 Percent, Two-Step Fallback W_max Effective

### Community 34 - "Database Migrations"
Cohesion: 0.25
Nodes (3): upgrade(), upgrade(), upgrade()

### Community 35 - "Backend Service Config"
Cohesion: 0.18
Nodes (11): command, container_name, depends_on, env_file, ports, restart, volumes, working_dir (+3 more)

### Community 38 - "Postgres Docker Config"
Cohesion: 0.20
Nodes (10): POSTGRES_DB, POSTGRES_PASSWORD, POSTGRES_USER, container_name, environment, image, ports, restart (+2 more)

### Community 44 - "Frontend Docker Config"
Cohesion: 0.25
Nodes (8): VITE_API_URL, container_name, depends_on, environment, ports, restart, volumes, frontend

### Community 46 - "Schedule Generate API"
Cohesion: 0.22
Nodes (3): generate(), latest(), get_latest_schedule()

### Community 48 - "LP Solver Docker Config"
Cohesion: 0.29
Nodes (7): command, container_name, ports, restart, volumes, working_dir, lp-solver

### Community 49 - "Risk Indicator Docker Config"
Cohesion: 0.29
Nodes (7): command, container_name, ports, restart, volumes, working_dir, risk-indicator

### Community 50 - "security.py"
Cohesion: 0.19
Nodes (5): create_access_token(), create_refresh_token(), hash_password(), verify_password(), TestPasswordHashing

### Community 51 - "Tech Stack Documentation"
Cohesion: 0.33
Nodes (6): FastAPI + SQLAlchemy + PostgreSQL Stack, JWT Auth (python-jose + bcrypt), Pytest Testing Suite Dependencies, Data Flows: Logging/Dashboard and Schedule Generation, Tech Stack (React/FastAPI/PuLP/PostgreSQL/Docker), Three-Tier Microservices Architecture

### Community 52 - "Docker Build Config"
Cohesion: 0.53
Nodes (6): build, context, dockerfile, build, build, build

### Community 55 - "run_real.py"
Cohesion: 0.05
Nodes (35): solve_greedy(), load(), _f_sqrt(), fair_objective(), _fmt(), main(), _make_charts(), mean() (+27 more)

### Community 56 - "Healthcheck Config"
Cohesion: 0.40
Nodes (5): interval, retries, test, timeout, healthcheck

### Community 57 - "Functional Requirements Progress"
Cohesion: 0.40
Nodes (4): Tier 1 9/14 FR Complete 06/10/2026, CRUD Subjects FR 6 Partial Update exclude_unset, Dashboard Widgets FR 8-9, Data Export Delete FR 14

### Community 59 - "Docker Compose Services"
Cohesion: 0.50
Nodes (3): services, volumes, postgres_data

### Community 62 - "Tier1 Database Logging"
Cohesion: 0.67
Nodes (3): Nine Database Tables PostgreSQL 15, Tier 1 Backend Foundations 14 Endpoints, Logging Feature FR 3-5

### Community 68 - "3. Metrics (Các chỉ số so sánh)"
Cohesion: 0.13
Nodes (14): 1.1. Các trường dữ liệu (Schema), 1.2. Các kịch bản kiểm thử (Test Scenarios), 1. Synthetic Dataset (Tập dữ liệu giả lập), 2.1. Mô tả Baseline (Greedy), 2.2. Sự khác biệt cốt lõi (Greedy vs. LP Solver), 2. Baseline (Thuật toán Đối chứng), 3.1. Tỷ lệ tìm thấy lịch (Feasibility Rate) - *Càng cao càng tốt*, 3.2. Tổng số giờ thiếu hụt (Total Deadline Shortfall) - *Càng thấp càng tốt* (+6 more)

### Community 99 - "User"
Cohesion: 0.33
Nodes (7): create_subject(), delete_subject(), get_subject(), list_subjects(), _to_response(), update_subject(), User

### Community 100 - "devDependencies"
Cohesion: 0.18
Nodes (11): devDependencies, @types/react@^18.2.43, @types/react-dom@^18.2.17, typescript@^5.3.3, vite@^5.0.8, @vitejs/plugin-react@^4.2.1, @types/react, @types/react-dom (+3 more)

### Community 102 - "scripts"
Cohesion: 0.40
Nodes (5): scripts, build, dev, lint, preview

## Knowledge Gaps
- **55 isolated node(s):** `Time Slots tod_factor Grid`, `Risk Classification Low/Moderate/High`, `Full Regression 146 Tests`, `SchedulePage.tsx Calendar View and Breakdown Cards`, `QuickMoodBar` (+50 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 496 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **59 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `User` connect `User` to `Logging API`, `Auth API Backend`, `Test Fixtures Core`, `Assignments API`, `delete_user_data`, `User Data Repositories`, `schedule_service.py`, `Schedule Generate API`, `Dashboard Backend Services`, `security.py`, `TestAccountDeletion`, `Consent API`, `Feedback API`?**
  _High betweenness centrality (0.052) - this node is a cross-community bridge._
- **Are the 48 inferred relationships involving `User` (e.g. with `create_assignment()` and `delete_assignment()`) actually correct?**
  _`User` has 48 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Time Slots tod_factor Grid`, `Risk Classification Low/Moderate/High`, `Full Regression 146 Tests` to the rest of the system?**
  _55 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Logging API` be split into smaller, more focused modules?**
  _Cohesion score 0.10303030303030303 - nodes in this community are weakly interconnected._
- **Why does `LogRepository` connect `Logging API` to `User Data Repositories`, `schedule_service.py`, `SubjectRepository`?**
  _High betweenness centrality (0.028) - this node is a cross-community bridge._
- **Are the 15 inferred relationships involving `LogRepository` (e.g. with `delete_mood()` and `delete_sleep()`) actually correct?**
  _`LogRepository` has 15 INFERRED edges - model-reasoned connections that need verification._
- **Should `Frontend Auth App` be split into smaller, more focused modules?**
  _Cohesion score 0.14112903225806453 - nodes in this community are weakly interconnected._