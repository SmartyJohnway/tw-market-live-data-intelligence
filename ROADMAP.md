---
title: "tw-market-live-data-intelligence — Roadmap V3.2"
version: "3.2"
updated: "2026-09-14"
canonicalized_in_repo: "2026-09-23"
status_reconciled_through: "H-ACT-V3 promotion; Phase I not started"
project: "tw-market-live-data-intelligence"
product_positioning: "Taiwan Market Evidence & Research Infrastructure for Humans and AI Agents"
stable_product_release: "v1.0.0"
stable_release_commit: "e02bcb125999f542308a75f349c212f0ff3fee83"
roadmap_role: "Durable architecture and product roadmap; progress is tracked by checkboxes, not rolling status prose."
tags:
  - tw-market-live-data-intelligence
  - roadmap
  - market-evidence
  - research-evidence
  - mcp
  - ai-agent
  - local-first
  - governance
---

# tw-market-live-data-intelligence

# Roadmap V3.2 — Post-V1.0 Stable Release & Pre-Phase-G Reconciliation

> **版本日期：2026-09-14**  
> **產品穩定版：`v1.0.0`**  
> **Roadmap 版本與產品版本彼此獨立。**  
> **本文件不是 Git / release / deployment 狀態日誌。**  
> **未來一般進度更新只需由 Owner 將 `[ ]` 改為 `[x]`；不需要因 milestone 完成而重寫 Roadmap。**

> **Repository reconciliation — 2026-09-23:** This file is now the canonical
> repository Roadmap authority. The durable phase definitions below remain the
> V3.2 definitions from 2026-09-14. Current implementation evidence is more
> advanced than the original snapshot, but phase checkboxes are changed only
> when the whole Roadmap phase exit intent is met. Phase G has accepted G1/G2
> runtime evidence (material disclosures and monthly revenue), but the broader
> Roadmap G research scope is not declared complete here. Phase H has completed
> V3 contract/promotion governance and one bounded-live H1 TPEx attention route,
> while broader H1, H2 corporate-action, and H3 recent-reference coverage remain
> incomplete; therefore Roadmap Phase H also remains unchecked. **Phase I has
> not started and is not authorized by this consolidation.**

---

# 0. V3.2 的角色與使用規則

## 0.1 為什麼從 V3.1 升為 V3.2

Roadmap V3.1 建立了目前仍有效的核心產品哲學：

```text
AI
→ 理解使用者
→ 產生 Unified Market Evidence Request

TW-Market
→ Validate
→ Resolve Identity
→ Plan / Preview
→ Explicit Authorization
→ Execute Once
→ Result / Audit / AI Handoff

AI
→ 閱讀完整 evidence
→ 分析、比較、解釋、持續對話
```

V3.1 之後，工程實際完成了：

```text
Unified Workbench vertical closure
Local Service
Minimal six-tool MCP
Real Agent Closed-Loop Acceptance
Pre-Phase-F portability / identity realignment
Persistent Watchlist
Workbench integration
V1 feature closure
v1.0.0 stable release
MCP distribution / registry publication
```

其中最重要的架構演進不是「多了一個 release」，而是：

```text
Security Master
從 project-private runtime dependency
正式升格為 installation-local Taiwan Market Identity Service

durable cash-security identity
正式固定為 ISIN

fresh install
正式支援 NOT_INITIALIZED

Candidate B
不再是新 installation 的 production requirement
```

因此 V3.2 不是推翻 V3.1，而是：

> **把 V3.1 已落地的產品 contract、M8R-08G 的 portability / identity contract、Phase F closure 與 V1 stable release 整合成新的長期 Roadmap authority。**

## 0.2 Roadmap 不再追蹤會快速過期的狀態

V3.2 不再維護：

```text
CURRENT NEXT
CURRENT AUTHORIZED
NOT AUTHORIZED
current main SHA
current PR
current external directory review
current deployment queue
```

這些狀態由 Git、GitHub、release metadata、acceptance records、HANDOFF / PROJECT operational records 負責。

Roadmap 只回答：

```text
我們已經定案了什麼？
接下來想把產品做到什麼程度？
每個 Phase 必須做到哪些內容？
哪些邊界不可破壞？
什麼條件成立才算完成？
```

## 0.3 Checkbox 規則

Phase 與主要 milestone 使用：

```text
[x] completed
[ ] not yet completed
```

Owner 完成 milestone 後直接打勾即可。單純 `[ ] → [x]` 不需要升 Roadmap 版本。

只有下列情況才需要考慮 `V3.2 → V3.3`：

- 核心產品 contract 改變
- Phase scope 實質重排
- Identity authority 改變
- AI / runtime responsibility boundary 改變
- 新增會改變整體產品方向的大型 capability family
- Automation / execution safety contract 實質改寫

## 0.4 歷史文件處理原則

以下文件保留，不刪、不改寫：

```text
tw-market-live-data-intelligence_Roadmap_V3.1_2026-08-11.md

Base on Roadmapv3.1
Pre-Phase-F Portability,
Taiwan Market Identity Service
& Skill Realignment Plan.md
```

定位：

```text
historical architecture / planning evidence
```

第二份 Pre-Phase-F 文件中的已接受核心裁決已濃縮吸收進 V3.2。V3.2 成為後續規劃的 current Roadmap authority。

---

# 1. Frozen V1 Product Contract

以下內容視為 V1 已接受產品 contract。後續 Phase 原則上只做：

```text
extend
enrich
harden
evaluate
orchestrate
```

不得重新發明第二套核心 contract。

## 1.1 AI 與 TW-Market 的責任分界

### AI 負責

```text
理解自然語言與對話上下文
判斷是否需要呼叫 TW-Market
選擇 targets
選擇 data_needs
決定時間範圍
必要時向使用者追問
產生 Unified Market Evidence Request
閱讀完整 Unified Result
區分 observations / derived / missing / stale
整合不同 evidence family
分析、比較、解釋
生成使用者需要的研究報告
```

### TW-Market 負責

```text
request schema validation
canonical identity resolution
capability validation
resource bounds
deterministic planning
preview
explicit authorization boundary
source / route selection
bounded execute-once
deterministic calculations
currentness / timing semantics
coverage
fallback / missing evidence
citations
lineage
auditability
fail-closed behavior
```

### TW-Market 不負責

```text
建立第二套自然語言 intent classifier
取代 AI 理解使用者
替 AI 主觀挑選「最值得看」的證據
在 canonical result 中產生買賣建議
預測價格
執行交易
管理 broker credentials
```

核心原則：

> **我們不需要教程式理解使用者；我們需要讓 AI 能安全、明確、可稽核地使用程式。**

## 1.2 Canonical AI-facing contract

保留單一 Unified contract family：

```text
Unified Market Evidence Request
Canonical Preview
Unified Result
Capability Catalog
```

後續 Research Evidence 原則上應：

```text
extend data_needs / result sections
```

而不是建立第二套 competing AI-facing request language。

如果未來研究資料需要新的 subordinate schema，可以新增 evidence-family contract；但 AI-facing request authority 仍以 Unified Request 為核心。

## 1.3 Product workflow

```text
Mode A
Inspect / Validate

Mode B
Preview / Authorize / Execute Once

Mode C
Result / Audit / AI Handoff
```

完整使用者流程：

```text
Natural Language
→ AI
→ Unified Request
→ Validate
→ Preview
→ explicit confirmation / authorization
→ Execute Once
→ Result
→ Audit reference
→ AI Handoff
→ AI analysis / report
```

## 1.4 Six-tool MCP contract

V1 正式 MCP tool surface 固定為六個：

```text
1. market_describe_capabilities
2. market_validate_request
3. market_preview_request
4. market_read_result
5. market_export_ai_handoff
6. market_fetch_evidence
```

原則：

```text
no seventh persistent-watchlist mutation tool in V1
no MCP-only planner
no MCP-only request schema
no MCP-only result vocabulary
```

未來若真的需要新增 MCP tool：

> 必須先證明現有六工具無法在不扭曲語意的情況下完成新 capability，並以新的 Roadmap / contract decision 明確處理。

## 1.5 Execution safety contract

不可退讓：

```text
no trading
no order routing
no broker credential handling

no silent persistent mutation
no startup market fetch
no hidden full-market scan
no default polling
no default scheduler
no background refresh by default

preview != authorization
authorization != execution
execution must be bounded
execution must be explicit
fixture never silently becomes production authority
missing authority fails closed
```

## 1.6 Complete bounded evidence principle

正式原則：

> **Exhaustive within the authorized request scope.**

Authorized scope 由：

```text
targets
data_needs
time scope
supported market
resource bounds
authorization
```

共同決定。

範圍內應盡可能完整輸出：

```text
canonical observations
deterministic derived metrics
source
observed / published / effective timing
currentness
coverage
missing evidence
fallback
caveats
citations
lineage
audit references
```

Raw transport payload 不等於 AI context。Raw artifacts 可保留為 audit evidence、hash-bound reference、replay / verification material。

---

# 2. Frozen Identity, Portability & Persistence Contract

## 2.1 Taiwan Market Identity Service

Security Master 正式定位：

```text
Taiwan Market Identity Service
```

`tw-market-live-data-intelligence` 是主要 consumer，但不應成為唯一 consumer。

可服務未來：

```text
Market Evidence
Research Evidence
Persistent Watchlist
Portfolio consumers
ETF tools
Backtesting
Screening
Corporate Actions
Alert / monitoring consumers
other Taiwan market projects
AI / Agent Skills
```

## 2.2 Identity 三層模型

### Instrument Primary Identity

對受支援的台灣 cash-market securities：

```text
Instrument Primary Identity = ISIN
```

不得另外發明 custom permanent UUID 或 parallel durable security ID。

### Listing / Routing Identity

```text
market + security_code
```

例如：

```text
TWSE:2330
TPEX:6488
```

這是 current listing identity / routing identity，不是永久 instrument identity。

### Human-facing identity

```text
current name
historical name
aliases
English name
common shorthand
```

皆屬 metadata，不得作 durable primary key。

## 2.3 Knowledge universe 與 execution universe 分離

```text
identity known
≠
execution supported
```

Security Master 可以知道某 instrument 存在；Market Evidence runtime 可以仍然 `execution_eligibility = unsupported`。

不得因 identity knowledge 擴大，就自動擴張 execution scope。

## 2.4 Successor identity migration

若 corporate-action evidence 證明：

```text
Old ISIN
→ New ISIN
```

Persistent consumer 不得 silent rewrite。

必須：

```text
IDENTITY_MIGRATION_REVIEW_REQUIRED
```

使用者決定追蹤 successor 或保留原 instrument reference。

## 2.5 Installation-local Security Master release

Fresh installation：

```text
Security Master = NOT_INITIALIZED
```

這是合法 product state，不是 corruption。

依賴 identity authority 的操作應：

```text
FAIL CLOSED
→ SECURITY_MASTER_NOT_INITIALIZED
```

不得 fixture fallback、hidden network acquisition，亦不得把 FileNotFoundError leakage 當 product semantics。

## 2.6 Local release lifecycle

```text
BUILDING
→ CANDIDATE
→ QUALIFIED
→ ACTIVE
→ RETIRED
```

失敗：

```text
CANDIDATE
→ REJECTED
```

Production activation 必須 qualified、hash-bound、atomic、fail-closed。

## 2.7 Runtime consistency

保留：

```text
PROCESS_LIFETIME_IMMUTABLE_SELECTION
```

典型更新：

```text
build
→ qualify
→ seal
→ atomic active pointer swap
→ controlled restart
→ new process loads new ACTIVE release
```

不要求複雜 hot reload。

## 2.8 Candidate B 的永久定位

Historical Candidate B：

```text
historical development / acceptance evidence
regression provenance
audit reference
```

新 installation：

```text
不得要求 Candidate B
不得 copy Candidate B 作 production bootstrap
不得 fresh reprobe 後聲稱等價於 Candidate B
```

每個 installation 建立自己的 local Security Master Release。

## 2.9 Persistent Watchlist contract

Persistent Watchlist 的 durable reference：

```text
ISIN
```

Display / audit snapshot 可保留：

```text
name
market
security_code
resolved_under_release_id
```

Runtime execution：

```text
current ACTIVE Security Master Release
→ current routing projection
```

治理要求：

```text
installation-local persistence
immutable revisions
current projection
expected_version optimistic concurrency
preview → commit
no conversation-local target silently persists
no silent successor migration
```

V1 bounds：

```text
max 32 lists
max 500 entries per list
```

---

# 3. Frozen Local-First Product Boundary

## 3.1 Local-first

產品核心維持：

```text
local service
local persistence
local Security Master
explicit bounded network acquisition
MCP / UI reuse same service/runtime semantics
```

Local-first 不代表 offline-only，而是：

> **execution authority、state、identity、authorization 與 audit 預設由 installation 自己掌握。**

## 3.2 Workbench authority

Canonical Workbench：

```text
/workbench/
```

Compatibility surface：

```text
/workbench/mode-a/
→ compatibility redirect only
```

Simple Request Builder 為主要 UX；Advanced JSON 保留為完整 contract surface。

## 3.3 Distribution 不應成為 feature blocker

V1 public distribution 可包含 GitHub Release、MCP package、Official MCP Registry、third-party directories、container introspection、host compatibility。

但 external directory approval、registry ranking、social promotion、download count 不應阻塞後續產品 Phase。

---

# 4. Completed Product Foundation

# [x] Phase A — Governed Evidence Core

### 已定案內容

```text
official market evidence sources
TWSE / TPEx / TAIFEX source families
currentness semantics
source lineage
normalized evidence
partial / missing disclosure
fail-closed source behavior
```

### 預期成果 — 已達成

> 建立「資料從哪裡來、什麼時間、能不能用、缺什麼」的 governed evidence foundation。

# [x] Phase B — AI Guide & Portable Skill Baseline

### 已定案內容

```text
AI usage guide
Skill when-to-call semantics
facts / derived / assumptions / missing separation
source / currentness reading rules
portable Skill source packages
```

### 預期成果 — 已達成

> AI 不只會「叫工具」，而是知道何時該叫、如何建立 Request、如何閱讀 evidence。

# [x] Phase C — Unified Contract & Runtime

### 已定案內容

```text
Unified Request
Capability Catalog
Canonical Preview
Unified Result
deterministic planning
authorization binding
execute-once orchestrator
Result + separate Audit
```

### 預期成果 — 已達成

> Backend contract 成為單一、可驗證、可重用的 evidence execution chain。

# [x] Phase D — Unified Workbench

### 已定案內容

```text
Mode A Validate
Mode B Preview
Mode B Authorize
Execute Once
Mode C Result / AI Handoff
localhost-only operator workflow
```

### 預期成果 — 已達成

> Human operator 不依賴 MCP 也能完成完整 evidence journey。

# [x] Phase E — Local Service, MCP & Real-Agent Closed Loop

### 已定案內容

```text
local-first service layer
six-tool MCP
same canonical contracts
same execution boundary
real-agent acceptance
TWSE
TPEx
partial success
identity ambiguity
source failure
TAIFEX boundary
stale/currentness
```

### 預期成果 — 已達成

> AI Agent 可透過 MCP 完成與 Workbench 相同語意的 evidence closed loop。

# [x] Phase E-P — Portability, Identity Service & Skill Realignment

### 已定案內容

```text
fresh clone portability
NOT_INITIALIZED
installation-local Security Master Release
qualification
atomic activation
rollback semantics
ISIN durable identity
listing history
alias history
successor migration review
portable Skill realignment
dependency reproducibility
Candidate B runtime dependency removal
```

### 預期成果 — 已達成

> Repository 不依賴開發者原電腦的 private runtime payload；新 installation 可以自己建立 identity authority。

# [x] Phase F — Persistent Watchlist & Productization

### 已定案內容

```text
persistent Watchlist
durable ISIN references
immutable revisions
optimistic concurrency
preview → commit
Workbench integration
explicit persistence
```

### 預期成果 — 已達成

> TW-Market 從 conversation-local evidence engine 進化成具 installation-local durable user state 的產品。

# [x] V1 Release Gate — Stable Productization

### 已定案內容

```text
V1 feature complete
stable release freeze
release validation
v1.0.0
MCP distribution
registry publication
public product front door
```

Stable release anchor：

```text
v1.0.0
commit:
e02bcb125999f542308a75f349c212f0ff3fee83
```

### 預期成果 — 已達成

> V1 不只是 repository 中的一組功能，而是可以被第三方取得、安裝、辨識與驗證的正式產品版本。

---

# 5. Future Product Strategy

V1 之後的主軸不再是「做更多 quote API」。

目標是逐步進化成：

> **Taiwan Market Evidence & Research Infrastructure for Humans and AI Agents**

核心能力應回答：

```text
Who is this instrument?
What officially happened?
What market evidence exists?
How current is it?
What is missing?
What changed?
How does this compare to recent history?
What disclosures / fundamentals are relevant?
What official evidence supports the answer?
Can another AI consume this safely?
```

而不是直接回答：

```text
Should I buy?
Will the price rise?
Which stock will outperform?
Can you trade it for me?
```

# [ ] Phase G — Research Evidence Expansion

## G.0 Phase Goal

將 V1 的 `Market Evidence` 擴張為 `Market + Official Research Evidence`。

讓 AI 不只知道「現在市場發生什麼」，還能取得：

```text
公司正式揭露了什麼
近期營運與財務狀況是什麼
哪些官方文件支持這些事實
```

## G.1 Official Disclosure Evidence

需要做到：

```text
TWSE listed company material information
TPEx listed company material information
publication timestamp
company / instrument binding
announcement category
title
official source URL / source identity
raw evidence reference
normalized evidence record
amendment / correction semantics
```

第一優先資料族：重大訊息、重要公告、公司正式揭露事件。

要求：

```text
official source first
published_at preserved
observed_at preserved separately
company code must resolve through Identity Service
historical / current retrieval semantics must be explicit
duplicate / corrected disclosure handling must be deterministic
```

不得只抓新聞標題冒充重大訊息、用搜尋引擎摘要取代 official disclosure、把 AI 自動摘要寫回 canonical fact。

## G.2 Fundamentals & Periodic Operating Evidence

第一階段候選：

```text
monthly revenue
income statement
balance sheet
selected official financial statement fields
EPS / operating result where source semantics are clear
dividend distribution where relevant
```

每一筆資料必須保留至少：

```text
reporting period
period type
publication / filing time if available
currency
unit
consolidated / standalone semantics
industry-specific statement family
revision / restatement status
source
lineage
```

不得把 monthly、quarterly、annual、TTM、single-quarter、YTD 混為同一數值語意。

## G.3 Research Evidence Contract

Phase G 必須先建立 research evidence family contract。

原則：

```text
new research capability
→ extend Unified data_needs
→ project into Unified Result
```

而不是建立第二套 AI request language。

Research Evidence 至少需要：

```text
evidence_family
instrument identity
source authority
effective period
published time
observed time
currentness class
normalized facts
raw evidence reference
citation
missing / partial semantics
```

## G.4 Research Evidence Bundle

建立一個適合 AI 研究使用的完整 evidence projection：

```text
Research Evidence Bundle

├─ identity
├─ current market evidence
├─ official disclosures
├─ periodic operating evidence
├─ fundamentals
├─ currentness matrix
├─ missing evidence
├─ caveats
├─ citations
└─ audit references
```

這個 Bundle 是 AI report input，不是 AI-written investment report。

## G.5 Governed Research Orchestration

AI 可以要求：

```text
current market evidence
+ latest material disclosures
+ latest monthly revenue
+ selected financial statements
```

TW-Market deterministic 地 validate、plan、preview、authorize、fetch、normalize、package。

不能變成 unbounded web search、random crawler、general-purpose news agent。

## G.6 Phase G Acceptance

至少驗證：

```text
TWSE company research
TPEx company research
multi-target research
material disclosure available
no recent disclosure
corrected / duplicate disclosure
monthly revenue
quarterly statement
industry-specific financial schema
partial source failure
stale source
publication-time ambiguity
identity mismatch
unsupported evidence family
```

### Phase G 預期成果

完成後，AI 應可以安全處理類似：
> 「幫我研究 2330 最近發生什麼，包含目前行情、最近重大訊息、最新月營收與最近一期主要財務資訊，並把資料日期與缺漏講清楚。」

輸出必須 official-evidence-grounded、time-aware、citation-ready、missing-aware，而不是投資建議。

# [ ] Phase H — Interpretation & Historical Reference

## H.0 Phase Goal

解決：

> **資料本身正確，但 AI 因缺少市場制度、corporate action 或歷史基準而解讀錯誤。**

Phase H 是 interpretation safety，不只是附加資料。

## H.1 Regulatory / Trading Status Context

需要納入：

```text
注意股票
處置股票
變更交易
暫停 / 恢復交易
交易限制
其他會影響 quote interpretation 的 official status
```

每個狀態必須保留：

```text
status type
effective from
effective to if known
official reason / condition
source
published_at
observed_at
```

AI 必須能區分 ordinary market movement 與 market-supervision / restriction context。

## H.2 Corporate Action Interpretation

第一階段至少：

```text
cash dividend
stock dividend
ex-right
ex-dividend
capital reduction
split / consolidation where official evidence exists
capital increase effects
reference-price events
```

核心：

```text
raw close-to-close price change
≠
economic interpretation
```

若存在 corporate action，reference-price context 必須揭露。

不得在 corporate action unresolved 時直接產生一般「暴跌 / 暴漲」描述。

## H.3 Recent Historical Reference Baseline

最小 baseline：

```text
5D price range
20D price range
5D average volume
20D average volume
current position in range
current volume vs average
valid observation count
official date range
missing trading-day semantics
```

原則：descriptive context only，不是 technical indicator engine、strategy engine、backtester。

## H.4 Adjustment / Discontinuity Safety

若歷史期間跨越 ex-right、ex-dividend、capital reduction、split 或其他 material price-basis discontinuity，系統必須 detect、explain、adjust if governed method exists，否則 fail closed / caveat。

不得用 unresolved raw discontinuity 產生普通 return interpretation。

## H.5 Unified Quote Interpretation Context

Phase H 最終應能輸出：

```text
quote
+ regulatory status
+ corporate action context
+ reference-price context
+ recent baseline
+ caveats
```

作為 Unified Result 的 optional interpretation section。

### Phase H 預期成果

AI 能回答：

> 「今天這個跌幅到底代表市場下跌，還是除息／減資等價格基準改變？今天成交量相對最近 20 天到底大不大？」

並且不需要靠模型猜。

# [ ] Phase I — Cross-Market & Optional Context

## I.0 Phase Goal

提供：

> **只有在研究問題真的需要時才載入的市場背景。**

不把 Unified Result 變成資料百科全書。

## I.1 Evidence Value Gate

任何新 evidence family 在正式加入前必須回答：

```text
1. 是否有官方或足夠可信來源？
2. 是否直接改善 AI interpretation？
3. timing semantics 能否誠實定義？
4. normalization 是否不需主觀猜測？
5. missing 時是否會造成重大誤解？
6. 應該 default load 還是 optional load？
7. 是否容易誘發過度投資推論？
8. storage / network / latency cost 是否合理？
```

未通過：`DO NOT ADD`。

## I.2 Spot–Derivatives Descriptive Context

候選：

```text
spot market state
index futures
options
settlement references
open interest
put/call ratio
institutional futures/options positions
contract adjustment
```

必須揭露：

```text
spot observed time
derivatives observed time
settlement date
statistics frequency
contract identity
timing alignment status
```

禁止 leading-signal claim、prediction、manipulation claim、automatic bull / bear label。

## I.3 Derivatives Identity Boundary

Cash security 使用 ISIN-primary identity；不得強行套到 futures series、options series、expiring contracts。

Phase I 必須建立或重用清楚的 derivatives contract identity semantics，而不是污染 cash-market identity contract。

## I.4 Optional Equity-Market Context Candidates

候選 evidence family：

```text
market breadth
advance / decline counts
turnover concentration
industry classification / industry context
institutional investor flows
margin financing
short selling
securities lending
day-trading statistics
ETF composition / relationship
index constituent relationships
fund size / beneficiary context
```

每一項都必須先過 Evidence Value Gate。

## I.5 Default Result Minimalism

Phase I 不能導致每次查單一標的就自動抓所有 TAIFEX、融資融券、ETF、三大法人與市場寬度。

應維持 explicit / AI-selected data_needs 與 bounded optional loading。

### Phase I 預期成果

AI 在需要時可以得到：

> 「這個現貨變動在期貨、選擇權、市場寬度、籌碼或 ETF 關係背景下是什麼樣子？」

但 canonical evidence 不會直接宣告 bullish、bearish、leading 或 manipulated。

# [ ] Phase J — Integrated Research Acceptance

## J.0 Phase Goal

Phase J adds no new product capability。

它是：

> **Market + Research + Interpretation 的完整 acceptance gate。**

## J.1 Golden Research Scenarios

建立 governed scenario suite，至少涵蓋：

```text
normal TWSE
normal TPEx
multi-target
current market evidence
official EOD
material disclosure
no material disclosure
corrected disclosure
monthly revenue
financial statements
attention / disposition
suspend / resume
ex-dividend
ex-right
capital reduction
reference-price discontinuity
5D / 20D baseline
TAIFEX context
timing mismatch
partial success
stale
missing
source failure
identity ambiguity
unsupported identity
authorization refusal
resource bound
```

## J.2 Acceptance Layers

至少：

```text
contract fixture
deterministic unit
integration
service API
Workbench
MCP
fresh-install
real bounded network
real AI / agent
```

不是每個 scenario 都要每層完整重跑；但必須建立可追蹤的 coverage matrix。

## J.3 Golden Expected Semantics

Acceptance 不以文字完全一致判斷。

應檢查：

```text
correct identity
correct source
correct period
correct currentness
correct missing
correct partial
correct corporate-action handling
correct authorization
correct bounded execution
correct citations
correct no-trading boundary
```

## J.4 Regression Authority

Golden scenarios 應成為 new source、new evidence family、new MCP version、new agent host、new release 的 regression baseline。

### Phase J 預期成果

可以合理宣稱：

> **TW-Market 不只會抓資料；它能在主要台灣市場研究情境下維持一致、可驗證的 evidence semantics。**

# [ ] Phase K — Multi-Agent Compatibility & Evaluation

## K.0 Phase Goal

驗證：

> **不同 AI / Agent 是否能正確使用相同 TW-Market contract。**

不是比較哪個模型投資建議比較準，而是比較 tool-use correctness、protocol adherence、evidence interpretation、safety behavior。

## K.1 Agent Evaluation Dimensions

至少：

```text
是否知道何時需要 TW-Market
是否產生合法 Unified Request
是否選擇合理 data_needs
是否正確處理 identity
是否先 Preview
是否尊重 authorization
是否理解 execute-once
是否理解 partial
是否理解 stale/currentness
是否揭露 missing
是否正確讀 citations
是否會把 full_success 說成 realtime guarantee
是否會產生 unsupported trading claim
```

## K.2 Tool / Protocol Compatibility

測試：

```text
MCP tool discovery
tool schema interpretation
tool-call sequencing
structured result handling
large result handling
timeout behavior
host confirmation behavior
transport differences
```

Agent / Host 名單可以隨時演進。Roadmap 不把任何單一 vendor 永久寫成 mandatory。

候選：ChatGPT、Claude、Gemini、GitHub Copilot、Hermes、OpenCode、other MCP-capable agents。

## K.3 Compatibility Matrix

產出 Agent Compatibility Matrix。

每個 host 至少標記：

```text
transport support
six-tool discovery
Validate
Preview
Execute Once
Result
AI Handoff
large-output behavior
confirmation semantics
known limitations
```

## K.4 No Host-Specific Core Fork

若某個 Agent 有限制，先做 adapter / packaging / documentation。

不得輕易修改 canonical result、增加 competing tool contract、破壞 local-first semantics，只為迎合單一 host。

### Phase K 預期成果

TW-Market 可以被描述為：

> **agent-portable evidence service，而不是只對單一模型調教成功的專案。**

# [ ] Phase L — Production Hardening & Extension Architecture

## L.0 Phase Goal

把已經能用的產品，整理成：

> **可以長期維護、可以持續增加 evidence family，而不讓治理與可靠性隨規模崩解的平台。**

## L.1 Observability

至少：

```text
structured logs
trace / request IDs
execution IDs
source timing
adapter timing
failure reason codes
resource usage
network attempt accounting
```

不得把敏感內容或大 raw payload 無限制寫 log。

## L.2 Replay & Audit

建立：

```text
request replay semantics
result replay semantics
artifact reference retention
audit retention policy
hash verification
reproduction limits
```

要能區分 replay old evidence 與 re-fetch current evidence。

## L.3 Schema & Migration Policy

至少：

```text
schema compatibility policy
database migration policy
Watchlist migration
Security Master release compatibility
result compatibility
Skill compatibility
MCP tool-schema compatibility
```

禁止 silent incompatible migration。

## L.4 Source Drift Management

每個 source adapter 必須能面對：

```text
schema drift
field rename
encoding change
empty-but-200 response
delayed publication
unexpected universe delta
HTTP failure
rate limiting
source removal
```

重要 source 需建立 contract probes、drift fixtures、failure reason code。

## L.5 Security Hardening

至少：

```text
localhost exposure review
path containment
input bounds
output bounds
dependency review
supply-chain review
MCP prompt/tool injection boundary
authorization review
secret handling if future source requires it
```

維持 no broker credential handling。

## L.6 Resource & Load Boundaries

驗證：

```text
large Watchlist
multi-target
large disclosure result
large financial result
long AI handoff
bounded concurrent local calls
timeout
memory
disk retention
```

確定 max targets、max evidence rows、max payload、max artifacts 都有可預期行為。

## L.7 Evidence Family Extension Contract

未來新增 new evidence family 應有固定流程：

```text
source inventory
→ source contract
→ capability
→ schema
→ adapter
→ normalization
→ timing/currentness
→ Result projection
→ tests
→ Skill / guide update
→ acceptance
```

不能每次新增資料都重新修改整個 architecture。

## L.8 CI / Release Governance

包含：

```text
required CI profile
Windows compatibility
fresh clone
non-network deterministic profile
network acceptance profile
release manifest
dependency lock
branch / merge protection where appropriate
release reproducibility
```

### Phase L 預期成果

> TW-Market 從「完成很多功能的 repository」進化成「可以長期擴張與維護的 evidence platform」。

# [ ] Phase M — Agent-Scheduled Research & Bounded Monitoring

## M.0 Phase Goal

Phase M 的 Automation 定義正式為：

> **讓外部 Agent / scheduler 安全地定時或短時間重複呼叫 TW-Market；不是讓 TW-Market 默默變成永久 background polling daemon。**

核心：

```text
Scheduling belongs to the invoking Agent by default.

TW-Market remains:
bounded
auditable
explicit
evidence-oriented
```

## M.1 Scheduled One-Shot Research

典型：

```text
每天 10:00
→ Agent invokes TW-Market once
→ Research Evidence Bundle
→ AI writes report

每天 12:00
→ invoke once
→ noon research update

after close
→ EOD research
```

TW-Market 不需要理解 cron / calendar / daily schedule。

它只需在每次 invocation：Validate → Preview / policy authorization → Execute Once → Result。

## M.2 Research Report Handoff

建立適合 scheduled Agent 使用的：

```text
Research Evidence Bundle
→ AI report-generation contract
```

TW-Market 提供 facts、periods、currentness、changes、missing、citations。

AI 負責 narrative、comparison、executive summary、user-facing report。

TW-Market 不直接成為 investment commentary generator。

## M.3 Bounded Repeated Research Session

支援例如：

```text
10:00 → 11:00
every 5 minutes
max 12 invocations
targets = [...]
data_needs = [...]
```

必要 contract：

```text
session_id
start
end
interval
max_invocations
max_network_requests
targets
data_needs
per-invocation receipt
result sequence
```

不得 monitor_forever = true、unbounded polling、silent extension。

## M.4 External Scheduler First

預設由 ChatGPT / Agent scheduler、Hermes scheduler、OS scheduler、CI scheduler 或 other agent runner 負責 clock / recurrence。

TW-Market does not need internal scheduler。

只有在未來證明 external orchestration cannot satisfy a governed requirement 才考慮 internal scheduling component。

## M.5 Deterministic Condition Contract

進一步的盤中監控可支援：

```text
if deterministic evidence condition becomes true
→ return condition_met event
```

例如概念：

```text
price_change_pct <= -3
AND
relative_volume_20d >= 2
```

AI 可以把自然語言需求轉成 condition contract；但 runtime 應 deterministically evaluate explicit condition。

不得讓 LLM subjective judgement 成為每五分鐘是否觸發警報的唯一 authority。

## M.6 Alert Delivery Boundary

預設：

```text
condition event
→ returned to Agent / scheduler
→ Agent decides notification channel
```

TW-Market 不必第一版內建 email、LINE、Telegram、SMS、push。

## M.7 Monitoring Authorization Envelope

Repeated monitoring 的 authorization 不等於 unlimited authorization。

應綁：

```text
exact session
targets
data_needs
time window
interval
maximum calls
maximum network requests
condition contract
expiry
```

Session 過期 fail closed。

## M.8 Security Master Refresh Boundary

Security Master 仍不是高頻資料。

如未來允許 Agent 定期觸發 update：

```text
must be explicit opt-in policy
must retain qualification
must retain atomic activation
must retain old ACTIVE on failure
```

不得把 market monitoring schedule 自動等同於 refresh identity authority。

## M.9 Scheduled / Monitoring Acceptance

至少：

```text
daily one-shot research
scheduled noon report
bounded 1-hour monitoring
max invocation enforcement
session expiry
network bound
source failure mid-session
stale data mid-session
corporate action during session
condition not met
condition met exactly once
duplicate alert suppression policy
Agent restart
machine sleep / missed invocation semantics
timezone / market-session boundary
```

### Phase M 預期成果

使用者可以要求外部 Agent：

> 「每天中午幫我做一次這份 Watchlist 的盤中研究報告。」

或者：

> 「今天 10:00 到 11:00，每 5 分鐘檢查一次 2330；如果明確條件成立就提醒我。」

而 TW-Market 核心仍保持 local-first、bounded、auditable、non-trading、explicit。

---

# 6. Cross-Phase Global Rules

所有 G–M 都必須遵守。

## 6.1 Official-source-first

優先 TWSE、TPEx、MOPS、TAIFEX 與其他 authoritative Taiwan market institutions。

第三方資料只能在 official source unavailable、value is clear、provenance is explicit、legal / usage terms acceptable 後再評估。

## 6.2 Timing is part of the data

每一個 evidence family 都要能回答：

```text
What period does this represent?
When was it published?
When did we observe it?
When does it become effective?
How stale can it be?
```

不得用單一 timestamp 掩蓋不同時間語意。

## 6.3 Missing is not zero

```text
missing
unknown
not published
not supported
source failed
stale
not applicable
```

必須可區分。

## 6.4 Evidence is not conclusion

Canonical evidence 可以包含 facts、deterministic calculations、descriptive comparisons。

不得偷偷加入 buy / sell、price target、bullish / bearish verdict、causal claim without evidence。

## 6.5 No second product core

後續功能不得建立 parallel identity authority、parallel request contract、parallel result contract、parallel planner、parallel execution model。

## 6.6 Scope grows only when semantics are governed

能抓到資料不代表應加入產品。

每次擴張都必須先回答 source authority、identity、time semantics、normalization、currentness、missing、failure、value to AI。

---

# 7. Long-Term Product Boundary

TW-Market 的長期目標：

> **Taiwan Market Evidence & Research Infrastructure for Humans and AI Agents**

它應該成為可靠的：

```text
identity layer
market evidence layer
official research evidence layer
interpretation context layer
audit / lineage layer
agent integration layer
```

它不是：

```text
broker
autonomous trader
portfolio accounting system
full backtesting platform
technical-analysis signal engine
general-purpose web crawler
general-purpose RAG
AI investment advisor
```

上述系統都可以成為 consumer，但不應全部被 TW-Market 吞入核心。

---

# 8. Target Architecture After V3.2 Future Phases

```text
                       Human
                         │
                         ▼
                    AI / Agent
                         │
          ┌──────────────┼──────────────┐
          │              │              │
       ChatGPT          Claude         Gemini
          │              │              │
          └──────────────┴──────────────┘
                         │
                         ▼
              Unified Evidence Request
                         │
                         ▼
        ┌──────────────────────────────────┐
        │            TW-Market             │
        │                                  │
        │ Taiwan Market Identity Service   │
        │ Market Evidence                  │
        │ Official Disclosures             │
        │ Fundamentals                     │
        │ Corporate Actions                │
        │ Regulatory Context               │
        │ Historical Reference             │
        │ Optional Cross-Market Context    │
        │ Currentness / Missing / Audit    │
        └──────────────────────────────────┘
                         │
                         ▼
               Research Evidence Bundle
                         │
                         ▼
                    AI / Agent
                         │
              analysis / report / alert
```

Scheduled use：

```text
External Agent Scheduler
          │
          ├─ 10:00 invoke once
          ├─ 12:00 invoke once
          └─ every 5m for bounded 1h session
                         │
                         ▼
              same TW-Market contract
```

---

# 9. V3.2 Phase Checklist

```text
[x] Phase A — Governed Evidence Core
[x] Phase B — AI Guide & Portable Skill Baseline
[x] Phase C — Unified Contract & Runtime
[x] Phase D — Unified Workbench
[x] Phase E — Local Service, MCP & Real-Agent Closed Loop
[x] Phase E-P — Portability, Identity Service & Skill Realignment
[x] Phase F — Persistent Watchlist & Productization
[x] V1 Release Gate — v1.0.0 Stable Productization

[ ] Phase G — Research Evidence Expansion
[ ] Phase H — Interpretation & Historical Reference
[ ] Phase I — Cross-Market & Optional Context
[ ] Phase J — Integrated Research Acceptance
[ ] Phase K — Multi-Agent Compatibility & Evaluation
[ ] Phase L — Production Hardening & Extension Architecture
[ ] Phase M — Agent-Scheduled Research & Bounded Monitoring
```

---

# 10. V3.2 Principal Product Decision

```text
PRESERVE:
V1 frozen evidence contract
local-first architecture
six-tool MCP
ISIN durable identity
installation-local Security Master
explicit execute-once
complete bounded evidence
auditability
non-trading boundary

EXPAND NEXT:
official research evidence
interpretation safety
historical context
optional cross-market context

VALIDATE:
integrated research scenarios
multi-agent behavior

HARDEN:
platform extensibility
observability
migration
security
source drift

AUTOMATE LAST:
external-agent scheduled research
bounded repeated monitoring
deterministic alert conditions
```

最終原則：

> **先把證據做深、把解讀做安全、把跨 Agent 使用做穩，再讓排程與監控把這些成熟能力放大。**