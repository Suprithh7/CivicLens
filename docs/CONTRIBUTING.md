# Contributing to CivicLens AI

Thank you for considering contributing to CivicLens AI! This project aims to make government policies accessible to millions of citizens.

---

## 🎯 **How You Can Help**

We welcome contributions in these areas:

### 1. **Code Contributions**
- Backend APIs (FastAPI)
- Frontend features (React)
- AI/ML improvements (RAG pipeline)
- Blockchain integration (Solidity)

### 2. **Non-Code Contributions**
- Documentation improvements
- Translation (Hindi, Tamil, Bengali, etc.)
- UI/UX design
- Testing with real government PDFs

---

## 🛠️ **Development Setup**

### Prerequisites
- Python 3.10+
- Node.js 18+
- PostgreSQL 14+
- Git

### Setup Steps
```bash
# 1. Fork and clone
git clone https://github.com/YOUR_USERNAME/CivicLens.git
cd CivicLens

# 2. Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Frontend setup
cd ../frontend
npm install

# 4. Database setup
createdb civiclens_dev

# 5. Run locally
# Terminal 1: Backend
cd backend && uvicorn main:app --reload

# Terminal 2: Frontend
cd frontend && npm start
```

---

## 📝 **Contribution Workflow**

### 1. **Pick an Issue**
- Check [Issues](https://github.com/yourusername/CivicLens/issues)
- Comment "I'd like to work on this"
- Wait for assignment

### 2. **Create a Branch**
```bash
git checkout -b feature/your-feature-name
# Examples:
# - feature/add-hindi-translation
# - fix/pdf-upload-error
# - docs/update-readme
```

### 3. **Make Changes**
- Follow coding standards (below)
- Write tests if applicable
- Update documentation

### 4. **Commit**
```bash
git add .
git commit -m "feat: add Hindi translation support"
```

**Commit Message Format:**
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `test:` Tests
- `refactor:` Code refactoring

### 5. **Push and Create PR**
```bash
git push origin feature/your-feature-name
```
Then open a Pull Request on GitHub.

---

## 📐 **Coding Standards**

### Python (Backend)
```python
# Use type hints
def get_policy(policy_id: int) -> dict:
    pass

# Use docstrings
def simplify_text(text: str) -> str:
    """
    Simplifies complex policy text using LLM.
    
    Args:
        text: Raw policy text
    
    Returns:
        Simplified text in plain language
    """
    pass

# Follow PEP 8
# Use black for formatting: black .
```

### JavaScript (Frontend)
```javascript
// Use functional components
const PolicyCard = ({ policy }) => {
  return <div>{policy.title}</div>;
};

// Use meaningful names
const fetchPolicies = async () => { ... };

// Use Prettier for formatting
```

### SQL
```sql
-- Use descriptive table/column names
CREATE TABLE policy_documents (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL
);

-- Add indexes for performance
CREATE INDEX idx_policy_title ON policy_documents(title);
```

---

## 🧪 **Testing**

### Backend Tests
```bash
cd backend
pytest tests/
```

### Frontend Tests
```bash
cd frontend
npm test
```

**We aim for 80%+ code coverage.**

---

## 🌍 **Translation Guidelines**

If adding a new language:

1. Add language code to `frontend/src/i18n/locales/`
2. Translate these keys:
   - `common.upload`
   - `common.search`
   - `policy.title`
   - `eligibility.check`

3. Test with native speakers

---

## 🚫 **What NOT to Do**

- ❌ Don't commit API keys or secrets
- ❌ Don't push large files (>10MB)
- ❌ Don't break existing tests
- ❌ Don't submit PRs without descriptions

---

## 🏆 **Recognition**

All contributors will be:
- Listed in `CONTRIBUTORS.md`
- Mentioned in release notes
- Eligible for swag (stickers, t-shirts)

---

## 📧 **Questions?**

- **GitHub Discussions:** [Link]
- **Discord:** [Link]
- **Email:** contribute@civiclens.ai

---

**Remember: Every line of code you write could help a citizen access benefits they deserve. Thank you! 🙏**
