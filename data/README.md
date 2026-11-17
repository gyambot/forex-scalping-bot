# Historical Data Provenance

## 2025 EURUSD source

- Provider: [HistData.com free historical data](https://www.histdata.com/download-free-forex-data/)
- Product: Generic ASCII EUR/USD M1 bars, full calendar year 2025.
- Downloaded: 2026-11-12.
- Original archive: `HISTDATA_COM_ASCII_EURUSD_M1_2025.zip`
- Archive SHA-256: `b7c23d20b9577588a8b13508d58fedbe487e569b7b8b5dd368bd1d2b61115de0`
- Converted file: `eurusd_m5_2025.csv`
- Converted file SHA-256: `a681d32ba080ab982e868e611c737692daa8a4c8d78fcb5b5bc4a9d098784638`

HistData states that bar-based OHLC prices are based on tick **bid** prices;
ask data is available only in its generic ASCII tick files. Its CSV timestamps
are fixed Eastern Standard Time (UTC-05:00), without daylight-saving
adjustments. The conversion script therefore applies a fixed five-hour UTC
offset, not a DST-aware timezone.

The archive contains 372,084 rows and 60 duplicate minute rows. The vendor
status report notes data gaps and explicitly provides no warranty or
certification. The source also contains an out-of-order clock sequence on
2025-10-26; the converter excludes that entire source date rather than guessing
how to repair it. It merges duplicate minute stamps using first open, maximum
high, minimum low, and last close. Only complete five-minute buckets containing
all five constituent minute stamps are emitted. This produced 73,683 M5 bars;
884 incomplete buckets were excluded, and 719 gaps longer than five minutes
remain (including market closures and data gaps).

Reproduce the converted data with:

```powershell
python scripts/prepare_histdata.py --input data/HISTDATA_COM_ASCII_EURUSD_M1_2025.zip --output data/eurusd_m5_2025.csv
```

HistData warns that it provides no warranty/certification. This data and the
modeled fixed spread are evidence inputs, not an assurance of executable fills
or future performance. Check the provider's current terms before redistributing
the archive.

## 2026 temporal validation source

- Provider/product: HistData.com generic ASCII EUR/USD M1 bars.
- Coverage: January through October 2026, using the ten available monthly
  source archives in `raw/2026/`.
- Combined source archive: `HISTDATA_COM_ASCII_EURUSD_M1_2026_01_10.zip`
- Combined archive SHA-256:
  `c6b53289d3a45a551713fbac86d85d5be33c5bf68485a2e91e8c3c7c88161631`
- Converted file: `eurusd_m5_2026_01_10.csv`
- Converted file SHA-256:
  `2aefb1e45fd05eb6d88deb6689dfebc5057ce4048f7e8de623a27df657b0d25a`
- Downloaded: 2026-11-12.

The converter found eight duplicate rows and out-of-order timestamps on
2026-07-05, 2026-09-24, and 2026-10-09; those full source dates were excluded.
It emitted 60,551 complete M5 bars, excluded 955 incomplete buckets, and
retained 784 gaps over five minutes. Coverage runs from 2026-01-01 22:05 UTC to
2026-10-30 20:50 UTC. The monthly source archives are retained under
`data/raw/2026/`.

| Month | Archive SHA-256 |
|---|---|
| 2026-01 | `7c3ad3ae3626d6ee9575c07679212424799f3b32aac056c42584db1b89298137` |
| 2026-02 | `2e38a7ae97579b0ac0180878df23b2e43aa7ee5cd7ef377f06f0f845fa8bd9e7` |
| 2026-03 | `f55203d8661af3e0ce04bee4fe2dd3d22dcf42aa93a50af9948cf939a7eeb313` |
| 2026-04 | `4141266da0c7cd9aab2f608ccf7d79bffb3fe573a4ad8745ee2381c2e6deb758` |
| 2026-05 | `200b70301142ed9ce112ba65896bddbe199592977b030342603d643f571f03fe` |
| 2026-06 | `f339d646269816031689c2f84d69db58fdfbbac23bd23a4a0c1a2323430c7713` |
| 2026-07 | `d5e51949169327a82a50c52182486397b206fd95d5a0c06b700b89b435eace26` |
| 2026-08 | `65c7c5d0f170abf4a60b86908723ef5068ccec7aa3c76baefbe8542f87eed5b3` |
| 2026-09 | `c6538f46e4897db060152b192b5a69cd711841d95c12b405f1557dbff562d597` |
| 2026-10 | `eda8700ef26c8e1c57dd4fc5f0669e612cfca1fd602f9bb301b508a2a6fd1737` |
