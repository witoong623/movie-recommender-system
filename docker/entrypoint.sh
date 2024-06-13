#!/bin/bash

echo "Seeding database..."
python -m tools.seed_db

echo "Generate movie similarity matrix"
python -m tools.train_item_based_cf

# Execute the CMD from Dockerfile
exec "$@"
