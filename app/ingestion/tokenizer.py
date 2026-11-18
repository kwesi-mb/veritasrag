from transformers import AutoTokenizer


class DocumentTokenizer:

    def __init__(
        self,
        model_name: str = "BAAI/bge-base-en-v1.5",
    ):
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_name
        )

    def encode(self, text: str) -> list[int]:
        return self.tokenizer.encode(
            text,
            add_special_tokens=False,
        )

    def decode(self, token_ids: list[int]) -> str:
        return self.tokenizer.decode(
            token_ids,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=False,
        )

    def count(self, text: str) -> int:
        return len(self.encode(text))

    def special_token_count(self) -> int:
        return self.tokenizer.num_special_tokens_to_add(
            pair=False
        )