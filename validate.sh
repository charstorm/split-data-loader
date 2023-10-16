set -ex
src="splitdataloader"
black $src
flake8 $src
mypy $src
