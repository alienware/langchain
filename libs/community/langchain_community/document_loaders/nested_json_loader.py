"""Loader that loads data from JSON."""
import json
from pathlib import Path
from typing import Callable, Dict, List, Optional, Union

from langchain.docstore.document import Document
from langchain.document_loaders.base import BaseLoader


class NestedJSONLoader(BaseLoader):
    """Loads a JSON file and flattens the nested structure referencing any identifier provided
    to load the text into documents.

    Example:
        {"key": [{"identifier": "text", "text": "value1"}, {"identifier": "text", "text": "value2"}]}
        -> [{"key_value1_text": "value1"}, {"key_value2_text": "value2"}]
    """

    def __init__(
        self,
        file_path: Union[str, Path],
        metadata_func: Optional[Callable[[Dict, Dict], Dict]] = None,
    ):
        """Initialize the JSONLoader.

        Args:
            file_path (Union[str, Path]): The path to the JSON file.
            metadata_func (Callable[Dict, Dict]): A function that takes in the JSON
                object extracted by flattening and the default metadata and returns
                a dict of the updated metadata.
        """

        self.file_path = Path(file_path).resolve()
        self._metadata_func = metadata_func

    def _flatten__nested_json(self, json_text):
        out = {}

        def flatten_json(json_data, key_name=''):
            if type(json_data) is dict:
                for a in json_data:
                    if a == 'identifier': continue
                    flatten_json(json_data[a], key_name + a + '_')
            elif type(json_data) is list:
                i = 0
                for a in json_data:
                    try:
                        identifier = a[a['identifier']]
                    except:
                        identifier = str(i)
                    flatten_json(a, key_name + identifier + '_')
                    i += 1
            else:
                out[key_name[:-1]] = json_data

        flatten_json(json.loads(json_text))
        return out

    def load(self) -> List[Document]:
        """Load and return documents from the JSON file."""

        data = self._flatten__nested_json(self.file_path.read_text())

        docs = []

        for i, sample in enumerate(data.items(), 1):
            metadata = dict(
                source=str(self.file_path),
                seq_num=i,
            )

            text = sample

            # In case the text is None, set it to an empty string
            text = dict([text]) or ""

            # In case the text is of type dict or list, dump to a JSON string
            if type(text) in [dict, list]:
                text = json.dumps(text)

            docs.append(Document(page_content=text, metadata=metadata))

        return docs
