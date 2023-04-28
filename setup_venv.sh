#!/bin/sh

# This script creates and deletes a virtual environment for Python to manage
# dependencies separately from other projects.
#
# To create a virtual environment, run:
#   ./venv_py.sh
# or
#   ./venv_py.sh create
#
# To delete the existing virtual environment, run:
#   ./venv_py.sh delete

action=$1

create_venv() {
  rm -rf venv_py
  python3 -m venv venv_py
  . venv_py/bin/activate

  ./venv_py/bin/pip3 install wheel
  ./venv_py/bin/pip3 install -r ./requirements.txt

  echo "Updating submodules..."
  git submodule update --init --recursive

  echo "Downloading blocks and ledgers..."
  app/data/download_data.sh

  echo "Setup complete."
}

delete_venv() {
  . venv_py/bin/activate
  deactivate
  rm -rf venv_py
}

if [ "$action" = "delete" ]; then
  delete_venv
else
  create_venv
fi

