# Day 2 (Thu 8 Oct): data, decision prompt, screens

Goal by end of day: seed data is in BigQuery, the Decision Agent prompt works in AI Studio on the example JSON,
and the dashboard and task screens render the example contract data on the deployed URL.

First, finish any leftover Day 1 items: Cloud Run URL shows "API connected", budget alert is set, teammates have
access, and `grep -h '"name"' contracts/*.json` prints at_risk_batch, decision_output, option_results (in that order).

## Person A: seed data and baseline
1. Generate the data (needs only python3):

       python3 data/generate_seed.py

2. Make sure the BigQuery dataset exists (use the real project id, not the project name):

       bq --location=asia-south1 mk --dataset PROJECT_ID:retail_stock

3. Load the tables:

       sh data/load_to_bigquery.sh

   Check with `bq ls PROJECT_ID:retail_stock` (5 tables), and run a sample query in the BigQuery console.
4. Run the baseline: `python3 agents/baseline.py`
5. Write down the assumptions you are making (elasticity, transfer cost, handling cost, salvage value) in docs/assumptions.md.

Done when: 5 tables are queryable in BigQuery and baseline_results.csv exists.

## Person B: Decision Agent prompt and API skeleton
1. Open agents/decision_prompt.md and agents/decision_schema.json.
2. In AI Studio, paste the system instruction, turn on structured output with the schema, and test with the
   example inputs in contracts/at_risk_batch.json and contracts/option_results.json. Work through the test checklist.
3. Add an API route that returns mock data in the decision_output shape (for example, POST /api/decide returning
   contracts/decision_output.json). Real calls come on Day 3 to 4.
4. Only you call the Gemini API. Save good responses in docs/ so others can use them without spending the free tier.
5. Keep the API key out of the repo; read it from an environment variable or Secret Manager.

Done when: the prompt returns valid schema-conformant JSON on the example data, and the mock route is deployed.

## Person C: screens on example data
1. Build the three screens against GET /api/demo: (1) impact dashboard with KPI cards and a baseline-vs-agent chart,
   (2) at-risk batch list with the options table and the recommendation, (3) staff task view.
2. Deploy to Cloud Run and check the URL on your phone.
3. List the data fields you need that are not in the contracts yet (for example, a list of batches, not just one) and
   send them to A and B today. Contract changes need all three of you to agree.

Done when: all three screens render example data from the deployed URL.

## Everyone: evening check (15 minutes)
- Does what A produces (tables, option results) match what B expects?
- Does what B produces (decision output) match what C displays?
- Agree on the one thing that must work by the Day 5 checkpoint: the yogurt scenario from data to dashboard.

## Notes on the baseline (read this)
- The contract files contain EXAMPLE numbers (for example, a large improvement over the baseline). They are placeholders.
  The simulated numbers will differ. After Day 4, regenerate the contracts from real calculator output.
- The baseline is a fixed 30% markdown when 3 days remain, with no transfers. In the simulation it earns slightly LESS
  than doing nothing across the at-risk batches: it loses money on 10 of 14 batches (mildly overstocked ones, where
  discounting gives away margin on units that would have sold anyway) and helps the heavily overstocked ones such as the
  yogurt. This held for every demand-response assumption tested (elasticity 1.5 to 5).
- So report TWO baselines in the demo: "do nothing" and "fixed 30% markdown". Judges will ask about a strawman.
- The demand response (elasticity 2.5) is an assumption, not measured. Say so, and show the sensitivity.
  Change it with: ELASTICITY=3.5 python3 agents/baseline.py
- Distances are placeholders; replace with Maps Distance Matrix values on Day 4.
