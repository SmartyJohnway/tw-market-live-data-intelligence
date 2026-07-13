# M8 through M8C consolidated acceptance

Status: `m8_through_m8c_consolidated_acceptance_pass_with_caveats`.

Implemented through track: M8C. No M9 or successor task is authorized; `next_task=null` and `next_task_status=awaiting_operator_prioritization` in the M8 source registry.

M8 provides multi-source context building and controlled conversation projection. M8A integrates official cash-market EOD/reference context. M8B integrates official TAIFEX OpenAPI EOD/statistical/reference context. M8C adds TAIFEX MIS bounded regular-session initial-state runtime and, in M8C-02, controlled M8 context integration with source-specific currentness fail-closed precedence.

Consolidated caveats remain: no realtime guarantee, no trading advice, no recommendation, no trading signal, no scheduler, no polling daemon, no startup fetch, no model call, no raw payload exposure, and no persistent market-data cache.
