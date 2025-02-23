from copy import deepcopy
from datetime import datetime

import pytest
from pydantic import BaseModel, ValidationError

from py_semantic_taxonomy.adapters.routers.validation import (
    IRI,
    DateTime,
    MultilingualString,
    Node,
    VersionString,
    one_per_language,
    Notation,
)


def test_iri():
    class IRIModel(BaseModel):
        foo: IRI

    assert IRIModel(foo="http://example.com/foo")
    assert IRIModel(foo="http://example.com/foo").foo == "http://example.com/foo"
    with pytest.raises(ValidationError):
        IRIModel(foo="***")


def test_version_string():
    assert VersionString(**{"@value": "2000"})
    assert VersionString(**{"@value": "2000"}).value == "2000"
    with pytest.raises(ValidationError):
        VersionString(foo="bar")


def test_date_time():
    dt = DateTime(
        **{"@type": "http://www.w3.org/2001/XMLSchema#dateTime", "@value": "2025-01-01T01:23:45"}
    )
    assert dt
    assert dt.value == datetime(year=2025, month=1, day=1, hour=1, minute=23, second=45)

    d = DateTime(**{"@type": "http://www.w3.org/2001/XMLSchema#date", "@value": "2025-01-01"})
    assert d
    assert d.value == datetime(year=2025, month=1, day=1)

    with pytest.raises(ValidationError):
        DateTime(**{"@type": "http://www.w3.org/2001/XMLSchema#time", "@value": "2025-01-01"})

    with pytest.raises(ValidationError):
        DateTime(**{"@type": "http://www.w3.org/2001/XMLSchema#dateTime"})

    with pytest.raises(ValidationError):
        DateTime(**{"@value": "2025-01-01"})

    with pytest.raises(ValidationError):
        DateTime(**{"@type": "http://www.w3.org/2001/XMLSchema#date", "@value": "something"})


def test_multilingual_string():
    s = MultilingualString(**{"@value": "foo", "@language": "en-GB"})
    assert s.value == "foo"
    assert s.language == "en-GB"

    with pytest.raises(ValidationError):
        MultilingualString(**{"@value": "foo"})

    with pytest.raises(ValidationError):
        MultilingualString(**{"@language": "en-GB"})


def test_multilingual_string_extra_forbidden():
    assert MultilingualString(**{"@value": "foo", "@language": "en-UK"})
    with pytest.raises(ValidationError):
        MultilingualString(**{"@value": "foo", "@language": "en-UK", "@type": "http://www.w3.org/1999/02/22-rdf-syntax-ns#PlainLiteral"})


def test_multilingual_string_langauge_code():
    s = MultilingualString(**{"@value": "foo", "@language": "en-UK"})
    assert s.language == "en-GB"

    with pytest.raises(ValidationError):
        MultilingualString(**{"@value": "foo", "@language": "w00t-w00t"})


def test_multilingual_string_text_direction():
    s = MultilingualString(**{"@value": "foo", "@language": "en-GB"})
    assert s.direction == "ltr"

    s = MultilingualString(**{"@value": "foo", "@language": "en-GB", "@direction": "ltr"})
    assert s.direction == "ltr"

    f = MultilingualString(**{"@value": "افتضاح است.", "@language": "fa", "@direction": "rtl"})
    assert f.direction == "rtl"

    with pytest.raises(ValidationError):
        MultilingualString(**{"@value": "foo", "@language": "en-GB", "@direction": "wut?"})


def test_node():
    n = Node(**{"@id": "https://example.com/foo"})

    assert n
    assert n.id_ == "https://example.com/foo"


def test_node_extra():
    n = Node(**{"@id": "https://example.com/foo", "foo": "bar"})

    assert n
    assert n.id_ == "https://example.com/foo"
    assert n.foo == "bar"


def test_one_per_language():
    vals = [
        MultilingualString(**{"@value": "foo, guv'nor?", "@language": "en-GB"}),
        MultilingualString(**{"@value": "foo, eh?", "@language": "en-CA"}),
        MultilingualString(**{"@value": "foo", "@language": "en-US"}),
    ]

    assert one_per_language(deepcopy(vals), "whatever") == vals

    with pytest.raises(ValueError) as excinfo:
        vals = [
            MultilingualString(**{"@value": "foo", "@language": "en-US"}),
            MultilingualString(**{"@value": "too", "@language": "en-US"}),
        ]
        one_per_language(vals, "something")
    MSG = "Only one string per language code is allowed for `something`, but language `en-US` has 2 strings: ['foo', 'too']"
    excinfo.value == MSG


def test_notation_forbid_extra_values():
    assert Notation(**{"@value": "7-11"})
    assert Notation(**{"@value": "7-11", "@type": "http://www.w3.org/1999/02/22-rdf-syntax-ns#PlainLiteral"})
    with pytest.raises(ValueError):
        Notation(**{"@value": "7-11", "@type": "http://www.w3.org/1999/02/22-rdf-syntax-ns#PlainLiteral", "language": "en"})