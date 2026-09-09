# College Prediction Methodology

## Objective

The College Prediction module recommends possible colleges after a student receives a score and predicted rank.

## Workflow

1. Student takes test.
2. Result dashboard calculates score.
3. Rank predictor estimates AIR.
4. College predictor compares AIR with historical cutoff data.
5. System recommends Safe, Moderate, and Dream colleges.

## Input

- Exam: NEET or JEE
- Marks
- Predicted rank
- Category
- Preferred state

## Data Source Plan

College cutoff data should come from official counselling sources wherever possible:

- MCC UG counselling for NEET AIQ, AIIMS, central universities, and deemed universities
- State counselling authorities for state quota medical colleges
- JoSAA opening and closing rank archive for IITs, NITs, IIITs, and GFTIs
- CSAB rounds for additional NIT, IIIT, and GFTI seats

The current prototype uses a small starter dataset stored in:

`datasets/college_cutoffs/college_cutoffs.xlsx`

## Update Frequency

The cutoff dataset should be updated:

- After every counselling round
- After final seat allotment
- Once every admission cycle for historical trend analysis

For a production system, the data should include year, round number, quota, branch/course, gender pool, and category.

## Filtering Decisions

Students should be able to filter by state because admission chances vary strongly between All India quota, home state quota, and state counselling rules.

Students should also filter by category because cutoff ranks differ for General, OBC, EWS, SC, ST, and PwD categories.

## Recommendation Labels

The system should show three recommendation types:

- Safe: predicted rank is better than or equal to the opening rank
- Moderate: predicted rank falls between opening and closing rank
- Dream: predicted rank is slightly outside the closing rank but still worth tracking

This helps students understand admission chances without treating the prediction as a guaranteed result.

## Current Prototype Logic

The prototype compares the predicted rank with historical opening and closing ranks:

- If predicted rank is less than or equal to opening rank, college is marked Safe.
- If predicted rank is between opening and closing rank, college is marked Moderate.
- If predicted rank is within 20 percent beyond closing rank, college is marked Dream.
- Otherwise, the college is not shown in recommendations.

## Future Improvements

- Connect predicted rank automatically from Rank Predictor
- Add JEE branch-level recommendations
- Add NEET course-level recommendations
- Add quota, round, gender, and year filters
- Show expected college range instead of only college list
- Generate a personalized PDF report
