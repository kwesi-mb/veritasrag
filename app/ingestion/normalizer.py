import re
import unicodedata


class TextNormalizer:

    @staticmethod
    def normalize(text: str) -> str:
        if not text:
            return ""

        # Normalize Unicode characters.
        text = unicodedata.normalize("NFKC", text)

        # Normalize line endings.
        text = text.replace("\r\n", "\n")
        text = text.replace("\r", "\n")

        # Remove null and unwanted control characters,
        # while retaining tabs and newlines.
        text = "".join(
            char
            for char in text
            if char in "\n\t" or not unicodedata.category(char).startswith("C")
        )

        # Normalize horizontal whitespace.
        text = re.sub(r"[^\S\n]+", " ", text)

        # Remove whitespace around newlines.
        text = re.sub(r" *\n *", "\n", text)

        # Collapse excessive blank lines.
        text = re.sub(r"\n{3,}", "\n\n", text)

        return text.strip()