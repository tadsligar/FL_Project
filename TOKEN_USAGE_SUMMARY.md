# Token Usage Analysis - All Architectures

**Dataset:** MedQA US Test Set (1,071 questions)
**Model:** Qwen 2.5 32B (Q4_K_M quantization)
**Date:** December 2024

---

## 📊 FULL DATASET TOKEN USAGE (1,071 Questions)

### **Token Efficiency Ranking** (Lower is better)

| Rank | Architecture | Tokens/Q | vs Zero-Shot | Accuracy | Full Dataset? |
|------|-------------|----------|--------------|----------|---------------|
| 1 | **Zero-Shot** | **513** | **1.0x** | 52.9% | ✅ YES |
| 2 | **Zero-Shot (Physician)** | **521** | **1.0x** | 59.2% | ✅ YES |
| 3 | **Progressive Temperature** | **7,089** | **13.8x** | 72.2% | ✅ YES |
| 4 | **Progressive Temp Parallel** | **11,049** | **21.6x** | 73.5% | ✅ YES |
| 5 | **Debate (Standard)** | **13,291** | **25.9x** | 56.1% | ✅ YES |

---

## 💰 ACCURACY VS. COST ANALYSIS

### **Cost-Effectiveness Rankings** (Accuracy per 1000 tokens)

| Architecture | Accuracy | Tokens/Q | Accuracy per 1K tokens | Cost-Effectiveness Rank |
|-------------|----------|----------|------------------------|------------------------|
| **Zero-Shot (Physician)** | 59.2% | 521 | **113.6** | 🥇 1st |
| **Zero-Shot** | 52.9% | 513 | **103.1** | 2nd |
| **Progressive Temperature** | 72.2% | 7,089 | **10.2** | 3rd |
| **Progressive Temp Parallel** | 73.5% | 11,049 | **6.7** | 4th |
| **Debate (Standard)** | 56.1% | 13,291 | **4.2** | 5th |

**Interpretation:**
- Zero-Shot methods are most cost-effective but less accurate
- Progressive Temperature offers best balance of accuracy and cost
- Progressive Temp Parallel: highest accuracy but 21.6x cost of baseline

---

## 📈 DETAILED TOKEN USAGE BY ARCHITECTURE

### **1. Progressive Temperature Parallel** ⭐ HIGHEST ACCURACY
- **Average:** 11,049 tokens/question
- **Range:** 11,049 - 11,050 tokens/q (extremely consistent)
- **Total (2 runs):** 23,667,589 tokens
- **Cost vs Zero-Shot:** 21.6x
- **Accuracy:** 73.5%
- **Accuracy gain per 1000 tokens:** 6.7%
- **Status:** ✅ 2 full runs complete

**Breakdown:**
- Run 1: 11,050 tokens/q (11,834,396 total)
- Run 2: 11,049 tokens/q (11,833,193 total)
- **Variance:** <1 token (exceptional consistency)

### **2. Progressive Temperature (Baseline)**
- **Average:** 7,089 tokens/question
- **Range:** 7,078 - 7,097 tokens/q
- **Total (3 runs):** 22,776,331 tokens
- **Cost vs Zero-Shot:** 13.8x
- **Accuracy:** 72.2%
- **Accuracy gain per 1000 tokens:** 10.2%
- **Status:** ✅ 3 full runs complete

**Breakdown:**
- Run 1: 7,097 tokens/q (7,600,608 total)
- Run 2: 7,078 tokens/q (7,580,548 total)
- Run 3: 7,092 tokens/q (7,595,175 total)
- **Variance:** 19 tokens (very consistent)

### **3. Debate (Standard)**
- **Average:** 13,291 tokens/question
- **Range:** 13,205 - 13,337 tokens/q
- **Total (3 runs):** 42,702,643 tokens
- **Cost vs Zero-Shot:** 25.9x
- **Accuracy:** 56.1%
- **Accuracy gain per 1000 tokens:** 4.2%
- **Status:** ✅ 3 full runs complete (but poor performance)

**Breakdown:**
- Run 1: 13,337 tokens/q
- Run 2: 13,329 tokens/q
- Run 3: 13,205 tokens/q
- **Variance:** 132 tokens

**Note:** Debate uses most tokens but achieves only 56.1% accuracy - **not cost-effective**

### **4. Zero-Shot (Physician Role)**
- **Average:** 521 tokens/question
- **Total:** 557,862 tokens
- **Cost vs Zero-Shot:** 1.0x
- **Accuracy:** 59.2%
- **Accuracy gain per 1000 tokens:** 113.6%
- **Status:** ✅ 1 full run

**Most cost-effective per accuracy point**

### **5. Zero-Shot (Standard)**
- **Average:** 513 tokens/question
- **Total:** 549,070 tokens
- **Cost vs Zero-Shot:** 1.0x (baseline)
- **Accuracy:** 52.9%
- **Status:** ✅ Multiple runs

**Cheapest but lowest accuracy**

---

## 💡 KEY INSIGHTS

### **1. Cost vs. Accuracy Trade-offs**

```
Zero-Shot:           513 tokens/q  →  52.9% accuracy  (baseline)
Zero-Shot Physician: 521 tokens/q  →  59.2% accuracy  (+6.3% for +8 tokens)
Prog Temp:         7,089 tokens/q  →  72.2% accuracy  (+19.3% for 13.8x cost)
Prog Temp Parallel:11,049 tokens/q →  73.5% accuracy  (+20.6% for 21.6x cost)
Debate:           13,291 tokens/q  →  56.1% accuracy  (+3.2% for 25.9x cost)
```

### **2. Marginal Cost of Improvements**

**Zero-Shot → Zero-Shot Physician:**
- Cost increase: +8 tokens/q (+1.6%)
- Accuracy gain: +6.3%
- **Best ROI:** 0.79% accuracy per 1 token

**Zero-Shot → Progressive Temperature:**
- Cost increase: +6,576 tokens/q (+1,282%)
- Accuracy gain: +19.3%
- **ROI:** 0.0029% accuracy per 1 token

**Progressive Temp → Progressive Temp Parallel:**
- Cost increase: +3,960 tokens/q (+55.9%)
- Accuracy gain: +1.3%
- **ROI:** 0.00033% accuracy per 1 token
- **Marginal cost:** 3,046 tokens per 1% accuracy gain

### **3. Efficiency by Use Case**

**For Maximum Cost-Efficiency:**
- **Winner:** Zero-Shot (Physician) - 113.6% per 1K tokens
- Use when: Budget constrained, acceptable to have 59% accuracy

**For Balanced Performance:**
- **Winner:** Progressive Temperature - 10.2% per 1K tokens
- Use when: Need 72% accuracy, moderate budget (13.8x baseline)

**For Maximum Accuracy:**
- **Winner:** Progressive Temp Parallel - 6.7% per 1K tokens
- Use when: Need highest accuracy (73.5%), willing to pay 21.6x cost

**Avoid:**
- Debate methods - 25.9x cost for only 56% accuracy (worse than Zero-Shot Physician at 1x cost)

---

## 📉 TOKEN USAGE BY CATEGORY

### **Simple Baselines** (500-600 tokens/q)
- Zero-Shot: 513 tokens/q (52.9% accuracy)
- Zero-Shot Physician: 521 tokens/q (59.2% accuracy)
- **Cost:** 1.0x baseline
- **Best for:** Budget constraints

### **Progressive Temperature Family** (7,000-11,000 tokens/q)
- Progressive Temperature: 7,089 tokens/q (72.2% accuracy)
- Progressive Temp Parallel: 11,049 tokens/q (73.5% accuracy)
- **Cost:** 13.8x - 21.6x baseline
- **Best for:** High accuracy requirements

### **Debate Methods** (13,000-14,000 tokens/q)
- Debate Standard: 13,291 tokens/q (56.1% accuracy)
- **Cost:** 25.9x baseline
- **Best for:** Nothing (poor accuracy for high cost)

---

## 🎯 RECOMMENDATIONS

### **For Production Deployment:**

1. **If budget is primary concern:**
   - Use **Zero-Shot (Physician)**: 521 tokens/q, 59.2% accuracy
   - Cost: 1x baseline
   - Best cost-effectiveness ratio

2. **If accuracy is important but cost matters:**
   - Use **Progressive Temperature**: 7,089 tokens/q, 72.2% accuracy
   - Cost: 13.8x baseline
   - Good balance of accuracy and cost

3. **If maximum accuracy is required:**
   - Use **Progressive Temp Parallel**: 11,049 tokens/q, 73.5% accuracy
   - Cost: 21.6x baseline
   - Highest accuracy, exceptional stability

4. **Avoid:**
   - Debate methods: High cost (25.9x) for poor accuracy (56%)
   - Not cost-effective in any scenario

### **Cost Scaling:**

For 1 million questions:
- **Zero-Shot:** 513M tokens
- **Zero-Shot Physician:** 521M tokens
- **Progressive Temp:** 7.1B tokens (13.8x)
- **Progressive Temp Parallel:** 11.0B tokens (21.6x)
- **Debate:** 13.3B tokens (25.9x)

---

## 📊 SUMMARY STATISTICS

### **Token Usage Range:**
- **Minimum:** 513 tokens/q (Zero-Shot)
- **Maximum:** 13,291 tokens/q (Debate)
- **Median:** 7,089 tokens/q (Progressive Temperature)
- **Range:** 12,778 tokens/q

### **Total Tokens Evaluated:**
- **Progressive Temperature family:** 46.4M tokens (5 runs × 1,071 q)
- **Debate methods:** 42.7M tokens (3 full runs)
- **Zero-Shot methods:** 1.1M tokens
- **Grand Total:** ~90M+ tokens across all experiments

---

## 🔍 TOKEN CONSISTENCY ANALYSIS

### **Most Consistent (Low Variance):**
1. **Progressive Temp Parallel:** <1 token variance
2. **Progressive Temp:** 19 tokens variance
3. **Debate:** 132 tokens variance

All architectures show excellent token consistency across runs, indicating:
- Predictable computational costs
- Reliable resource planning
- Stable implementation

---

**Conclusion:** Progressive Temperature Parallel offers the best accuracy (73.5%) at a reasonable cost (21.6x baseline). For budget-constrained scenarios, Zero-Shot Physician provides decent accuracy (59.2%) at baseline cost (1.0x).
