from typing import Dict
from dataclasses import dataclass


@dataclass
class IncomingData:
    file_url: str


@dataclass
class RequestMessage:
    messageId: str
    messageType: str
    data: IncomingData

    @classmethod
    def from_dict(cls, data: Dict):
        incoming_data = data.get('data')
        if incoming_data:
            data_obj = IncomingData(**incoming_data)
        else:
            data_obj = None
        return cls(
            messageId=data.get('messageId'),
            messageType=data.get('messageType'),
            data=data_obj
        )
