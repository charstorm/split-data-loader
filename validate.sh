set -ex
src="splitdataloader"
ruff format $src
ruff check $src
mypy $src
