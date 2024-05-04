from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional
from pandas import DataFrame

class EmailParser(ABC):
    def __init__(self, folder_path: Path):
        """
        Initialize the EmailParser with a folder path.

        Args:
            folder_path (Path): Path to the folder containing email files
        """
        self.folder_path = folder_path

    @abstractmethod
    def parse(self) -> Optional[DataFrame]:
        """
        Extract email bodies and metadata from a folder of emails as a table

        Returns:
            Pandas dataframe containing thread id, email id, email text, email
            metadata columns
        """
        pass
