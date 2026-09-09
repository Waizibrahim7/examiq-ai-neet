# Rank Prediction Methodology

## Objective

The Rank Prediction module estimates a student's expected All India Rank based on exam marks and historical marks-vs-rank data.

## Input

- Student marks
- Historical rank data
- Exam type

## Historical Rank Data

The prototype uses a sample NEET rank dataset stored in:

`datasets/neet_rank_data.csv`

Each row contains:

- Marks
- AIR

## Processing

1. The student enters marks in the Rank Predictor page.
2. The system loads historical rank data from the CSV file.
3. The system compares the entered marks with the nearest historical marks range.
4. If the entered marks fall between two data points, the system estimates rank using linear interpolation.
5. The system assigns a performance category based on marks.
6. The system estimates the approximate percentage of students the user performed better than.

## Output

- Predicted AIR
- Performance category
- Approximate student comparison percentage
- Expected competition level

## Performance Categories

- Excellent: 650 and above
- Very Good: 600 to 649
- Good: 550 to 599
- Average: 500 to 549
- Needs Improvement: below 500

## Current Limitations

This is a prototype module. The prediction is based on sample historical data and should not be treated as an official rank prediction. Accuracy can be improved later by adding larger official datasets from multiple exam years.

## Future Improvements

- Add separate datasets for JEE and CUET
- Use real historical counselling data
- Predict college admission chances
- Show rank range instead of a single rank
- Connect marks automatically from the Result Dashboard
