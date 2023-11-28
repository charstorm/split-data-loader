set -ex
src="splitdataloader"
ruff check $src
ruff format $src
mypy $src
