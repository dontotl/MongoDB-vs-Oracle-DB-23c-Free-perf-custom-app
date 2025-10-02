python -V
mkdir venvs
cd venvs
python -m venv oravsmongo
cd oravsmongo/bin/
source activate
pip install flask pymongo
python -m pip install --upgrade pip
