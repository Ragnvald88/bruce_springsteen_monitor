# Task Completion Checklist

## Before Committing Code

### 1. Code Quality
- [ ] Code follows PEP 8 style guidelines
- [ ] No syntax errors or import issues
- [ ] Removed debug print statements
- [ ] Added appropriate logging statements
- [ ] Docstrings for new methods/classes

### 2. Testing
- [ ] Test basic functionality manually
- [ ] Test with different configurations (1-3 browsers)
- [ ] Test error handling (network issues, timeouts)
- [ ] Verify filter functionality works correctly
- [ ] Check performance metrics are accurate

### 3. Dependencies
- [ ] Update requirements.txt if new packages added
- [ ] Verify all imports are used
- [ ] Remove unused imports
- [ ] Check compatibility with Python 3.8+

### 4. Environment
- [ ] Sensitive data in .env, not in code
- [ ] Update .env.example if new variables added
- [ ] No hardcoded credentials or URLs

### 5. Documentation
- [ ] Update README.md if functionality changed
- [ ] Update claude.md for AI assistant reference
- [ ] Add comments for complex logic
- [ ] Update CHANGELOG.md with changes

### 6. Performance
- [ ] No unnecessary sleeps or waits
- [ ] Efficient selectors for elements
- [ ] Proper resource cleanup (browsers, threads)
- [ ] Memory usage is reasonable

### 7. Anti-Detection
- [ ] Randomized wait times
- [ ] Human-like interaction patterns
- [ ] Proper user agent and headers
- [ ] Session rotation working

## Final Steps
```bash
# Format code (if black installed)
black *.py

# Clean up
rm -rf __pycache__
rm -rf .pytest_cache

# Git commands
git add .
git status
git commit -m "descriptive message"
git push
```