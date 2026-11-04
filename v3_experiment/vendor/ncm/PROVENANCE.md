Source: https://github.com/HazyResearch/ncm

Pinned revision: c70274273f489abc73832b2b98584a8483b6b203

Files: `models/quant.py`, `utils/registry.py`, `utils/misc.py`, `LICENSE`.
The local filenames omit their original parent directories. Only the imports
of registry and misc were changed to relative imports. The authors' MIT
license is included unchanged.

This experiment uses the official residual quantizer with manual levels,
k-means initialization and disabled learned residual convolutions. Its linear
byte encoder/decoder and frozen-Qwen-conditioned regression heads are our
experimental adaptation, not the official NCM Transformer VQ-VAE or generator.
