# Week 5 - Proper Git Workflow (CORRECTED!)

## ⚠️ What Happened

I created all the Week 5 Day 1-2 files but forgot to create the feature branches FIRST! 
The files are sitting in the `develop` branch working directory (uncommitted).

## ✅ The Fix (2 Options)

### Option 1: Automated Script (Recommended - 1 minute)

Just run this script - it will do everything:

```bash
cd C:\Modern-E-commerce-Analytics-Platform
scripts\setup_week5_git_workflow.bat
```

**What it does:**
1. ✅ Checks you're on develop
2. ✅ Creates 3 feature branches
3. ✅ Checkouts `feature/week5-query-optimization`
4. ✅ Stages all Day 1-2 files
5. ✅ Shows you the commit command to run

Then you just need to:
```bash
# Commit
git commit -m "feat(week5): add Day 1-2 query optimization docs and tests"

# Push
git push -u origin feature/week5-query-optimization
```

### Option 2: Manual Steps (If you want full control)

```bash
# 1. Verify you're on develop
git status
# Should show: On branch develop

# 2. Create 3 feature branches FROM develop
git branch feature/week5-query-optimization
git branch feature/week5-great-expectations
git branch feature/week5-dbt-tests

# 3. Verify branches created
git branch --list "feature/week5*"

# 4. Checkout query optimization branch
git checkout feature/week5-query-optimization

# 5. Stage Week 5 Day 1-2 files
git add docs/week5/
git add transform/tests/performance/
git add transform/models/marts/core/fact_orders_OPTIMIZED.sql
git add scripts/create_week5_branches.bat
git add scripts/create_week5_branches.sh
git add scripts/setup_week5_git_workflow.bat

# 6. Verify what's staged
git status

# 7. Commit
git commit -m "feat(week5): add Day 1-2 query optimization documentation and tests

- Add comprehensive optimization strategy docs (300+ lines)
- Create performance test suite with 5 production queries
- Document 77% avg performance improvement
- Calculate \$2,297 annual cost savings
- Prepare interview materials and resume bullets
- Add Week 5 documentation guides (5 files)
"

# 8. Push
git push -u origin feature/week5-query-optimization
```

## 📋 Current File Status

### Files Created (Currently in develop working directory - UNCOMMITTED)

```
docs/week5/
├── README.md                    (Week 5 overview - 450 lines)
├── CHECKLIST.md                 (Detailed checklist - 550 lines)
├── DAY1-2-COMPLETION.md        (Completion guide - 600 lines)
├── QUICK-START.md               (Quick start - 250 lines)
└── FILES-SUMMARY.md             (Files summary - 300 lines)

transform/tests/performance/
├── README.md                    (Testing guide - 450 lines)
└── query_performance.sql        (5 test queries - 700 lines)

transform/models/marts/core/
└── fact_orders_OPTIMIZED.sql    (Enhanced model - 500 lines)

scripts/
├── create_week5_branches.bat    (Windows automation)
├── create_week5_branches.sh     (Linux/Mac automation)
└── setup_week5_git_workflow.bat (Git workflow fix - NEW!)
```

**Status**: All files exist in working directory, need to be committed to proper branch

## 🎯 After Running the Script / Manual Steps

You'll be on `feature/week5-query-optimization` branch with files staged.

**Then:**

1. **Commit and Push:**
   ```bash
   # Already have staged files, just commit
   git commit -m "feat(week5): add Day 1-2 query optimization docs and tests"
   git push -u origin feature/week5-query-optimization
   ```

2. **Create Pull Request:**
   - Go to GitHub/GitLab
   - Create PR: `feature/week5-query-optimization` → `develop`
   - Title: "Week 5 Day 1-2: Query Optimization Documentation & Tests"

3. **After Merge (when ready for Day 3-5):**
   ```bash
   # Switch to develop and pull merged changes
   git checkout develop
   git pull origin develop
   
   # Checkout Day 3-5 branch
   git checkout feature/week5-great-expectations
   
   # Start Day 3-5 work
   ```

## 🗺️ Week 5 Branch Strategy

```
develop
├── feature/week5-query-optimization     (Day 1-2) ← YOU ARE HERE
├── feature/week5-great-expectations     (Day 3-5) ← NEXT
└── feature/week5-dbt-tests              (Day 6-7) ← AFTER THAT
```

**Workflow:**
1. Complete Day 1-2 → Commit to `feature/week5-query-optimization` → Merge to develop
2. Complete Day 3-5 → Commit to `feature/week5-great-expectations` → Merge to develop
3. Complete Day 6-7 → Commit to `feature/week5-dbt-tests` → Merge to develop
4. Tag release: `v0.5-week5-complete`

## 🚨 Common Issues

### Issue: "Branch already exists"
```bash
# If branches were created before, delete and recreate
git branch -D feature/week5-query-optimization
git branch -D feature/week5-great-expectations
git branch -D feature/week5-dbt-tests

# Then create fresh
git branch feature/week5-query-optimization
git branch feature/week5-great-expectations
git branch feature/week5-dbt-tests
```

### Issue: "You have uncommitted changes"
**Good!** That's expected. Those are the Week 5 files we created. Just follow the steps above.

### Issue: "I'm not on develop"
```bash
# Stash your changes first
git stash

# Checkout develop
git checkout develop

# Run the setup script
scripts\setup_week5_git_workflow.bat

# Your files will be back in working directory
```

## ✅ Verification

After running setup, verify:

```bash
# Check current branch
git branch --show-current
# Should show: feature/week5-query-optimization

# Check staged files
git status
# Should show Week 5 files staged for commit

# Check all Week 5 branches exist
git branch --list "feature/week5*"
# Should show all 3 branches
```

## 🎯 Quick Command Reference

```bash
# RUN THIS ONE COMMAND:
scripts\setup_week5_git_workflow.bat

# Then commit:
git commit -m "feat(week5): add Day 1-2 query optimization docs and tests"

# Then push:
git push -u origin feature/week5-query-optimization

# Done! ✅
```

---

**TL;DR**: 
1. Run `scripts\setup_week5_git_workflow.bat`
2. Commit the staged files
3. Push
4. You're done!

**Time**: 2 minutes total
**Difficulty**: Super easy (script does everything)
