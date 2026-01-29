# Detailed Similarity Evaluation Results

Per-scene breakdown showing ground truth vs predicted similarity pairs.

## 3RSCAN

### 02b33dfb-be2b-2d54-92d2-cd012b2b3c40

**Validated Objects:** 14

**Metrics:**
- Ground Truth Pairs: 7
- Predicted Pairs: 3
- True Positives: 3
- False Positives: 0
- False Negatives: 4
- Precision: 1.000
- Recall: 0.429
- F1 Score: 0.600

**Ground Truth Pairs (7):**
- `(2, 3)` ✓ PREDICTED
- `(2, 7)` ✓ PREDICTED
- `(2, 10)` ✓ PREDICTED
- `(3, 7)` ✗ MISSED
- `(3, 10)` ✗ MISSED
- `(5, 22)` ✗ MISSED
- `(7, 10)` ✗ MISSED

**Predicted Pairs (3):**
- `(2, 3)` ✓ CORRECT
- `(2, 7)` ✓ CORRECT
- `(2, 10)` ✓ CORRECT

**Missed Pairs (False Negatives) (4):**
- `(3, 7)`
- `(3, 10)`
- `(5, 22)`
- `(7, 10)`

---

### 095821f7-e2c2-2de1-9568-b9ce59920e29

**Validated Objects:** 11

**Metrics:**
- Ground Truth Pairs: 2
- Predicted Pairs: 2
- True Positives: 2
- False Positives: 0
- False Negatives: 0
- Precision: 1.000
- Recall: 1.000
- F1 Score: 1.000

**Ground Truth Pairs (2):**
- `(2, 3)` ✓ PREDICTED
- `(8, 10)` ✓ PREDICTED

**Predicted Pairs (2):**
- `(2, 3)` ✓ CORRECT
- `(8, 10)` ✓ CORRECT

---

### 0958220d-e2c2-2de1-9710-c37018da1883

**Validated Objects:** 14

**Metrics:**
- Ground Truth Pairs: 2
- Predicted Pairs: 2
- True Positives: 2
- False Positives: 0
- False Negatives: 0
- Precision: 1.000
- Recall: 1.000
- F1 Score: 1.000

**Ground Truth Pairs (2):**
- `(6, 8)` ✓ PREDICTED
- `(10, 13)` ✓ PREDICTED

**Predicted Pairs (2):**
- `(6, 8)` ✓ CORRECT
- `(10, 13)` ✓ CORRECT

---

### 09582212-e2c2-2de1-9700-fa44b14fbded

**Validated Objects:** 14

**Metrics:**
- Ground Truth Pairs: 9
- Predicted Pairs: 1
- True Positives: 1
- False Positives: 0
- False Negatives: 8
- Precision: 1.000
- Recall: 0.111
- F1 Score: 0.200

**Ground Truth Pairs (9):**
- `(3, 4)` ✗ MISSED
- `(3, 5)` ✗ MISSED
- `(3, 16)` ✗ MISSED
- `(4, 5)` ✗ MISSED
- `(4, 16)` ✗ MISSED
- `(5, 16)` ✗ MISSED
- `(6, 8)` ✗ MISSED
- `(7, 8)` ✓ PREDICTED
- `(10, 13)` ✗ MISSED

**Predicted Pairs (1):**
- `(7, 8)` ✓ CORRECT

**Missed Pairs (False Negatives) (8):**
- `(3, 4)`
- `(3, 5)`
- `(3, 16)`
- `(4, 5)`
- `(4, 16)`
- `(5, 16)`
- `(6, 8)`
- `(10, 13)`

---

### 09582225-e2c2-2de1-9564-f6681ef5e511

**Validated Objects:** 7

**Metrics:**
- Ground Truth Pairs: 9
- Predicted Pairs: 1
- True Positives: 1
- False Positives: 0
- False Negatives: 8
- Precision: 1.000
- Recall: 0.111
- F1 Score: 0.200

**Ground Truth Pairs (9):**
- `(3, 4)` ✓ PREDICTED
- `(3, 5)` ✗ MISSED
- `(3, 16)` ✗ MISSED
- `(4, 5)` ✗ MISSED
- `(4, 16)` ✗ MISSED
- `(5, 16)` ✗ MISSED
- `(6, 8)` ✗ MISSED
- `(7, 8)` ✗ MISSED
- `(10, 13)` ✗ MISSED

**Predicted Pairs (1):**
- `(3, 4)` ✓ CORRECT

**Missed Pairs (False Negatives) (8):**
- `(3, 5)`
- `(3, 16)`
- `(4, 5)`
- `(4, 16)`
- `(5, 16)`
- `(6, 8)`
- `(7, 8)`
- `(10, 13)`

---

## SCANNET

### scene0000_00

**Validated Objects:** 14

**Metrics:**
- Ground Truth Pairs: 0
- Predicted Pairs: 1
- True Positives: 0
- False Positives: 1
- False Negatives: 0
- Precision: 0.000
- Recall: 0.000
- F1 Score: 0.000

**Ground Truth Pairs:** None (no similar objects)

**Predicted Pairs (1):**
- `(5, 6)` ✗ FALSE POSITIVE

---

### scene0001_00

**Validated Objects:** 14

**Metrics:**
- Ground Truth Pairs: 9
- Predicted Pairs: 3
- True Positives: 2
- False Positives: 1
- False Negatives: 7
- Precision: 0.667
- Recall: 0.222
- F1 Score: 0.333

**Ground Truth Pairs (9):**
- `(0, 1)` ✗ MISSED
- `(0, 8)` ✓ PREDICTED
- `(0, 9)` ✓ PREDICTED
- `(1, 8)` ✗ MISSED
- `(1, 9)` ✗ MISSED
- `(8, 9)` ✗ MISSED
- `(11, 12)` ✗ MISSED
- `(11, 13)` ✗ MISSED
- `(12, 13)` ✗ MISSED

**Predicted Pairs (3):**
- `(0, 8)` ✓ CORRECT
- `(0, 9)` ✓ CORRECT
- `(3, 4)` ✗ FALSE POSITIVE

**Missed Pairs (False Negatives) (7):**
- `(0, 1)`
- `(1, 8)`
- `(1, 9)`
- `(8, 9)`
- `(11, 12)`
- `(11, 13)`
- `(12, 13)`

---

### scene0002_00

**Validated Objects:** 14

**Metrics:**
- Ground Truth Pairs: 2
- Predicted Pairs: 1
- True Positives: 1
- False Positives: 0
- False Negatives: 1
- Precision: 1.000
- Recall: 0.500
- F1 Score: 0.667

**Ground Truth Pairs (2):**
- `(4, 9)` ✗ MISSED
- `(18, 19)` ✓ PREDICTED

**Predicted Pairs (1):**
- `(18, 19)` ✓ CORRECT

**Missed Pairs (False Negatives) (1):**
- `(4, 9)`

---

### scene0003_00

**Validated Objects:** 14

**Metrics:**
- Ground Truth Pairs: 9
- Predicted Pairs: 1
- True Positives: 1
- False Positives: 0
- False Negatives: 8
- Precision: 1.000
- Recall: 0.111
- F1 Score: 0.200

**Ground Truth Pairs (9):**
- `(0, 16)` ✗ MISSED
- `(0, 18)` ✗ MISSED
- `(0, 19)` ✓ PREDICTED
- `(2, 3)` ✗ MISSED
- `(2, 5)` ✗ MISSED
- `(3, 5)` ✗ MISSED
- `(16, 18)` ✗ MISSED
- `(16, 19)` ✗ MISSED
- `(18, 19)` ✗ MISSED

**Predicted Pairs (1):**
- `(0, 19)` ✓ CORRECT

**Missed Pairs (False Negatives) (8):**
- `(0, 16)`
- `(0, 18)`
- `(2, 3)`
- `(2, 5)`
- `(3, 5)`
- `(16, 18)`
- `(16, 19)`
- `(18, 19)`

---

### scene0004_00

**Validated Objects:** 13

**Metrics:**
- Ground Truth Pairs: 30
- Predicted Pairs: 5
- True Positives: 5
- False Positives: 0
- False Negatives: 25
- Precision: 1.000
- Recall: 0.167
- F1 Score: 0.286

**Ground Truth Pairs (30):**
- `(0, 4)` ✗ MISSED
- `(1, 3)` ✗ MISSED
- `(5, 6)` ✗ MISSED
- `(5, 7)` ✗ MISSED
- `(5, 8)` ✗ MISSED
- `(5, 9)` ✓ PREDICTED
- `(5, 10)` ✓ PREDICTED
- `(5, 11)` ✓ PREDICTED
- `(5, 12)` ✗ MISSED
- `(6, 7)` ✗ MISSED
- `(6, 8)` ✓ PREDICTED
- `(6, 9)` ✗ MISSED
- `(6, 10)` ✗ MISSED
- `(6, 11)` ✗ MISSED
- `(6, 12)` ✗ MISSED
- `(7, 8)` ✗ MISSED
- `(7, 9)` ✗ MISSED
- `(7, 10)` ✗ MISSED
- `(7, 11)` ✗ MISSED
- `(7, 12)` ✓ PREDICTED
- `(8, 9)` ✗ MISSED
- `(8, 10)` ✗ MISSED
- `(8, 11)` ✗ MISSED
- `(8, 12)` ✗ MISSED
- `(9, 10)` ✗ MISSED
- `(9, 11)` ✗ MISSED
- `(9, 12)` ✗ MISSED
- `(10, 11)` ✗ MISSED
- `(10, 12)` ✗ MISSED
- `(11, 12)` ✗ MISSED

**Predicted Pairs (5):**
- `(5, 9)` ✓ CORRECT
- `(5, 10)` ✓ CORRECT
- `(5, 11)` ✓ CORRECT
- `(6, 8)` ✓ CORRECT
- `(7, 12)` ✓ CORRECT

**Missed Pairs (False Negatives) (25):**
- `(0, 4)`
- `(1, 3)`
- `(5, 6)`
- `(5, 7)`
- `(5, 8)`
- `(5, 12)`
- `(6, 7)`
- `(6, 9)`
- `(6, 10)`
- `(6, 11)`
- `(6, 12)`
- `(7, 8)`
- `(7, 9)`
- `(7, 10)`
- `(7, 11)`
- `(8, 9)`
- `(8, 10)`
- `(8, 11)`
- `(8, 12)`
- `(9, 10)`
- `(9, 11)`
- `(9, 12)`
- `(10, 11)`
- `(10, 12)`
- `(11, 12)`

---

### scene0005_00

**Validated Objects:** 14

**Metrics:**
- Ground Truth Pairs: 8
- Predicted Pairs: 5
- True Positives: 3
- False Positives: 2
- False Negatives: 5
- Precision: 0.600
- Recall: 0.375
- F1 Score: 0.462

**Ground Truth Pairs (8):**
- `(3, 4)` ✓ PREDICTED
- `(3, 5)` ✓ PREDICTED
- `(3, 16)` ✓ PREDICTED
- `(4, 5)` ✗ MISSED
- `(4, 16)` ✗ MISSED
- `(5, 16)` ✗ MISSED
- `(6, 8)` ✗ MISSED
- `(10, 13)` ✗ MISSED

**Predicted Pairs (5):**
- `(2, 12)` ✗ FALSE POSITIVE
- `(3, 4)` ✓ CORRECT
- `(3, 5)` ✓ CORRECT
- `(3, 16)` ✓ CORRECT
- `(14, 15)` ✗ FALSE POSITIVE

**Missed Pairs (False Negatives) (5):**
- `(4, 5)`
- `(4, 16)`
- `(5, 16)`
- `(6, 8)`
- `(10, 13)`

---

### scene0006_00

**Validated Objects:** 14

**Metrics:**
- Ground Truth Pairs: 4
- Predicted Pairs: 2
- True Positives: 2
- False Positives: 0
- False Negatives: 2
- Precision: 1.000
- Recall: 0.500
- F1 Score: 0.667

**Ground Truth Pairs (4):**
- `(1, 2)` ✓ PREDICTED
- `(5, 6)` ✓ PREDICTED
- `(6, 8)` ✗ MISSED
- `(10, 13)` ✗ MISSED

**Predicted Pairs (2):**
- `(1, 2)` ✓ CORRECT
- `(5, 6)` ✓ CORRECT

**Missed Pairs (False Negatives) (2):**
- `(6, 8)`
- `(10, 13)`

---

### scene0008_00

**Validated Objects:** 15

**Metrics:**
- Ground Truth Pairs: 5
- Predicted Pairs: 3
- True Positives: 3
- False Positives: 0
- False Negatives: 2
- Precision: 1.000
- Recall: 0.600
- F1 Score: 0.750

**Ground Truth Pairs (5):**
- `(0, 1)` ✓ PREDICTED
- `(3, 5)` ✓ PREDICTED
- `(9, 14)` ✓ PREDICTED
- `(20, 23)` ✗ MISSED
- `(25, 31)` ✗ MISSED

**Predicted Pairs (3):**
- `(0, 1)` ✓ CORRECT
- `(3, 5)` ✓ CORRECT
- `(9, 14)` ✓ CORRECT

**Missed Pairs (False Negatives) (2):**
- `(20, 23)`
- `(25, 31)`

---

## Overall Summary

- **Total Scenes:** 13
- **Total Ground Truth Pairs:** 96
- **Total Predicted Pairs:** 30
- **Total True Positives:** 26
- **Total False Positives:** 4
- **Total False Negatives:** 70

**Aggregate Metrics (micro-averaged):**
- Precision: 0.867 (86.7%)
- Recall: 0.271 (27.1%)
- F1 Score: 0.413
