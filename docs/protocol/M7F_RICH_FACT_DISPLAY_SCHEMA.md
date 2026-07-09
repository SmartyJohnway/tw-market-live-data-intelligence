# M7F Rich Fact Display Schema

Status:
- display_schema_defined

Catalog path:
- docs/data_capabilities/rich_fact_display_catalog.json

Catalog schema version:
- m7f_rich_fact_display_catalog.v1

Required field entry shape:

```json
{
  "field_key": "price_like_value",
  "display_name": "Price-like value",
  "description": "Operator-readable parsed field.",
  "field_group": "price_quote",
  "source_layers": ["M7A", "M7B"],
  "source_path_candidates": [],
  "display_allowed": true,
  "ai_handoff_allowed": true,
  "operator_only": false,
  "exposure_class": "operator_display_allowed",
  "confidence_level": "project_validated",
  "provenance": "derived_from_normalized_observation",
  "caveats": [],
  "currentness_dependent": true,
  "calendar_dependent": false,
  "unit": null,
  "raw_forbidden": false,
  "frontend_render_hint": "scalar",
  "sort_order": 100
}
```

Required schema rules:

- field_key must be unique.
- display_name must be non-empty.
- field_group must be one of defined groups.
- exposure_class must be one of defined exposure classes.
- confidence_level must be one of defined confidence levels.
- raw_forbidden=true requires display_allowed=false and ai_handoff_allowed=false.
- ai_handoff_allowed=true requires display_allowed=true.
- currentness_dependent=true means M7E currentness label must be shown near the field or group.
- calendar_dependent=true means M7E-05 calendar authority confidence must be shown near the field or group.
