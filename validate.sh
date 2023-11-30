set -ex
src="splitdataloader"
ruff check $src
ruff format $src
pyright $src
