from typing import Any, Dict, List

from pynamodb.attributes import Attribute
from pynamodb.attributes import AttributeContainer
from pynamodb.attributes import BinaryAttribute
from pynamodb.attributes import BinarySetAttribute
from pynamodb.attributes import DecimalAttribute
from pynamodb.attributes import DecimalSetAttribute
from pynamodb.attributes import DiscriminatorAttribute
from pynamodb.attributes import DynamicMapAttribute
from pynamodb.attributes import EnumIntAttribute
from pynamodb.attributes import EnumStrAttribute
from pynamodb.attributes import IntAttribute
from pynamodb.attributes import IntSetAttribute
from pynamodb.attributes import JSONAttribute
from pynamodb.attributes import ListAttribute
from pynamodb.attributes import MapAttribute
from pynamodb.attributes import TTLAttribute
from pynamodb.attributes import UTCDateTimeAttribute
from pynamodb.attributes import UTCDatetimeIntAttribute

from pynamodb.models import Model

SERIALIZABLE_TYPES = (
    BinaryAttribute,
    BinarySetAttribute,
    DecimalAttribute,
    DecimalSetAttribute,
    DiscriminatorAttribute,
    EnumIntAttribute,
    EnumStrAttribute,
    JSONAttribute,
)
ISO_DATETIME_TYPES = (
    UTCDateTimeAttribute,
    UTCDatetimeIntAttribute,
)
ENCODER_MAPPING = {
    SERIALIZABLE_TYPES: lambda attr, data: attr.serialize(data),
    TTLAttribute: lambda _, data: data.timestamp(),
    ISO_DATETIME_TYPES: lambda _, data: data.isoformat(),
}

class PrimitiveAttributeEncoder:
    @staticmethod
    def encode(attr: Attribute, data):
        for types, callable in ENCODER_MAPPING.items():
            if isinstance(attr, types):
                return callable(attr, data)
        return data


class Encoder:
    def encode(self, instance: Model) -> Dict[str, Any]:
        return self.encode_container(instance)

    def encode_container(self, container: AttributeContainer) -> Dict[str, Any]:
        encoded = {}
        for name, attr in container.get_attributes().items():
            value = getattr(container, name)
            if value is not None:
                encoded[name] = self.encode_attribute(attr, value)
        return encoded

    def encode_attribute(self, attr: Attribute, data: Any):
        if isinstance(attr, ListAttribute):
            return self.encode_list(attr, data)
        elif isinstance(attr, MapAttribute):
            return self.encode_map(attr, data)
        else:
            return PrimitiveAttributeEncoder.encode(attr, data)

    def encode_list(self, attr: ListAttribute, data: List) -> List:
        element_attr = (attr.element_type or Attribute)()
        return [self.encode_attribute(element_attr, value) for value in data]

    def encode_map(self, attr: MapAttribute, data: MapAttribute) -> Dict:
        if type(attr) is MapAttribute:
            return {name: data[name] for name in data}
        elif isinstance(attr, DynamicMapAttribute):
            return self.encode_dynamic_map(attr, data)
        else:
            return self.encode_container(data)

    def encode_dynamic_map(self, attr: DynamicMapAttribute, data: MapAttribute) -> Dict:
        encoded = {}
        attributes = attr.get_attributes()
        for name in data:
            value = getattr(data, name)
            if name in attributes:
                encoded[name] = self.encode_attribute(attributes[name], value)
            else:
                encoded[name] = value
        return encoded
