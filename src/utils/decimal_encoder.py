from decimal import Decimal
import json

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            # Convert Decimal to float or int so JSON can save it
            return float(obj) if '.' in str(obj) else int(obj)
        return super(DecimalEncoder, self).default(obj)