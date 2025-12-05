# LLaVA-Med v1.5 Setup Guide

## What is LLaVA-Med?

**LLaVA-Med** (Large Language and Vision Assistant for Medicine) is a multimodal model specifically fine-tuned for medical applications.

### Key Features:
- 🏥 **Medical fine-tuning** on biomedical literature and image-text pairs
- 👁️ **Vision-language** capabilities (can process medical images)
- 📊 Based on LLaVA 1.5 architecture
- 🔬 Trained on medical conversations and visual reasoning

### Model Specifications:
- **Base**: LLaVA 1.5 (Vicuna-7B or 13B + CLIP vision encoder)
- **Training**: PMC-15M (medical image-text pairs) + medical instruction tuning
- **Size**: 7B or 13B parameter variants
- **Modalities**: Text + Images

---

## ⚠️ Important: Should You Use LLaVA-Med for MedQA?

### Current MedQA Task:
- ✅ Text-only clinical questions
- ❌ No medical images
- ✅ Clinical reasoning required
- ❌ No visual understanding needed

### LLaVA-Med Strengths:
- ✅ Medical domain knowledge
- ✅ Clinical terminology
- ⚠️ **Vision capabilities (unused for MedQA)**
- ⚠️ Based on smaller base model (7B-13B)

### Better Alternatives for Text-Only MedQA:

| Model | Size | Medical Focus | Image Support | Text-Only Performance |
|-------|------|---------------|---------------|----------------------|
| **LLaVA-Med** | 7-13B | ⭐⭐⭐⭐⭐ | ✅ Yes | ⭐⭐⭐ Good |
| **Meditron:70B** | 70B | ⭐⭐⭐⭐⭐ | ❌ No | ⭐⭐⭐⭐⭐ Excellent |
| **Llama3:70B** | 70B | ⭐⭐⭐ General | ❌ No | ⭐⭐⭐⭐⭐ Excellent |
| **Mixtral:8x7B** | 47B | ⭐⭐⭐ General | ❌ No | ⭐⭐⭐⭐ Very Good |

---

## My Honest Assessment

### For Your Current Project (Text-Only MedQA):

**LLaVA-Med is NOT the best choice because:**

1. ❌ **Vision capabilities unused** - MedQA has no images
2. ❌ **Smaller model** - 7B/13B vs 70B available alternatives
3. ❌ **Less reasoning power** - Smaller parameter count limits complex reasoning
4. ⚠️ **No advantage over Meditron** - Meditron is also medical-focused but larger

**Better options:**
1. **Meditron:70B** - Medical + Large (best of both worlds)
2. **Llama3:70B** - General large model (excellent reasoning)
3. **Mixtral:8x7B** - Fast and capable

### When LLaVA-Med WOULD Be Perfect:

If your project included:
- 📊 Analyzing chest X-rays
- 🫀 Interpreting ECGs
- 🧠 Reading CT/MRI scans
- 🔬 Understanding pathology slides
- 📈 Mixed text + image clinical cases

---

## If You Still Want to Use LLaVA-Med

### Reasons You Might Choose It Anyway:

1. ✅ **Future-proofing** - Plan to add image tasks later
2. ✅ **Medical specificity** - Domain-specific fine-tuning
3. ✅ **Novel approach** - Using multimodal model for text-only (interesting for paper)
4. ✅ **Smaller footprint** - 7B fits easily on your 4090

### Setup Instructions:

#### Check Availability in Ollama

```bash
# Search for LLaVA models
ollama search llava

# As of now, Ollama has:
# - llava:7b (general LLaVA)
# - llava:13b (general LLaVA)
# - llava:34b (larger variant)

# LLaVA-Med specifically may not be in Ollama registry yet
```

#### Option 1: Use General LLaVA (if Med not available)

```bash
# Pull LLaVA (general, not medical-specific)
ollama pull llava:13b

# This is NOT LLaVA-Med, just regular LLaVA
# Medical fine-tuning is missing
```

#### Option 2: Download LLaVA-Med from Hugging Face

LLaVA-Med is available at: `https://huggingface.co/microsoft/llava-med-v1.5-mistral-7b`

```bash
# Install transformers
pip install transformers torch pillow

# Download model
python -c "
from transformers import AutoTokenizer, AutoModelForCausalLM
model = AutoModelForCausalLM.from_pretrained('microsoft/llava-med-v1.5-mistral-7b')
tokenizer = AutoTokenizer.from_pretrained('microsoft/llava-med-v1.5-mistral-7b')
"
```

#### Option 3: Use vLLM with LLaVA-Med

```bash
# Install vLLM with vision support
pip install vllm[vision]

# Serve LLaVA-Med
vllm serve microsoft/llava-med-v1.5-mistral-7b \
  --port 8000 \
  --trust-remote-code
```

---

## Configuration for LLaVA-Med

I'll create a config assuming you can get it running:

```yaml
# configs/llava_med.yaml
provider: "vllm"  # or "llamacpp" depending on setup
model: "microsoft/llava-med-v1.5-mistral-7b"
temperature: 0.3
max_output_tokens: 800

budgets:
  timeout_seconds: 120

logging:
  traces_dir: "runs/llava_med"
```

---

## Performance Expectations

### LLaVA-Med 7B on RTX 4090:

| Metric | Value |
|--------|-------|
| VRAM Usage | ~8GB |
| Speed | 30-50 tok/s |
| Case Time | ~2-3 min |
| Quality (estimated) | 60-70% on MedQA |

**Compare to:**
- Llama3:70B: ~75-80% accuracy (but slower)
- Mixtral:8x7B: ~68-73% accuracy (similar speed)
- Meditron:70B: ~78-82% accuracy (medical + large)

---

## My Recommendation

### Don't Use LLaVA-Med for This Project

**Instead, use one of these:**

#### Option 1: Meditron:70B (Best for Medical + Text)

```bash
# Check if available
ollama search meditron

# If available:
ollama pull meditron:70b

# Use config
poetry run mas eval --config configs/meditron_70b.yaml --n 10
```

**Why?**
- ✅ Medical domain knowledge (like LLaVA-Med)
- ✅ 70B parameters (much better reasoning)
- ✅ Text-optimized (no wasted vision capabilities)
- ✅ Better for your task

#### Option 2: Llama3:70B (Best Overall)

```bash
ollama pull llama3:70b
poetry run mas eval --config configs/llama3_70b.yaml --n 10
```

**Why?**
- ✅ Excellent reasoning
- ✅ Large model (70B)
- ✅ Well-tested and reliable
- ✅ Good documentation

#### Option 3: Mixtral:8x7B (Best for Speed)

```bash
ollama pull mixtral:8x7b
poetry run mas eval --config configs/mixtral_8x7b.yaml --n 10
```

**Why?**
- ✅ Fast (3-4x faster than 70B)
- ✅ Good reasoning (between 8B and 70B)
- ✅ Perfect fit for 4090
- ✅ More iterations in 1 month

---

## Future Work: If You Want to Use LLaVA-Med Later

### Extend Your Project to Include Images

1. **Add Visual MedQA** - Some MedQA variants include images
2. **Radiology Cases** - Integrate chest X-ray interpretation
3. **Multimodal Reasoning** - Text + Image diagnostic cases

### Example Multimodal Case:

```python
# Future: Visual case with LLaVA-Med
case = {
    "question": "Patient with shortness of breath. See chest X-ray.",
    "image": "chest_xray.jpg",
    "options": ["A. Pneumonia", "B. CHF", "C. COPD", "D. PE"]
}

# LLaVA-Med can process both text and image
result = run_case_multimodal(case)
```

This would be a **great extension** for your project and perfect use of LLaVA-Med!

---

## Summary

### For Your Current Text-Only MedQA Project:

❌ **Don't use LLaVA-Med**
- Vision capabilities unused
- Smaller model (7-13B)
- Better alternatives exist

✅ **Use instead:**
1. **Meditron:70B** (if available) - Medical + Large
2. **Llama3:70B** - Excellent reasoning
3. **Mixtral:8x7B** - Fast + good quality

### For Future Multimodal Medical Project:

✅ **LLaVA-Med would be perfect!**
- Add medical imaging
- Radiology interpretation
- Visual + text reasoning
- Novel research direction

---

## What Should You Do?

Let me know:
1. **How much system RAM** do you have? (This determines if 70B will work)
2. **Do you want medical specificity** or general reasoning?
3. **Priority: Speed or Quality?**

Based on your answer, I'll recommend:
- **32GB+ RAM + Want Best Quality**: Meditron:70B or Llama3:70B
- **Any RAM + Want Speed**: Mixtral:8x7B
- **Want to try LLaVA-Med anyway**: I'll help you set it up (but know it's not optimal)

**My honest advice: Skip LLaVA-Med for now, use Mixtral:8x7B or Llama3:70B, and save LLaVA-Med for a future multimodal extension!**
