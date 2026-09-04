"""Makes fitparse tolerate FIT definition messages whose declared field size is
not a multiple of the declared base type's size.

Why this exists
---------------
COROS watches (verified on an APEX Pro activity export) emit definitions such as
"field size 1, base type uint32". fitparse 1.2.0 rejects the entire file rather
than degrading that one field, so *every* COROS activity upload failed with a
500 from POST /api/parser/fit.

fitparse's own source proposes exactly the fix applied here
(fitparse/base.py:193-194):

    # NOTE: we could fall back to byte encoding if there's any
    # examples in the wild. For now, just throw an exception

COROS is that example in the wild. We fall back to BASE_TYPE_BYTE and drop the
field's profile binding, so the offending field decodes as opaque bytes and
every other field in the message parses normally.

Why patch rather than vendor
----------------------------
`_parse_definition_message` is 58 lines. Copying it here would silently diverge
from upstream on every fitparse upgrade. Patching the single branch keeps the
rest of the method upstream's.

Why this cannot cause an outage
-------------------------------
`apply()` never raises. If a future fitparse release changes that branch, the
anchor no longer matches, we log a warning and leave fitparse untouched --
COROS files then fail exactly as they did before this shim, and nothing else
changes. `tests/unit/test_fit_parser.py` covers the tolerant behaviour, so an
upgrade that breaks the anchor fails CI loudly instead of failing in production.
"""

import inspect
import logging
import textwrap

import fitparse.base
from fitparse.records import BASE_TYPE_BYTE

logger = logging.getLogger(__name__)

_STRICT_BRANCH = """            if (field_size % base_type.size) != 0:
                # NOTE: we could fall back to byte encoding if there's any
                # examples in the wild. For now, just throw an exception
                raise FitParseError("Invalid field size %d for type '%s' (expected a multiple of %d)" % (
                    field_size, base_type.name, base_type.size))"""

_TOLERANT_BRANCH = """            if (field_size % base_type.size) != 0:
                # Patched by parsers/_fitparse_compat.py -- see module docstring.
                base_type = BASE_TYPE_BYTE
                field = None"""

_PATCHED_FLAG = "_uphill_tolerates_undersized_fields"


def apply() -> bool:
    """Patch fitparse in place. Returns True if tolerant parsing is active.

    Idempotent, and safe to call at import time: it swallows every failure and
    reports it via the return value and a warning log.
    """
    target = fitparse.base.FitFile._parse_definition_message
    if getattr(target, _PATCHED_FLAG, False):
        return True

    try:
        source = inspect.getsource(target)
    except (OSError, TypeError) as exc:  # source unavailable (frozen/zipped install)
        logger.warning(
            "fitparse compatibility patch skipped: source unavailable (%s). "
            "FIT files with undersized field definitions will fail to parse.",
            exc,
        )
        return False

    if _STRICT_BRANCH not in source:
        logger.warning(
            "fitparse compatibility patch skipped: _parse_definition_message no longer "
            "matches the expected shape (fitparse upgraded?). FIT files with undersized "
            "field definitions will fail to parse."
        )
        return False

    namespace = dict(vars(fitparse.base))
    namespace["BASE_TYPE_BYTE"] = BASE_TYPE_BYTE
    exec(textwrap.dedent(source.replace(_STRICT_BRANCH, _TOLERANT_BRANCH)), namespace)  # noqa: S102

    patched = namespace["_parse_definition_message"]
    setattr(patched, _PATCHED_FLAG, True)
    fitparse.base.FitFile._parse_definition_message = patched
    return True
