---
title: Liquid Sense GPU Prototype
emoji: 💧
colorFrom: purple
colorTo: blue
sdk: gradio
sdk_version: 6.32.0
python_version: '3.12'
app_file: app.py
license: apache-2.0
---

Text-only experimental port of the shipped Liquid Sense general checkpoint.
Choose **ZeroGPU** in hardware settings. No validated GPU speed or quality claim.
CPU smoke uses torch2.15+cpu; this target uses ZeroGPU-supported torch2.13 and
requires an actual GPU validation before integration into the Android app.
Exact pinned shipped pack,546verified tensors,32physical layers/56visits,
mHC2,conv7,local256. No stockQwen substitution or extra training.
The model identity discloses its Qwen-derived lineage.
Cold bootstrap downloads the published2GBZIP and extracts the exact text pack;
this takes time at first boot. Interrupted downloads fail visibly, never silently
resume or substitute unverified weights. The public demo supports text only;
no browsing, Python execution or online Android integration is advertised.
