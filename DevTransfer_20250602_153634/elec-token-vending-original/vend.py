from datetime import datetime

class Vend:
    def __init__(self, amount, kwh, tier1_kwh, tier2_kwh):
        self.date = datetime.now()
        self.amount = amount
        self.kwh = kwh
        self.tier1_kwh = tier1_kwh
        self.tier2_kwh = tier2_kwh

    def to_dict(self):
        return {
            'date': self.date.isoformat(),
            'amount': self.amount,
            'kwh': self.kwh,
            'tier1_kwh': self.tier1_kwh,
            'tier2_kwh': self.tier2_kwh
        }

    @classmethod
    def from_dict(cls, data):
        vend = cls(data['amount'], data['kwh'], data['tier1_kwh'], data['tier2_kwh'])
        vend.date = datetime.fromisoformat(data['date'])
        return vend
