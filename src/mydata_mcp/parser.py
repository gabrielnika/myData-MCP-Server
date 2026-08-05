"""Parse myDATA XML responses into plain dicts, surviving the API's quirks.

The API sometimes wraps the payload in a <string> element containing
HTML-escaped inner XML, which is occasionally malformed (bare ampersands in
company names). Strategy: xmltodict first; on failure, lxml in recover mode.
Namespace prefixes (icls:, ecls:) are stripped so consumers see plain keys.
"""

import html
from typing import Any

import xmltodict
from lxml import etree


class ParseError(Exception):
    """Raised when a myDATA response cannot be parsed as XML."""


def parse_mydata_xml(xml_text: str) -> dict:
    parsed = _parse_with_recovery(xml_text)
    wrapper = parsed.get("string")
    if isinstance(wrapper, dict) and "#text" in wrapper:
        parsed = _parse_with_recovery(html.unescape(wrapper["#text"]))
    return _strip_namespaces(parsed)


def _parse_with_recovery(xml_text: str) -> dict:
    try:
        return xmltodict.parse(xml_text)
    except Exception:
        parser = etree.XMLParser(recover=True, encoding="utf-8")
        try:
            root = etree.fromstring(xml_text.encode("utf-8"), parser=parser)
        except Exception as exc:
            raise ParseError(f"myDATA returned unparseable XML: {exc}") from exc
        if root is None:
            raise ParseError("myDATA returned unparseable XML (empty document).")
        return xmltodict.parse(etree.tostring(root, encoding="utf-8"))


def _strip_namespaces(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            (key if key.startswith("@") else key.split(":", 1)[-1]): _strip_namespaces(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_strip_namespaces(item) for item in value]
    return value
