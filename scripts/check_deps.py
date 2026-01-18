import sys
import os

print(f"Python: {sys.version}")
try:
    import torch

    print(f"Torch: {torch.__version__}")
except ImportError as e:
    print(f"Torch Error: {e}")

try:
    import spacy

    print(f"SpaCy: {spacy.__version__}")
except ImportError as e:
    print(f"SpaCy Error: {e}")

try:
    from sentence_transformers import CrossEncoder

    print("Sentence-Transformers: OK")
except ImportError as e:
    print(f"Sentence-Transformers Error: {e}")
except Exception as e:
    print(f"Sentence-Transformers Other Error: {e}")
