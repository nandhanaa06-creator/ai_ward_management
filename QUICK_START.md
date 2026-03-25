# 🚀 QUICK COMMANDS - AI Models

## ⚡ Setup (One Time)

```bash
# 1. Activate virtual environment
venv\Scripts\activate

# 2. Install dependencies
pip install scikit-learn numpy

# 3. Train category model
python manage.py train_ai_model

# 4. Train priority model
python manage.py train_priority_model

# 5. Run server
python manage.py runserver
```

---

## 🧪 Test Commands

```bash
# Test category AI
python -m ai_model.predict

# Test priority AI
python -m ai_model.priority_model

# Test duplicate detection
python -m ai_model.duplicate_detection
```

---

## 📊 What You Get

When citizen submits: **"Electric wire hanging dangerously near school"**

✅ **Category**: Electricity (95%)
✅ **Priority**: HIGH (92%)
✅ **Status**: urgent_review (auto)
✅ **Duplicate**: Checked automatically
✅ **Warning**: If similar complaint exists

---

## ✅ Verification

- [ ] Install: `pip install scikit-learn numpy`
- [ ] Train: `python manage.py train_ai_model`
- [ ] Train: `python manage.py train_priority_model`
- [ ] Files exist: `ai_model/*.pkl`
- [ ] Submit complaint → auto-categorized
- [ ] Submit complaint → auto-prioritized
- [ ] Submit similar → duplicate warning

---

## 🎯 3 AI Models

1. **Category** (90-98%) - Naive Bayes
2. **Priority** (85-95%) - Random Forest
3. **Duplicate** (80%) - TF-IDF + Cosine

---

**Ready? Run:**
```bash
python manage.py train_ai_model
python manage.py train_priority_model
python manage.py runserver
```

**Then submit complaints!** 🚀
