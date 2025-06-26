# Task Completion Checklist

## After Making Code Changes

### 1. Code Quality Checks
- [ ] Verify all imports are present and correct
- [ ] Check that new code follows existing patterns
- [ ] Ensure proper error handling with try-except blocks
- [ ] Add appropriate logging statements
- [ ] Verify thread safety for any shared state

### 2. Testing
- [ ] Test the bot with minimal configuration (1 browser, short run)
- [ ] Verify new features work as expected
- [ ] Check that existing functionality isn't broken
- [ ] Monitor logs for any new errors or warnings

### 3. Performance Validation
- [ ] Check that changes don't significantly impact speed
- [ ] Verify memory usage remains reasonable
- [ ] Ensure browser creation/cleanup works properly

### 4. Documentation Updates
- [ ] Update CLAUDE.md if architecture changes
- [ ] Add comments for complex new logic
- [ ] Update docstrings for modified methods

### 5. Configuration
- [ ] Update .env.example if new environment variables added
- [ ] Update bot_config.json if new configuration options added
- [ ] Document any new configuration requirements

### 6. Pre-commit Checks
```bash
# Check for syntax errors
python3 -m py_compile fansale.py

# Quick run test (interrupt after successful start)
python3 fansale.py

# Check logs for errors
tail -n 50 fansale_bot.log
```

### 7. File Cleanup
- [ ] Remove any test screenshots
- [ ] Clear test browser profiles if needed
- [ ] Reset statistics file if doing major testing

## Important Reminders
- The bot operates WITHOUT login - don't add login requirements
- Speed is critical - minimize delays in ticket detection/purchase flow
- Thread safety is essential - use locks for shared state
- Browser stealth is important - maintain anti-detection measures