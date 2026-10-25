"""Where S08's build reads and writes. The working folder is git-ignored (under work/); set S08_WORK to put
it elsewhere. The founder's portrait of M4 is read from work/people/raw/ (not in the repo either)."""
import os
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[2]
WORK = os.environ.get("S08_WORK", str(REPO / "work" / "people" / "DS-CAST-M4-S08-F05-v01" / "data")).rstrip("/") + "/"
RAW = REPO / "work" / "people" / "raw"
os.makedirs(WORK, exist_ok=True)
