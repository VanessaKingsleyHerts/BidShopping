#!/bin/bash

# Customize how many CI pipelines to trigger
N_RUNS=5
BRANCH="main"
TRIGGER_FILE=".gitlab-ci.yml"
#TRIGGER_FILE="ci_trigger.txt"

echo "# manual test" >> $TRIGGER_FILE
for i in $(seq 1 $N_RUNS); do
  #echo "# CI trigger run $i" >> $TRIGGER_FILE
  git add $TRIGGER_FILE
  git commit -m "Trigger pipeline run $i"
  git push origin $BRANCH

  echo "✅ Triggered pipeline $i. Sleeping 90s to let CI process..."
  sleep 90
done
