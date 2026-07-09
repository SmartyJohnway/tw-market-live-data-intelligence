# M7E-05 TWSE Trading Calendar Authority

Status:
- shared_authority_defined

Purpose:
- Establish a formal TWSE trading-day authority for Mode A / Mode B / Mode C.
- Replace independent weekday-only trading-day inference with a shared resolver.

Source endpoint:
- TWSE OpenAPI holidaySchedule
- GET /v1/holidaySchedule/holidaySchedule
- https://openapi.twse.com.tw/v1/holidaySchedule/holidaySchedule

Endpoint traps:
- Date is ROC/Minguo YYYMMDD.
- Endpoint includes trading-day labels and non-trading dates.
- Name containing `交易日` is an explicit trading-day label, not a closure.
- Name not containing `交易日` is endpoint non-trading date.
- Weekends are non-trading by independent rule.
- `市場無交易，僅辦理結算交割作業` is non-trading.

Authority contract:
- Controlled ingestion only.
- Runtime consumers read supplied/local artifacts.
- No startup network.
- No hidden runtime fetch.
- No raw endpoint payload exposure in AI context.
- Shared resolver is `scripts/twse_trading_calendar.py::resolve_twse_trading_day`.

Mode contract:
- Mode A must use shared resolver for TWSE source-date trading-day checks.
- Mode B must use shared resolver for latest-observation/currentness trading-day checks.
- Mode C must use shared resolver for AI handoff trading-day language.
- No Mode A/B/C component should independently infer trading days.

Caveats:
- Not a full official exchange calendar/session engine.
- Does not cover all special sessions or emergency closures.
- No real-time SLA.
- Not trading advice.
- TAIFEX/TPEx-specific calendars are deferred unless explicitly supplied in future tasks.

Next task:
- M7F-FRONTEND-OPERATOR-PRESENTATION-AND-CONTEXT-WORKBENCH
