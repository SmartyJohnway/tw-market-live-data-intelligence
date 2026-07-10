# M7G Rich Fact Browser Real Safe Artifact Rendering

Status: real_safe_artifact_rendering_defined

M7G-04 renders operator-selected local safe artifacts only after validation accepted and operator clicks Load validated artifact.

Static demo remains the default context.

Rejected artifacts never reach renderM7FRichFactBrowser.

Active context mode is explicit:
- static_demo
- loaded_safe_artifact

The loaded local safe artifact becomes the active safe context for the Rich Fact Browser and safe handoff preview only after the explicit operator load action. Validation alone records validation status but does not replace the active context.

This task does not execute refresh.
This task does not fetch live data.
This task does not add backend/API/MCP.

M7G-09 controlled manual refresh execution remains mandatory downstream work.
