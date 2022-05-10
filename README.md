# Dinosaur Planet Decompilation Status

The status page for the Dinosaur Planet decompilation.

Progress data is stored under `data/` and is usually automatically updated by the decomp repository's CI. Any commits to `master` will trigger a CI build that commits the built site to the `gh-pages` branch.

## Developing
1. Install Python prerequisites `pip3 install -r requirements.txt`
2. Run `progress.py` from the decomp repository to update `data/progress.json` (if an update is needed)
3. Build `./build.py`
