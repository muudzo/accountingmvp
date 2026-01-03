import pandas as pd
from typing import List
from .base import BaseParser
from .sanitizer import sanitize_csv_value
from src.models.transaction import RawTransaction

class BankCSVParser(BaseParser):
    """Parser for Generic Type A Bank Statements."""
    
    REQUIRED_COLS = {'Date', 'Amount', 'Reference', 'Description'}

    def validate(self, file_path: str) -> bool:
        try:
            df = pd.read_csv(file_path, nrows=1)
            return self.REQUIRED_COLS.issubset(df.columns)
        except Exception:
            return False

    def parse(self, file_path: str) -> List[RawTransaction]:
        df = pd.read_csv(file_path)
        transactions = []
        
        for idx, row in df.iterrows():
            # Sanitize inputs immediately
            clean_desc = sanitize_csv_value(str(row.get('Description', '')))
            clean_ref = sanitize_csv_value(str(row.get('Reference', '')))
            
            txn = RawTransaction(
                raw_date=str(row['Date']),
                raw_amount=str(row['Amount']),
                raw_reference=clean_ref,
                description=clean_desc,
                source_file=file_path.split('/')[-1],
                line_number=idx + 2 # Header is line 1
            )
            transactions.append(txn)
            
        return transactions
