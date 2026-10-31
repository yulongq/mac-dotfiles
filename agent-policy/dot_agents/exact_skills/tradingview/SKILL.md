---
name: tradingview
description: Use TradingView MCP first for financial-market research needing quotes, price history, technicals, valuation, company fundamentals, earnings, analyst estimates, screening, macro indicators, or company news and filings. Use within broader investment or sector research even when TradingView is not named. Not for conceptual finance explanations or calculations fully supported by supplied data.
---

# TradingView research

Use the connected TradingView MCP as the first source for the market-data portion of relevant research. Discover its available tools and make the matching read calls before searching the web for the same data; merely noting that the connector exists does not satisfy this workflow. Request only the data the question needs. Honor an explicitly selected source or source restriction.

Web verification requirements still apply. Use primary filings, issuer releases, statistical agencies, and central banks for authoritative definitions, material claims, and gaps in TradingView coverage. Broader business or industry research can use both: TradingView supplies market and financial evidence, while primary sources establish disclosures and explanations. Do not turn this preference into a ban on web research.

## Select the read

Discover the connected tools by TradingView name or capability; the names below are suffixes, not a fixed host namespace. Read their current schemas before calling them. Resolve company names or ambiguous tickers with `search_symbols`, then match the exchange, instrument type, and currency needed by the question. Search order is not listing preference; a similarly named company or depositary receipt can come first. Reuse an already established `EXCHANGE:TICKER`.

| Evidence needed | TradingView route |
| --- | --- |
| Current quote, valuation columns, or peer comparison | `get_symbol_data`; use `get_symbol_data_batch` for multiple symbols. Discover non-default columns through `get_screener_columns`. |
| Returns, price moves, volume, or historical chart data | `get_ohlcv` with the requested date window and interval. Follow `has_more` and `next_date_to` when the returned window is incomplete; request raw bars for calculations, not only `summary`. |
| RSI, moving averages, MACD, or other technical indicators | `get_technicals_rating` with an explicit timeframe. Its aggregate rating is an indicator summary, not an analyst recommendation. |
| Current fundamentals or valuation | `get_financials` with the appropriate `ttm`, `fq`, or `fy` period. |
| Historical revenue, margins, earnings, debt, or cash flow | `get_financial_history` with `fq` or `fy` and a date window. |
| Analyst consensus, price targets, or estimates | `get_forecasts`; keep estimates separate from reported results and management guidance. |
| Screening an investment universe | `get_screener_columns`, then `run_screener` with the intended market, filters, columns, and sort. Compare returned rows with `totalCount` before claiming full coverage. |
| Earnings or dividend dates | `get_earnings_calendar` or `get_dividends_calendar`. The earnings calendar holds only the next and most recent report, even when given an older date range; use history or documents for earlier quarters. |
| Company filings, earnings calls, or news | `get_documents` then `get_document_view` with a returned view ID; `get_news` then `get_news_story` with a returned story ID. A summary view is not the full filing or transcript. Follow original source links when the claim needs the underlying text. |
| Macro releases or indicator history | `get_economic_calendar` for events; `get_economic_symbols` then `get_economic_data` for series. Discover indicator codes instead of constructing them. |

For research on the user's watchlist, use `list_watchlists` and `get_watchlist`. Avoid `get_active_watchlist` for inspection: it can activate a list or create one. Research alone does not request changes to watchlists or alerts.

## Interpret the response

- Carry the exchange, currency, units, reporting period, and available data timestamps into comparisons. A fetch time does not prove a quote is real-time; label missing freshness or price-adjustment information rather than assuming it. Price changes from OHLCV are not automatically total shareholder returns.
- Check financial-history labels against the requested periods before calculating trends. Duplicate or missing quarters need reconciliation with filings; do not relabel points from their position in an array or combine mismatched TTM, annual, and quarterly figures.
- Check `success`, `partial`, `warnings`, and `missing` where returned. Nulls, unresolved symbols, empty windows, and backend failures are not zeros. Resolve an incorrect symbol or unsupported field through its catalog; when coverage or access remains unavailable, state the specific gap and use an appropriate alternate source. Do not silently replace a failed MCP call with an apparently complete answer.
- Attribute values to TradingView MCP and include the relevant period or as-of time. Use returned document or news links when available; otherwise give a plain source label rather than inventing a citation URL. Distinguish reported values, consensus, calculations, and inference. A price move alongside a headline does not establish its cause.
