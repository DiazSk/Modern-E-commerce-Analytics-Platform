#!/bin/bash

# ==============================================================================
# Week 5 Feature Branch Creation Script
# ==============================================================================
# Purpose: Create feature branches for Week 5 implementation
# Usage: bash scripts/create_week5_branches.sh
# ==============================================================================

# Ensure we're on develop branch
git checkout develop

# Pull latest changes
git pull origin develop

echo "Creating Week 5 feature branches..."

# Feature 1: Query Optimization (Day 1-2)
git checkout -b feature/week5-query-optimization
git push -u origin feature/week5-query-optimization

# Back to develop
git checkout develop

# Feature 2: Great Expectations (Day 3-5)
git checkout -b feature/week5-great-expectations
git push -u origin feature/week5-great-expectations

# Back to develop
git checkout develop

# Feature 3: dbt Tests (Day 6-7)
git checkout -b feature/week5-dbt-tests
git push -u origin feature/week5-dbt-tests

# Back to develop
git checkout develop

echo "✅ All Week 5 feature branches created successfully!"
echo ""
echo "Branches created:"
echo "  - feature/week5-query-optimization"
echo "  - feature/week5-great-expectations"
echo "  - feature/week5-dbt-tests"
echo ""
echo "To start working on query optimization:"
echo "  git checkout feature/week5-query-optimization"
