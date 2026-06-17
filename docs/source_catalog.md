# Source Catalog

This file records all researched candidate sources.

| Source | Type | Official? | Data Freshness | Auth/API Key | Method | Status | Notes |
|---|---|---:|---|---|---|---|---|
| TWSE official website | Public web | Yes | Often delayed / page-dependent | No | Web / OpenAPI | Not probed | Use as first official baseline |
| TPEx official website | Public web | Yes | Often delayed / page-dependent | No | Web / OpenAPI | Not probed | Use as official OTC baseline |
| TWSE MIS | Public market system | Semi-official/public | Potentially near real-time | Session/cookie may be required | HTTP / JS / session | Not probed | Candidate for live data; must respect rate limits |
| Yahoo Taiwan Finance | Public web | No, but mainstream | Potentially live in browser | No | Dynamic web / hidden endpoints | Not probed | Web scraping may be fragile |
| Yahoo Finance global | Public web | No, but mainstream | May be delayed | No | Quote/chart endpoint | Not probed | Candidate for ^TWII, 2330.TW |
| FinMind | Data platform | No | Depends on dataset/plan | Token optional/required | API | Not probed | Better for research/historical data |
| Fugle MarketData API | Commercial/API | No | Real-time depending plan | API key | REST/WebSocket | Feasibility only | Good developer docs |
| Fubon Neo API | Broker API | No | Real-time depending account/API | API key/account | SDK/REST/WebSocket | Feasibility only | Strong candidate for formal use |
