import math
from typing import List, Optional, Union

from .OpenAIProvider import OpenAIProvider


class NemotronProvider(OpenAIProvider):

    SUPPORTED_EMBEDDING_SIZES = {
        512,
        1024,
        2048,
    }

    def _resize_and_normalize(
        self,
        vector: List[float],
    ) -> Optional[List[float]]:
        if not isinstance(self.embedding_size, int):
            self.logger.error(
                "Nemotron embedding size was not configured"
            )
            return None

        if self.embedding_size not in self.SUPPORTED_EMBEDDING_SIZES:
            self.logger.error(
                "Unsupported Nemotron embedding size: %s. "
                "Supported sizes are: %s",
                self.embedding_size,
                sorted(self.SUPPORTED_EMBEDDING_SIZES),
            )
            return None

        if len(vector) < self.embedding_size:
            self.logger.error(
                "Nemotron returned a vector with %d dimensions, "
                "but %d dimensions were requested",
                len(vector),
                self.embedding_size,
            )
            return None

        reduced_vector = vector[:self.embedding_size]

        norm = math.sqrt(
            math.fsum(
                value * value
                for value in reduced_vector
            )
        )

        if not math.isfinite(norm) or norm <= 0:
            self.logger.error(
                "Cannot normalize Nemotron vector: "
                "invalid L2 norm %s",
                norm,
            )
            return None

        return [
            value / norm
            for value in reduced_vector
        ]

    def embed_text(
        self,
        text: Union[str, List[str]],
        document_type: str = None,
    ) -> Optional[List[List[float]]]:
        if isinstance(text, str):
            if not text.strip():
                self.logger.error(
                    "Cannot embed an empty text"
                )
                return None

            expected_count = 1

        elif isinstance(text, list):
            if not text:
                self.logger.error(
                    "Cannot embed an empty text list"
                )
                return None

            if not all(
                isinstance(item, str) and item.strip()
                for item in text
            ):
                self.logger.error(
                    "Every embedding input must be "
                    "a non-empty string"
                )
                return None

            expected_count = len(text)

        else:
            self.logger.error(
                "Embedding input must be a string "
                "or a list of strings"
            )
            return None

        vectors = super().embed_text(
            text=text,
            document_type=document_type,
        )

        if not vectors:
            self.logger.error(
                "Nemotron returned no embedding vectors"
            )
            return None

        if len(vectors) != expected_count:
            self.logger.error(
                "Nemotron embedding count mismatch: "
                "expected %d, received %d",
                expected_count,
                len(vectors),
            )
            return None

        processed_vectors = []

        for vector_index, vector in enumerate(vectors):
            if not vector:
                self.logger.error(
                    "Nemotron returned an empty vector "
                    "at index %d",
                    vector_index,
                )
                return None

            processed_vector = (
                self._resize_and_normalize(vector)
            )

            if processed_vector is None:
                self.logger.error(
                    "Failed to process Nemotron vector "
                    "at index %d",
                    vector_index,
                )
                return None

            processed_vectors.append(
                processed_vector
            )

        return processed_vectors