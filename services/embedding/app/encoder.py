from pathlib import Path

import numpy as np
import onnxruntime
from tokenizers import Tokenizer

TOKENIZER_FILENAME = "tokenizer.json"
MODEL_FILENAME = "model.onnx"
PAD_TOKEN = "[PAD]"
PAD_TOKEN_ID = 0


def mean_pool(token_embeddings: np.ndarray, attention_mask: np.ndarray) -> np.ndarray:
    weights = attention_mask[..., None].astype(np.float32)
    summed = (token_embeddings * weights).sum(axis=1)
    token_counts = np.clip(weights.sum(axis=1), 1e-9, None)
    return summed / token_counts


def l2_normalize(vectors: np.ndarray) -> np.ndarray:
    norms = np.clip(np.linalg.norm(vectors, axis=1, keepdims=True), 1e-12, None)
    return vectors / norms


class Encoder:
    def __init__(
        self, model_dir: Path, max_sequence_length: int, inference_batch_size: int
    ) -> None:
        self._tokenizer = Tokenizer.from_file(str(model_dir / TOKENIZER_FILENAME))
        self._tokenizer.enable_truncation(max_length=max_sequence_length)
        self._tokenizer.enable_padding(pad_id=PAD_TOKEN_ID, pad_token=PAD_TOKEN)
        self._session = onnxruntime.InferenceSession(
            str(model_dir / MODEL_FILENAME), providers=["CPUExecutionProvider"]
        )
        self._input_names = {value.name for value in self._session.get_inputs()}
        self._inference_batch_size = inference_batch_size
        self.max_sequence_length = max_sequence_length
        self.dimensions = len(self.encode(["warmup"])[0])

    def _build_feed(self, texts: list[str]) -> tuple[dict[str, np.ndarray], np.ndarray]:
        encodings = self._tokenizer.encode_batch(texts)
        attention_mask = np.array([e.attention_mask for e in encodings], dtype=np.int64)
        available = {
            "input_ids": np.array([e.ids for e in encodings], dtype=np.int64),
            "attention_mask": attention_mask,
            "token_type_ids": np.array([e.type_ids for e in encodings], dtype=np.int64),
        }
        return {name: available[name] for name in self._input_names}, attention_mask

    def encode(self, texts: list[str]) -> list[list[float]]:
        vectors: list[np.ndarray] = []
        for start in range(0, len(texts), self._inference_batch_size):
            batch = texts[start : start + self._inference_batch_size]
            feed, attention_mask = self._build_feed(batch)
            token_embeddings = self._session.run(None, feed)[0]
            vectors.append(l2_normalize(mean_pool(token_embeddings, attention_mask)))
        return np.vstack(vectors).astype(np.float32).tolist()

    def count_tokens(self, text: str) -> int:
        return len(self._tokenizer.encode(text).ids)
