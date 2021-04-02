# Install

Install on Linux

```bash
conda install cudnn=7.6 cudatoolkit=10.1
pip install tensorflow-gpu==2.3
```

Install on Windows
```bash
conda install tensorflow-gpu=2.3
```

Note: conda doesn't have tf 2.3 on Linux, see https://anaconda.org/anaconda/tensorflow-gpu.


yes: only one identifier is changed

no: multiple identifier renaming;

Ignored cases:

Interface method renaming which causes implementation renaming

Changes on comments or docstr are not renaming.
