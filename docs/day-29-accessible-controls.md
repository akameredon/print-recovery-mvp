# Day 29 — Accessible keyboard-friendly controls

## Purpose

Day 29 improves the operator dashboard for keyboard and assistive-technology use. The page now provides a skip link to the main content, a named main landmark, visible `:focus-visible` outlines and live regions for asynchronous recovery results.

The existing buttons, form controls, selectors, text areas and action cards remain reachable through the normal keyboard tab order. The skip link allows an operator to bypass the repeated page header and reach the job dashboard directly. The live output regions announce recommendation and timeline updates without requiring the operator to search the page manually.

This is an HTML-level accessibility improvement. It does not claim full WCAG conformance or replace testing with the target shop’s assistive technology and browser combination.

## Verification

```bash
python3 test_accessibility_controls.py
```

The focused test verifies skip navigation, the main landmark, visible focus styling, live regions and the existing recovery controls. The complete executable regression suite passed after the change.
