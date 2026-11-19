# third_party/

TG-RAG is not redistributed here (its release has no licence file). Clone it into this folder at the tested commit:

```bash
git clone https://github.com/hanjiale/Temporal-GraphRAG.git third_party/TG-RAG
git -C third_party/TG-RAG checkout 350f5163f2f6a56700fd20f20684d83aabbe44d7
pip install -r third_party/TG-RAG/requirements.txt   # on Windows use this repo's requirements.txt instead
```

Then apply the two model-line changes in `configs/tgrag_config_changes.md`. To use a checkout elsewhere, set
`TGRAG_HOME=/path/to/TG-RAG`. The scripts and tests add `src/` and `TGRAG_HOME` to the Python path automatically.
