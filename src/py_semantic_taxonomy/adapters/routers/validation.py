from collections import defaultdict
from datetime import datetime
from enum import Enum, StrEnum
from typing import Annotated, Literal

import langcodes
import rfc3987
from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    PlainSerializer,
    conlist,
    field_validator,
)


def validate_iri(value: str) -> str:
    rfc3987.parse(value, rule="IRI")
    return value


IRI = Annotated[
    str,
    AfterValidator(validate_iri),
]
SerializableDateTime = Annotated[
    datetime,
    PlainSerializer(lambda dt: dt.isoformat(), return_type=str),
]


class VersionString(BaseModel):
    """
    The range for http://www.w3.org/2002/07/owl#versionInfo is
    http://www.w3.org/2000/01/rdf-schema#Resource, which is a class instance with no restrictions
    or other guidance: https://www.w3.org/TR/rdf-schema/#ch_resource.

    In JSON-LD version strings would therefore be given as:

    ```'http://www.w3.org/2002/07/owl#versionInfo': [{'@value': 'some_number'}]```

    * It's a list because there can in theory be more than one
    * It uses ```{}``` syntax because it is an object, not a string

    Version numbers should be numeric, so we don't need a language or text direction. However, we
    don't know how they are arranged, so can't convert to numeric types.
    """

    value: str = Field(alias="@value")


class DateTimeType(Enum):
    date = "http://www.w3.org/2001/XMLSchema#date"
    datetime = "http://www.w3.org/2001/XMLSchema#dateTime"


class DateTime(BaseModel):
    """
    The range for http://purl.org/dc/terms/created is http://www.w3.org/2000/01/rdf-schema#Literal.
    We will be more strict and require an ISO 8601 date or datetime.
    """

    type_: DateTimeType = Field(alias="@type")
    # Pydantic can convert ISO 8601 dates and datetimes to native types automatically
    value: SerializableDateTime = Field(alias="@value")

    model_config = ConfigDict(use_enum_values=True)


class MultilingualString(BaseModel):
    """
    A dictionary which provides a language-tagged string literal compatible with JSON-LD 1.1.

    The language code must be compliant with BCP 47:
    https://www.w3.org/TR/rdf11-concepts/#dfn-language-tagged-string

    We use the `langcodes` library to ensure this compliance, and to fix common errors:
    https://pypi.org/project/langcodes/

    The direction is not required by the JSON-LD standard, but we will always include it to make
    code more predictable.
    """

    value: str = Field(alias="@value")
    language: str = Field(alias="@language")
    # https://www.w3.org/TR/json-ld11/#base-direction
    direction: Literal["ltr", "rtl"] = Field(alias="@direction", default="ltr")

    @field_validator("language", mode="after")
    @classmethod
    def language_code_valid(cls, value):
        # Will raise a subclass of ValidationError if invalid
        return langcodes.standardize_tag(value)

    model_config = ConfigDict(extra="forbid")


class Node(BaseModel):
    """
    If the RDF refers to a class instance instead of a string literal, this instance can have
    arbitrary attributes, but it must have at least an `@id`.
    """

    id_: IRI = Field(alias="@id")

    model_config = ConfigDict(extra="allow")


class StatusChoice(StrEnum):
    accepted = "http://purl.org/ontology/bibo/status/accepted"
    draft = "http://purl.org/ontology/bibo/status/draft"
    rejected = "http://purl.org/ontology/bibo/status/rejected"


class Status(BaseModel):
    id_: StatusChoice = Field(alias="@id")

    model_config = ConfigDict(extra="allow", allow_enum_values=True)


def one_per_language(values: list[MultilingualString], label: str) -> list[MultilingualString]:
    """Ensure that there is only one multilingual string per language code"""
    grouped = defaultdict(list)
    for mlstr in values:
        grouped[mlstr.language].append(mlstr.value)
    for key, obj in grouped.items():
        if len(obj) > 1:
            raise ValueError(
                f"Only one string per language code is allowed for `{label}`, but language `{key}` has {len(obj)} strings: {obj}"
            )
    return values


class Notation(BaseModel):
    """
    TBD: The range for http://www.w3.org/2004/02/skos/core#notation
    """

    value: str = Field(alias="@value")
    type_: IRI = Field(
        alias="@type", default="http://www.w3.org/1999/02/22-rdf-syntax-ns#PlainLiteral"
    )

    model_config = ConfigDict(extra="forbid")


class NonLiteralNote(BaseModel):
    """
    Used for skos:changeNote, skos:historyNote, and skos:editorialNote.

    SKOS allows for string literals but we require an author and timestamp for each.
    """

    values: conlist(MultilingualString, min_length=1) = Field(
        alias="http://www.w3.org/1999/02/22-rdf-syntax-ns#value"
    )
    creators: conlist(Node, min_length=1) = Field(alias="http://purl.org/dc/terms/creator")
    # XKOS guidance recommends `issued` instead of `created` for notes
    issued: conlist(DateTime, min_length=1, max_length=1) = Field(
        alias="http://purl.org/dc/terms/issued"
    )
