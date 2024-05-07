echo "Enter your package name..."
read SRC_DIR

mv src_dir/ $SRC_DIR
sed -i.bak "s|\(SOURCE_CODE_DIR.*=\).*|\1 $SRC_DIR|g" Makefile
sed -i.bak "s|\(SOURCE_CODE_DIR.*=\).*|\1 \"$SRC_DIR/\"|g" .github/badges/readme.py
sed -i.bak "s|src_dir/|$SRC_DIR|g" .pre-commit-config.yaml
sed -i.bak "s|src_dir/|$SRC_DIR|g" scripts/run-if-main-branch.sh
sed -i.bak "s|src_dir/|$SRC_DIR|g" .github/workflows/ci.yml
sed -i.bak "/^\[tool\.poetry\]$/,/^$/!b; /name = \"\"/s//name = \"$SRC_DIR\"/" pyproject.toml

echo "Changed:

Makefile
.github/badges/readme.py
.pre-commit-config.yaml
scripts/run-if-main-branch.sh
.github/workflows/ci.yml
pyproject.toml.

Changed \"SOURCE DIR/\" to $SRC_DIR.
"
