import pytest
from collections import namedtuple
from ontos.commands.map import parse_filter, matches_filter, FilterExpression

Doc = namedtuple('Doc', ['id', 'type', 'status', 'frontmatter'])

def test_parse_filter():
    expr = "type:strategy,kernel status:active"
    filters = parse_filter(expr)
    assert len(filters) == 2
    assert filters[0].field == "type"
    assert filters[0].values == ["strategy", "kernel"]
    assert filters[1].field == "status"
    assert filters[1].values == ["active"]

def test_matches_filter_basic():
    doc = Doc(id="auth_flow", type="strategy", status="active", frontmatter={"concepts": ["auth"]})
    
    # Match type
    assert matches_filter(doc, parse_filter("type:strategy")) is True
    assert matches_filter(doc, parse_filter("type:kernel")) is False
    
    # Match status
    assert matches_filter(doc, parse_filter("status:active")) is True
    
    # Match multiple (AND)
    assert matches_filter(doc, parse_filter("type:strategy status:active")) is True
    assert matches_filter(doc, parse_filter("type:strategy status:stable")) is False

def test_matches_filter_advanced():
    doc = Doc(id="auth_flow", type="strategy", status="active", frontmatter={"concepts": ["auth", "api"]})
    
    # Concept matching
    assert matches_filter(doc, parse_filter("concept:auth")) is True
    assert matches_filter(doc, parse_filter("concept:security")) is False
    
    # Glob matching on ID
    assert matches_filter(doc, parse_filter("id:auth_*")) is True
    assert matches_filter(doc, parse_filter("id:config")) is False
    
    # Case insensitivity
    assert matches_filter(doc, parse_filter("TYPE:Strategy")) is True
